"""Interactive REPL for aldakit with syntax highlighting and completion."""

import time
from pathlib import Path

# Initialize vendored packages path (must be before prompt_toolkit imports)
from . import ext  # noqa: F401

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from .constants import (
    DEFAULT_TEMPO,
    DEFAULT_VIRTUAL_PORT_NAME,
    POLL_INTERVAL_DEFAULT,
    REPL_COMPLETION_MIN_WORD_LENGTH,
    REPL_CONTINUATION_PROMPT,
    REPL_HISTORY_FILENAME,
    REPL_INSTRUMENT_COLUMNS,
    REPL_PROMPT,
)
from .errors import AldaParseError
from .midi.backends import LibremidiBackend
from .midi.generator import generate_midi
from .midi.types import INSTRUMENT_PROGRAMS
from .parser import parse

# Alda token colors - clean scheme
ALDA_STYLE = Style.from_dict(
    {
        "note": "#ffffff",  # white - notes
        "rest": "#888888",  # gray - rests
        "octave": "#cc99ff",  # light purple - octave changes
        "duration": "#66ccff",  # light blue - durations
        "instrument": "#ff99cc bold",  # pink bold - instruments
        "attribute": "#99cc99",  # sage green - attributes
        "barline": "#555555",  # dark gray
        "comment": "#666666 italic",  # comments
    }
)


class AldaLexer(Lexer):
    """Syntax highlighter for alda code."""

    def lex_document(self, document: Document):
        def get_line_tokens(line_number):
            line = document.lines[line_number]
            tokens = []
            i = 0
            while i < len(line):
                ch = line[i]

                # Comments
                if ch == "#":
                    tokens.append(("class:comment", line[i:]))
                    break

                # Instrument/part declaration (word followed by :)
                # Look ahead to check for colon
                if ch.isalpha():
                    j = i
                    while j < len(line) and (line[j].isalnum() or line[j] == "-"):
                        j += 1
                    if j < len(line) and line[j] == ":":
                        # This is an instrument declaration
                        tokens.append(("class:instrument", line[i : j + 1]))
                        i = j + 1
                        continue
                    # Not followed by colon - check if it's a note/rest/octave
                    # (handled below by continuing the loop)

                # S-expressions (tempo, volume, etc.)
                if ch == "(":
                    j = i + 1
                    depth = 1
                    while j < len(line) and depth > 0:
                        if line[j] == "(":
                            depth += 1
                        elif line[j] == ")":
                            depth -= 1
                        j += 1
                    tokens.append(("class:attribute", line[i:j]))
                    i = j
                    continue

                # Notes (with optional accidentals and duration)
                if ch in "abcdefg":
                    j = i + 1
                    # Accidentals
                    while j < len(line) and line[j] in "+-_":
                        j += 1
                    tokens.append(("class:note", line[i:j]))
                    i = j
                    # Duration (separate token)
                    if i < len(line) and (line[i].isdigit() or line[i] == "."):
                        j = i
                        while j < len(line) and (line[j].isdigit() or line[j] == "."):
                            j += 1
                        # ms or s suffix
                        if j + 1 < len(line) and line[j : j + 2] == "ms":
                            j += 2
                        elif (
                            j < len(line)
                            and line[j] == "s"
                            and (j + 1 >= len(line) or not line[j + 1].isalpha())
                        ):
                            j += 1
                        tokens.append(("class:duration", line[i:j]))
                        i = j
                    continue

                # Rest (with optional duration)
                if ch == "r" and (
                    i + 1 >= len(line) or line[i + 1] not in "abcdefghijklmnopqstuvwxyz"
                ):
                    tokens.append(("class:rest", ch))
                    i += 1
                    # Duration (separate token)
                    if i < len(line) and (line[i].isdigit() or line[i] == "."):
                        j = i
                        while j < len(line) and (line[j].isdigit() or line[j] == "."):
                            j += 1
                        tokens.append(("class:duration", line[i:j]))
                        i = j
                    continue

                # Octave set (o followed by number)
                if ch == "o" and i + 1 < len(line) and line[i + 1].isdigit():
                    j = i + 1
                    while j < len(line) and line[j].isdigit():
                        j += 1
                    tokens.append(("class:octave", line[i:j]))
                    i = j
                    continue

                # Octave up/down
                if ch in "<>":
                    tokens.append(("class:octave", ch))
                    i += 1
                    continue

                # Barline
                if ch == "|":
                    tokens.append(("class:barline", ch))
                    i += 1
                    continue

                # Chord markers
                if ch == "/":
                    tokens.append(("class:note", ch))
                    i += 1
                    continue

                # Default (whitespace, etc.)
                tokens.append(("", ch))
                i += 1

            return tokens

        return get_line_tokens


