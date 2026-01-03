# pyalda

A zero-dependency Python parser and MIDI generator for the [Alda](https://alda.io) music programming language.

## Installation

```sh
pip install pyalda
```

Or with [uv](https://github.com/astral-sh/uv):

```sh
uv add pyalda
```

## Quick Start

### Command Line

```sh
# Play an Alda file
pyalda examples/twinkle.alda

# Evaluate inline code
pyalda -e "piano: c d e f g"

# Export to MIDI file
pyalda examples/bach-prelude.alda -o bach.mid

# Interactive REPL
pyalda repl
```

### Python API

```python
from pyalda import parse, generate_midi, LibremidiBackend

# Parse Alda source code
ast = parse("""
piano:
  (tempo 120)
  o4 c4 d e f | g a b > c
""")

# Generate MIDI sequence
sequence = generate_midi(ast)

# Save to file
backend = LibremidiBackend()
backend.save(sequence, "output.mid")

# Or play directly
with LibremidiBackend() as backend:
    backend.play(sequence)
```

## CLI Reference

```sh
pyalda [-h] [--version] [-e CODE] [-o FILE] [--port NAME]
       [--stdin] [--parse-only] [--no-wait] [-v]
       {repl,ports,play} [file]
```

### Subcommands

| Command | Description |
| ------- | ----------- |
| `repl` | Interactive REPL with syntax highlighting and auto-completion |
| `ports` | List available MIDI output ports |
| `play` | Play an Alda file or code (default behavior) |

### Options

| Option | Description |
| ------ | ----------- |
| `file` | Alda file to play (use `-` for stdin) |
| `-e, --eval CODE` | Evaluate Alda code directly |
| `-o, --output FILE` | Save to MIDI file instead of playing |
| `--port NAME` | MIDI output port name |
| `--stdin` | Read from stdin (blank line to play) |
| `--parse-only` | Print AST without playing |
| `--no-wait` | Don't wait for playback to finish |
| `-v, --verbose` | Verbose output |

### Examples

```bash
# Interactive REPL with syntax highlighting
pyalda repl

# List available MIDI ports
pyalda ports

# Play with verbose output
pyalda -v examples/jazz.alda

# Read from stdin
echo "piano: c d e f g" | pyalda -

# Parse and show AST
pyalda --parse-only -e "piano: c/e/g"

# Export to MIDI file
pyalda examples/twinkle.alda -o twinkle.mid
```

## Interactive REPL

The REPL provides an interactive environment for composing and playing Alda code:

```bash
pyalda repl
```

Features:

- Syntax highlighting
- Auto-completion for instruments (3+ characters)
- Command history (persistent across sessions)
- Multi-line input (Alt+Enter)
- MIDI playback control (Ctrl+C to stop)

REPL Commands:

- `:help` - Show help
- `:quit` - Exit REPL
- `:ports` - List MIDI ports
- `:instruments` - List available instruments
- `:tempo [BPM]` - Show/set default tempo
- `:stop` - Stop playback

## Alda Syntax Reference

### Notes and Rests

```alda
piano:
  c d e f g a b   # Notes
  r               # Rest
  c4 d8 e16       # With duration (4=quarter, 8=eighth, etc.)
  c4. d4..        # Dotted notes
  c500ms d2s      # Milliseconds and seconds
```

### Accidentals

```alda
c+    # Sharp
c-    # Flat
c_    # Natural
c++   # Double sharp
```

### Octaves

```alda
o4 c    # Set octave to 4
> c     # Octave up
< c     # Octave down
```

### Chords

```alda
c/e/g           # C major chord
c1/e/g          # Whole note chord
c/e/g/>c        # With octave change
```

### Ties and Slurs

```alda
c1~1            # Tied notes (duration adds)
c4~d~e~f        # Slurred notes (legato)
```

### Parts

```alda
piano: c d e

violin "v1": c d e    # With alias

violin/viola/cello "strings":   # Multi-instrument
  c d e
```

### Attributes

```alda
(tempo 120)     # Set tempo (BPM)
(tempo! 120)    # Global tempo

(vol 80)        # Volume (0-100)
(volume 80)

(quant 90)      # Quantization/legato (0-100)

(panning 50)    # Pan (0=left, 100=right)

# Dynamic markings
(pp) (p) (mp) (mf) (f) (ff)
```

### Variables

```alda
riff = c8 d e f g4

piano:
  riff riff > riff
```

### Repeats

```alda
c*4             # Repeat note 4 times
[c d e]*4       # Repeat sequence
[c d e f]*8     # 8 times
```

### Cram (Tuplets)

```alda
{c d e}4        # Triplet in quarter note
{c d e f g}2    # Quintuplet in half note
{c {d e} f}4    # Nested cram
```

### Voices

```alda
piano:
  V1: c4 d e f
  V2: e4 f g a
  V0:           # End voices
```

### Markers

```alda
piano:
  c d e f
  %chorus
  g a b > c

violin:
  @chorus       # Jump to chorus marker
  e f g a
```

## Supported Instruments

All 128 General MIDI instruments are supported. Common examples:

- `piano`, `acoustic-grand-piano`
- `violin`, `viola`, `cello`, `contrabass`
- `flute`, `oboe`, `clarinet`, `bassoon`
- `trumpet`, `trombone`, `french-horn`, `tuba`
- `acoustic-guitar`, `electric-guitar-clean`, `electric-bass`
- `choir`, `strings`, `brass-section`

See `src/pyalda/midi/types.py` for the complete mapping.

## MIDI Backend

pyalda uses [libremidi](https://github.com/jcelerier/libremidi) via nanobind for cross-platform MIDI I/O:

- Low-latency realtime playback
- Virtual MIDI port support (PyAldaMIDI)
- Pure Python MIDI file writing (no external dependencies)
- Cross-platform: macOS (CoreMIDI), Linux (ALSA), Windows (WinMM)
- Supports hardware and software/virtual MIDI ports (FluidSynth, IAC Driver, etc.)

```python
from pyalda import LibremidiBackend

backend = LibremidiBackend()

# List available ports
print(backend.list_output_ports())

# Play to virtual port (visible in DAWs like Ableton Live)
backend.play(sequence)

# Save to MIDI file
backend.save(sequence, "output.mid")
```

## MIDI Playback Setup

### Virtual Port (Recommended)

When no hardware MIDI ports are available, pyalda creates a virtual port named "PyAldaMIDI". This port is visible to DAWs and other MIDI software:

1. Start the REPL: `pyalda repl`
2. In your DAW (Ableton Live, Logic Pro, etc.), look for "PyAldaMIDI" in MIDI input settings
3. Play code in the REPL - notes will be sent to your DAW

### Software Synthesizer (FluidSynth)

For high-quality General MIDI playback without hardware, use [FluidSynth](https://www.fluidsynth.org/):

```sh
# Install FluidSynth (macOS)
brew install fluidsynth

# Download a SoundFont (e.g., FluidR3_GM.sf2)
# Place in ~/Music/sf2/

# Start FluidSynth with CoreMIDI (macOS)
fluidsynth -a coreaudio -m coremidi ~/Music/sf2/FluidR3_GM.sf2

# In another terminal, start pyalda
pyalda repl
# pyalda> piano: c d e f g
```

A helper script is included:

```sh
./scripts/fluidsynth-gm.sh           # Uses ~/Music/sf2/FluidR3_GM.sf2
./scripts/fluidsynth-gm.sh path.sf2  # Use custom SoundFont
```

### Hardware MIDI

Connect a USB MIDI interface or synthesizer, then:

```sh
# List available ports
pyalda ports

# Play to a specific port
pyalda --port "My MIDI Device" examples/twinkle.alda
```

### MIDI File Export

If you don't have MIDI playback set up, export to a file:

```bash
# Save to MIDI file
pyalda examples/twinkle.alda -o twinkle.mid

# Open with default app
open twinkle.mid
```

## Development

### Setup

```sh
git clone https://github.com/shakfu/pyalda.git
cd pyalda
uv sync
make  # Build the libremidi extension
```

### Run Tests

```sh
make test
# or
uv run pytest tests/ -v
```

### Project Architecture

![pyalda architecture](docs/assets/architecture.svg)

### Project Structure

```sh
src/pyalda/
  __init__.py       # Public API
  __main__.py       # python -m pyalda support
  cli.py            # Command-line interface
  repl.py           # Interactive REPL
  tokens.py         # Token types
  scanner.py        # Lexer
  ast_nodes.py      # AST node classes
  parser.py         # Recursive descent parser
  errors.py         # Error types
  _libremidi.cpp    # nanobind bindings for libremidi
  ext/              # Vendored prompt-toolkit
  midi/
    __init__.py
    types.py        # MIDI data types
    generator.py    # AST to MIDI conversion
    smf.py          # Pure Python MIDI file writer
    backends/
      base.py       # Abstract backend
      libremidi_backend.py

docs/               # Documentation and architecture diagrams
examples/           # Example Alda files
scripts/            # Helper scripts (FluidSynth setup)
tests/              # Test suite
thirdparty/         # libremidi source
```

## License

MIT

## See Also

- [Alda](https://alda.io) - The original Alda language and implementation
- [Alda Cheat Sheet](https://alda.io/cheat-sheet/) - Syntax reference
- [Extending pyalda](docs/extending-pyalda.md) - Design document for programmatic API