class AldaCompleter(Completer):
    """Auto-completion for alda."""

    ATTRIBUTES = [
        "(tempo ",
        "(volume ",
        "(quant ",
        "(key-sig ",
        "(pan ",
        "(panning ",
        "(track-vol ",
    ]

    def __init__(self):
        self.instruments = sorted(INSTRUMENT_PROGRAMS.keys())

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        line = document.current_line_before_cursor.strip()

        # Only complete instruments if:
        # - At start of line (no content yet), OR
        # - Word is at least 3 chars (to avoid matching notes)
        if ":" not in line and len(word) >= REPL_COMPLETION_MIN_WORD_LENGTH:
            for inst in self.instruments:
                if inst.startswith(word):
                    yield Completion(inst + ": ", start_position=-len(word))

        # Complete attributes after (
        if "(" in line and ")" not in line[line.rfind("(") :]:
            for attr in self.ATTRIBUTES:
                if attr.startswith("(" + word):
                    yield Completion(attr, start_position=-len(word) - 1)


def create_key_bindings(backend):
    """Create custom key bindings."""
    kb = KeyBindings()

    @kb.add(Keys.Escape, Keys.Enter)
    @kb.add(Keys.ControlJ)  # Ctrl+J as alternative for multi-line
    def _(event):
        """Insert newline for multi-line input."""
        event.current_buffer.insert_text("\n")

    @kb.add(Keys.ControlC)
    def _(event):
        """Stop playback on Ctrl+C."""
        if backend.is_playing():
            backend.stop()
        else:
            event.app.exit(exception=KeyboardInterrupt)

    return kb


def run_repl(
    port_name: str | None = None,
    verbose: bool = False,
    concurrent: bool = True,
    use_audio: bool = False,
    soundfont: str | None = None,
    default_tempo: int = DEFAULT_TEMPO,
    virtual_port_name: str = DEFAULT_VIRTUAL_PORT_NAME,
) -> int:
    """Run the interactive alda REPL.

    Args:
        port_name: MIDI output port name (None for default/virtual).
        verbose: If True, print note counts and durations.
        concurrent: If True (default), enable concurrent playback mode
            where multiple inputs layer on top of each other.
        use_audio: If True, use TinySoundFont audio backend instead of MIDI.
        soundfont: Path to SoundFont file (for audio backend).
        default_tempo: Default tempo in BPM (default: DEFAULT_TEMPO).
        virtual_port_name: Name for virtual MIDI port (default: DEFAULT_VIRTUAL_PORT_NAME).
    """
    # Check for MIDI ports if not using audio
    if not use_audio and port_name is None:
        test_backend = LibremidiBackend()
        ports = test_backend.list_output_ports()
        if not ports:
            # No MIDI ports - fall back to audio if soundfont is configured,
            # otherwise let the backend create a virtual port (AldakitMIDI)
            if soundfont:
                use_audio = True

    if use_audio:
        from .midi.backends import TsfBackend, HAS_TSF

        if not HAS_TSF:
            print("Error: Audio backend not available. The _tsf module was not built.")
            return 1

        try:
            backend = TsfBackend(soundfont=soundfont)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1

        backend_name = "TinySoundFont"
        # TsfBackend doesn't support concurrent mode
        supports_concurrent = False
    else:
        backend = LibremidiBackend(
            port_name=port_name,
            concurrent=concurrent,
            virtual_port_name=virtual_port_name,
        )
        backend._ensure_port_open()
        backend_name = virtual_port_name
        supports_concurrent = True

    history_file = Path.home() / REPL_HISTORY_FILENAME

    session = PromptSession(
        history=FileHistory(str(history_file)),
        lexer=AldaLexer(),
        completer=AldaCompleter(),
        style=ALDA_STYLE,
        key_bindings=create_key_bindings(backend),
        multiline=False,
        prompt_continuation=lambda width,
        line_number,
        is_soft_wrap: REPL_CONTINUATION_PROMPT,
    )

    # State (default_tempo passed as parameter)

    if supports_concurrent:
        mode_str = "concurrent" if backend.concurrent_mode else "sequential"
        print(f"aldakit REPL - {backend_name} port open ({mode_str} mode)")
    else:
        print(f"aldakit REPL - {backend_name} audio backend")
    print("Enter alda code, press Enter to play. Alt+Enter for multi-line.")
    print("Type :help for commands, Ctrl+D to exit.")
    print()

    try:
        while True:
            try:
                source = session.prompt(REPL_PROMPT).strip()
            except EOFError:
                break
            except KeyboardInterrupt:
                continue

            if not source:
                continue

            # Commands
            if source.startswith(":"):
                parts = source[1:].split(None, 1)
                cmd = parts[0].lower() if parts else ""
                arg = parts[1] if len(parts) > 1 else ""

                if cmd in ("q", "quit", "exit"):
                    break
                elif cmd in ("h", "help", "?"):
                    print("Commands:")
                    print("  :q :quit :exit    - Exit REPL")
                    print("  :help :h :?       - Show this help")
                    print("  :ports            - List MIDI ports")
                    print("  :instruments      - List instruments")
                    print("  :tempo [BPM]      - Show/set default tempo")
                    print("  :stop             - Stop playback")
                    print("  :status           - Show playback status")
                    print("  :concurrent       - Enable concurrent mode (layer inputs)")
                    print(
                        "  :sequential       - Enable sequential mode (wait for each)"
                    )
                    print()
                    print("Shortcuts:")
                    print("  Alt+Enter         - Multi-line input")
                    print("  Ctrl+C            - Stop playback / cancel")
                    print("  Ctrl+D            - Exit")
                    print("  Tab               - Auto-complete")
                    print("  Up/Down           - History")
                elif cmd == "ports":
                    if supports_concurrent:
                        ports = backend.list_output_ports()
                        if ports:
                            for i, p in enumerate(ports):
                                print(f"  {i}: {p}")
                        else:
                            print(f"  (no ports - using virtual {virtual_port_name})")
                    else:
                        print("  (using TinySoundFont audio backend)")
                elif cmd == "instruments":
                    insts = sorted(INSTRUMENT_PROGRAMS.keys())
                    # Print in columns
                    cols = REPL_INSTRUMENT_COLUMNS
                    for i in range(0, len(insts), cols):
                        row = insts[i : i + cols]
                        print("  " + "  ".join(f"{inst:20}" for inst in row))
                elif cmd == "tempo":
                    if arg:
                        try:
                            default_tempo = int(arg)
                            print(f"Default tempo: {default_tempo} BPM")
                        except ValueError:
                            print("Invalid tempo")
                    else:
                        print(f"Default tempo: {default_tempo} BPM")
                elif cmd == "stop":
                    backend.stop()
                    print("Stopped")
                elif cmd == "status":
                    playing = "playing" if backend.is_playing() else "idle"
                    if supports_concurrent:
                        mode = "concurrent" if backend.concurrent_mode else "sequential"
                        slots = backend.active_slots
                        print("Backend: MIDI (libremidi)")
                        print(f"Mode: {mode}")
                        print(f"Status: {playing}")
                        print(f"Active slots: {slots}/8")
                    else:
                        print("Backend: Audio (TinySoundFont)")
                        print(f"Status: {playing}")
                elif cmd == "concurrent":
                    if supports_concurrent:
                        backend.concurrent_mode = True
                        print(
                            "Concurrent mode enabled - inputs will layer on each other"
                        )
                    else:
                        print("Concurrent mode not available with audio backend")
                elif cmd == "sequential":
                    if supports_concurrent:
                        backend.concurrent_mode = False
                        print("Sequential mode enabled - each input waits for previous")
                    else:
                        print("Audio backend always uses sequential mode")
                else:
                    print(f"Unknown command: :{cmd}")
                continue

            # Add default tempo if not specified
            if "(tempo" not in source.lower():
                source = f"(tempo {default_tempo}) {source}"

            try:
                ast = parse(source, "<repl>")
                sequence = generate_midi(ast)

                if not sequence.notes:
                    print("(no notes)")
                    continue

                if verbose:
                    print(f"{len(sequence.notes)} notes, {sequence.duration():.2f}s")

                slot_id = backend.play(sequence)

                if slot_id is None:
                    print("(all playback slots busy - use :stop to clear)")
                elif not supports_concurrent or not backend.concurrent_mode:
                    # In sequential mode (or audio backend), wait for playback
                    while backend.is_playing():
                        time.sleep(POLL_INTERVAL_DEFAULT)
                # In concurrent mode, return immediately to accept next input

            except AldaParseError as e:
                print(f"Error: {e}")

    except KeyboardInterrupt:
        pass

    # Clean up backend
    if supports_concurrent:
        backend.close()
    else:
        backend.stop()
    print("Goodbye!")
    return 0
