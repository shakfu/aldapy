# aldakit

[![PyPI version](https://badge.fury.io/py/aldakit.svg)](https://pypi.org/project/aldakit/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A zero-dependency Python parser and MIDI generator for the [Alda](https://alda.io) music programming language[^1].

[^1]: Includes a rich REPL, native MIDI, and built-in audio via bundled [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit), [libremidi](https://github.com/jcelerier/libremidi), and [TinySoundFont](https://github.com/schellingb/TinySoundFont) respectively.

## Features

- **Alda Parser** - Full parser for the Alda music language with AST generation
- **MIDI Playback** - Low-latency playback via libremidi (CoreMIDI, ALSA, WinMM)
- **Audio Playback** - Built-in synthesis via TinySoundFont (no external synth required)
- **MIDI Export** - Save compositions as Standard MIDI Files
- **MIDI Import** - Load MIDI files and convert to Alda notation
- **Real-time Transcription** - Record from MIDI keyboards and convert to Alda
- **Programmatic Composition** - Build music with Python using the compose module
- **Music Theory** - Scale, chord, and interval utilities
- **Transformers** - Transpose, invert, augment, diminish, and more
- **Generative Music** - Markov chains, L-systems, cellular automata, Euclidean rhythms
- **Interactive REPL** - Syntax highlighting, auto-completion, and live playback
- **CLI Tools** - Play, transcribe, and convert from the command line

## Installation

Requires Python 3.10+

```sh
pip install aldakit
```

Or with [uv](https://github.com/astral-sh/uv):

```sh
uv add aldakit
```

## Quick Start

### Command Line

```sh
# Evaluate inline code
aldakit -e "piano: c d e f g"

# Interactive REPL
aldakit repl

# Play an Alda file (examples available in the repository)
aldakit examples/twinkle.alda

# Export to MIDI file
aldakit examples/bach-prelude.alda -o bach.mid
```

### Python API

```python
import aldakit

# Play directly
aldakit.play("piano: c d e f g")

# Save to MIDI file
aldakit.save("piano: c d e f g", "output.mid")

# Play from file
aldakit.play_file("song.alda")

# List available MIDI ports
print(aldakit.list_ports())
```

For more control, use the `Score` class:

```python
from aldakit import Score

score = Score("""
piano:
  (tempo 120)
  o4 c4 d e f | g a b > c
""")

# Play with options
score.play(port="FluidSynth", wait=False)

# Save to file
score.save("output.mid")

# Access internals
print(f"Duration: {score.duration}s")
print(score.ast)   # Parsed AST
print(score.midi)  # MIDI sequence
```

### MIDI Import

Import existing MIDI files and work with them as Alda:

```python
from aldakit import Score

# Import a MIDI file
score = Score.from_midi_file("recording.mid")

# Or use from_file (auto-detects .mid/.midi)
score = Score.from_file("song.mid")

# View as Alda source
print(score.to_alda())
# piano:
# o4 c4 d e f | g a b > c

# Play the imported MIDI
score.play()

# Export to Alda file
score.save("song.alda")

# Re-export to MIDI
score.save("output.mid")

# Import with custom quantization grid
# Default is 0.25 (16th notes), use 0.5 for 8th notes
score = Score.from_midi_file("recording.mid", quantize_grid=0.5)
```

Features:
- Multi-track MIDI files (each channel becomes a separate part)
- Tempo detection and preservation
- General MIDI instrument mapping
- Chord detection for simultaneous notes
- Configurable timing quantization

### Real-Time MIDI Transcription

Record MIDI input from a keyboard or controller:

```python
import aldakit

# List available MIDI input ports
print(aldakit.list_input_ports())

# Record for 10 seconds from the first available port
score = aldakit.transcribe(duration=10)

# Play back what was recorded
score.play()

# Export to Alda source
print(score.to_alda())

# Record with options
score = aldakit.transcribe(
    duration=30,
    port_name="My MIDI Keyboard",
    instrument="piano",
    tempo=120,
    quantize_grid=0.25,  # Quantize to 16th notes
)
```

For more control, use `TranscribeSession`:

```python
from aldakit.midi.transcriber import TranscribeSession

session = TranscribeSession(quantize_grid=0.25, default_tempo=120)

# Set a callback for note events (optional)
session.on_note(lambda pitch, vel, on: print(f"Note: {pitch}, vel={vel}, on={on}"))

# Start recording
session.start()

# Poll periodically (in a loop or timer)
import time
for _ in range(100):
    session.poll()
    time.sleep(0.1)

# Stop and get the recorded notes
seq = session.stop()
print(seq.to_alda())
```

### Programmatic Composition

Build music programmatically using the compose module:

```python
from aldakit import Score
from aldakit.compose import part, note, rest, chord, seq, tempo, volume

# Create a score from compose elements
score = Score.from_elements(
    part("piano"),
    tempo(120),
    note("c", duration=4),
    note("d"),
    note("e"),
    chord("c", "e", "g", duration=2),
)
score.play()

# Builder pattern with method chaining
score = (
    Score.from_elements(part("violin"))
    .with_tempo(90)
    .add(note("g", duration=8), note("a"), note("b"))
)

# Note transformations
c = note("c", duration=4)
c_sharp = c.sharpen()           # C#
c_up_octave = c.transpose(12)   # Up one octave

# Repeat syntax
pattern = seq(note("c"), note("d"), note("e"))
repeated = pattern * 4  # Repeat 4 times

# Export to Alda source
print(score.to_alda())  # "violin: (tempo 90) g8 a b"
```

Available compose elements:
- **Notes**: `note("c", duration=4, octave=5, accidental="+", dots=1)`
- **Rests**: `rest(duration=4)`, `rest(ms=500)`
- **Chords**: `chord("c", "e", "g")`, `chord(note("c"), note("e", accidental="+"))`
- **Sequences**: `seq(note("c"), note("d"))`, `Seq.from_alda("c d e")`
- **Parts**: `part("piano")`, `part("violin", alias="v1")`
- **Attributes**: `tempo(120)`, `volume(80)`, `octave(5)`, `panning(50)`
- **Dynamics**: `pp()`, `p()`, `mp()`, `mf()`, `f()`, `ff()`
- **Advanced**: `cram()`, `voice()`, `voice_group()`, `var()`, `var_ref()`, `marker()`, `at_marker()`

### Scales and Chords

Build melodies and harmonies using music theory helpers:

```python
from aldakit import Score
from aldakit.compose import part, tempo
from aldakit.compose import (
    # Scale functions
    scale, scale_notes, scale_degree, mode,
    relative_minor, relative_major,
    # Chord builders
    major, minor, dim, aug, maj7, min7, dom7,
    arpeggiate, invert_chord, voicing,
)

# Get scale pitches
c_major = scale("c", "major")       # ['c', 'd', 'e', 'f', 'g', 'a', 'b']
a_blues = scale("a", "blues")       # ['a', 'c', 'd', 'd+', 'e', 'g']

# Generate scale as playable notes
melody = scale_notes("c", "pentatonic", duration=8)

# Key relationships
rel_min = relative_minor("c")  # 'a' (C major -> A minor)
rel_maj = relative_major("a")  # 'c' (A minor -> C major)

# Build chords
c_maj = major("c")                    # C E G
a_min7 = min7("a")                    # A C E G
g_dom7 = dom7("g", inversion=1)       # B D F G (first inversion)

# Arpeggiate a chord
arp = arpeggiate(maj7("c"), pattern=[0, 1, 2, 3, 2, 1], duration=16)

# Custom voicing (spread chord across octaves)
spread = voicing(major("c"), [3, 4, 5])  # C3 E4 G5

# Create a I-IV-V-I progression
pitches = scale("c", "major")
progression = [
    major(pitches[0], duration=2),  # C major (I)
    major(pitches[3], duration=2),  # F major (IV)
    major(pitches[4], duration=2),  # G major (V)
    major(pitches[0], duration=1),  # C major (I)
]

score = Score.from_elements(
    part("piano"),
    tempo(100),
    *progression,
)
score.play()
```

Available scales: major, minor, harmonic-minor, melodic-minor, pentatonic, blues, chromatic, whole-tone, dorian, phrygian, lydian, mixolydian, locrian, japanese, arabic, hungarian-minor, spanish, bebop-dominant, bebop-major

Available chords: major, minor, dim, aug, sus2, sus4, maj7, min7, dom7, dim7, half_dim7, min_maj7, aug7, maj6, min6, dom9, maj9, min9, add9, power

### Transformers

Transform sequences with pitch and structural operations:

```python
from aldakit.compose import (
    note, seq,
    transpose, invert, reverse, shuffle,
    augment, diminish, fragment, loop, interleave,
    pipe,
)

# Create a motif
motif = seq(note("c", duration=8), note("d", duration=8), note("e", duration=8))

# Pitch transformers
up_fourth = transpose(motif, 5)      # Transpose up 5 semitones
inverted = invert(motif)             # Invert intervals around first note
backwards = reverse(motif)           # Retrograde

# Structural transformers
longer = augment(motif, 2)           # Double durations (8th -> quarter)
shorter = diminish(motif, 2)         # Halve durations (8th -> 16th)
first_two = fragment(motif, 2)       # Take first 2 elements
repeated = loop(motif, 4)            # Repeat 4 times (explicit)

# Chain transformations with pipe
result = pipe(
    motif,
    lambda s: transpose(s, 5),
    reverse,
    lambda s: augment(s, 2),
)

# All transforms preserve to_alda() export
print(result.to_alda())
```

### MIDI Transformers

For post-MIDI-generation processing, use MIDI-level transformers that operate on absolute timing:

```python
from aldakit import Score
from aldakit.midi.transform import (
    quantize, humanize, swing, stretch,
    accent, crescendo, normalize,
    filter_notes, trim, merge,
)

# Get MIDI sequence from a score
score = Score("piano: c d e f g a b > c")
midi_seq = score.midi

# Timing transformers
quantized = quantize(midi_seq, grid=0.25, strength=0.8)  # Snap to quarter-note grid
humanized = humanize(midi_seq, timing=0.02, velocity=10)  # Add subtle variations
swung = swing(midi_seq, grid=0.5, amount=0.3)            # Apply swing feel

# Velocity transformers
accented = accent(midi_seq, pattern=[1.0, 0.5, 0.5, 0.5])  # 4/4 accent pattern
crescendo_seq = crescendo(midi_seq, start_vel=50, end_vel=100)
normalized = normalize(midi_seq, target=100)

# Filtering and combining
filtered = filter_notes(midi_seq, lambda n: n.pitch >= 60)  # Keep notes >= middle C
trimmed = trim(midi_seq, start=0.0, end=2.0)               # First 2 seconds
merged = merge(midi_seq, another_seq)                       # Combine sequences
```

Note: MIDI transformers operate on absolute timing (seconds) and cannot be converted back to Alda notation.

### Generative Functions

Create algorithmic compositions with generative functions:

```python
from aldakit import Score
from aldakit.compose import part, tempo
from aldakit.compose.generate import (
    random_walk, euclidean, markov_chain, lsystem, cellular_automaton,
    shift_register, turing_machine,
)

# Random walk melody
melody = random_walk("c", steps=16, intervals=[-2, -1, 1, 2], duration=8, seed=42)

# Euclidean rhythms (e.g., Cuban tresillo: 3 hits over 8 steps)
rhythm = euclidean(hits=3, steps=8, pitch="c", duration=16)

# Markov chain
chain = markov_chain({
    "c": {"d": 0.5, "e": 0.3, "g": 0.2},
    "d": {"e": 0.6, "c": 0.4},
    "e": {"c": 0.5, "g": 0.5},
    "g": {"c": 1.0},
})
markov_melody = chain.generate(start="c", length=16, duration=8, seed=42)

# L-System (Fibonacci pattern)
from aldakit.compose import note, rest
fib = lsystem(
    axiom="A",
    rules={"A": "AB", "B": "A"},
    iterations=5,
    note_map={"A": note("c", duration=8), "B": note("e", duration=8)},
)

# Cellular automaton (Rule 110)
automaton = cellular_automaton(rule=110, width=8, steps=4, pitch_on="c", duration=16)

# Shift register (LFSR) - classic analog sequencer
lfsr = shift_register(16, bits=4, scale=["c", "e", "g", "b"], duration=16)

# Turing Machine - evolving loop (probability=0 for locked, higher for chaos)
turing = turing_machine(32, bits=8, probability=0.1, seed=42)

# Combine into a score
score = Score.from_elements(
    part("piano"),
    tempo(120),
    *melody.elements,
)
score.play()
```

## CLI Reference

```sh
aldakit [-h] [--version] [-e CODE] [-o FILE] [--port NAME|INDEX]
       [--stdin] [--parse-only] [--no-wait] [-v]
       {repl,ports,transcribe,play} [file]
```

### Subcommands

| Command | Description |
| ------- | ----------- |
| `repl` | Interactive REPL with syntax highlighting and auto-completion |
| `ports` | List available MIDI ports (both input and output) |
| `transcribe` | Record MIDI input and output Alda code |
| `play` | Play an Alda file or code (default behavior) |

### Options

| Option | Description |
| ------ | ----------- |
| `file` | Alda file to play (use `-` for stdin) |
| `-e, --eval CODE` | Evaluate Alda code directly |
| `-o, --output FILE` | Save to MIDI file instead of playing |
| `--port NAME\|INDEX` | MIDI port by name or index (see `aldakit ports`). Auto-selects if only one port available. |
| `--stdin` | Read from stdin (blank line to play) |
| `--parse-only` | Print AST without playing |
| `--no-wait` | Don't wait for playback to finish |
| `-v, --verbose` | Verbose output |

### Examples

```bash
# Interactive REPL with syntax highlighting
aldakit repl

# List available MIDI ports (input and output)
aldakit ports
aldakit ports -o  # output ports only
aldakit ports -i  # input ports only

# Play with verbose output
aldakit -v examples/jazz.alda

# Play to a specific port (by index or name)
aldakit --port 0 examples/twinkle.alda
aldakit --port FluidSynth examples/twinkle.alda

# Read from stdin
echo "piano: c d e f g" | aldakit -

# Parse and show AST
aldakit --parse-only -e "piano: c/e/g"

# Export to MIDI file
aldakit examples/twinkle.alda -o twinkle.mid

# Record MIDI input for 10 seconds (default)
aldakit transcribe

# Record from a specific input port (by index or name)
aldakit transcribe --port 0
aldakit transcribe --port "My MIDI Keyboard"

# Record for 30 seconds with verbose note display
aldakit transcribe -d 30 -v

# Record with Alda-style note display
aldakit transcribe -d 10 -v --alda-notes

# Record and save to file
aldakit transcribe -o recording.alda
aldakit transcribe -o recording.mid

# Record and play back
aldakit transcribe --play

# Record with custom settings (swing feel, triplet quantization)
aldakit transcribe -d 20 -t 90 -i guitar --feel triplet --play
```

## Interactive REPL

The REPL provides an interactive environment for composing and playing Alda code:

```bash
aldakit repl
```

Features:

- Syntax highlighting
- Auto-completion for instruments (3+ characters)
- Command history (persistent across sessions)
- Multi-line paste (use platform-specific paste: ctrl-v, shift-ctrl-v, cmd-v, etc.)
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

See [midi/types.py](https://github.com/shakfu/aldakit/blob/main/src/aldakit/midi/types.py) for the complete mapping.

## MIDI Backend

aldakit uses [libremidi](https://github.com/jcelerier/libremidi) via [nanobind](https://github.com/wjakob/nanobind) for cross-platform MIDI I/O:

- Low-latency realtime playback
- Virtual MIDI port support (AldakitMIDI), makes it easy to just send to your DAW.
- Pure Python MIDI file writing (no external dependencies)
- Cross-platform: macOS (CoreMIDI), Linux (ALSA), Windows (WinMM)
- Supports hardware and software/virtual MIDI ports (FluidSynth, IAC Driver, etc.)

```python
import aldakit

# List available ports
print(aldakit.list_ports())

# Play to virtual port (visible in DAWs like Ableton Live)
aldakit.play("piano: c d e f g")

# Play to a specific port
aldakit.play("piano: c d e f g", port="FluidSynth")

# Save to MIDI file
aldakit.save("piano: c d e f g", "output.mid")
```

## Audio Backend (Built-in)

For self-contained audio playback without external synthesizers, aldakit includes a built-in audio backend powered by [TinySoundFont](https://github.com/schellingb/TinySoundFont) and [miniaudio](https://github.com/mackron/miniaudio):

- Direct audio output (no FluidSynth or DAW required)
- Cross-platform: macOS (CoreAudio), Linux (ALSA/PulseAudio), Windows (WASAPI)
- Requires a SoundFont file (.sf2) for instrument sounds
- Header-only libraries for minimal binary size

### Basic Usage

```python
from aldakit import Score

# Play with built-in audio (requires SoundFont)
score = Score("piano: c d e f g")
score.play(backend="audio")

# Specify SoundFont explicitly
score.play(backend="audio", soundfont="/path/to/FluidR3_GM.sf2")
```

### SoundFont Setup

The audio backend requires a General MIDI SoundFont file. aldakit searches these locations automatically:

- `$ALDAKIT_SOUNDFONT` environment variable
- `~/Music/sf2/`
- `~/.aldakit/soundfonts/`
- `/usr/share/soundfonts/` (Linux)

**Option 1: Download manually**

Download a SoundFont and place it in `~/Music/sf2/`:
- [FluidR3_GM.sf2](https://archive.org/download/fluidr3-gm-gs/FluidR3_GM.sf2) (141 MB, high quality)
- [TimGM6mb.sf2](https://archive.org/download/TimGM6mb/TimGM6mb.sf2) (5.8 MB, compact)
- [GeneralUser_GS.sf2](https://archive.org/download/GeneralUserGS/GeneralUser_GS_1.471.sf2) (31 MB, balanced)

**Option 2: Auto-download**

```python
from aldakit.midi.soundfont import setup_soundfont

# Downloads TimGM6mb.sf2 (~6 MB) to ~/.aldakit/soundfonts/
setup_soundfont()
```

**Option 3: Environment variable**

```bash
export ALDAKIT_SOUNDFONT=/path/to/your/soundfont.sf2
```

### Using TsfBackend Directly

```python
from aldakit import Score
from aldakit.midi.backends import TsfBackend

# Create backend with specific SoundFont
with TsfBackend(soundfont="~/Music/sf2/FluidR3_GM.sf2") as backend:
    score = Score("piano: c/e/g")
    backend.play(score.midi)
    backend.wait()  # Block until playback completes

# Inspect SoundFont presets
backend = TsfBackend()
print(f"Presets: {backend.preset_count}")
for i in range(min(10, backend.preset_count)):
    print(f"  {i}: {backend.preset_name(i)}")
```

### Audio vs MIDI Backend

| Feature | Audio (`backend="audio"`) | MIDI (`backend="midi"`) |
|---------|---------------------------|-------------------------|
| External synth required | No | Yes (FluidSynth, DAW, hardware) |
| Setup complexity | Just needs SoundFont | Requires MIDI routing |
| Sound quality | Depends on SoundFont | Depends on synth |
| DAW integration | No | Yes (virtual port) |
| Latency | Very low | Very low |
| Effects (reverb, etc.) | No | Depends on synth |

**Recommendation:** Use `backend="audio"` for quick playback and standalone use. Use `backend="midi"` (default) for DAW integration, hardware synths, or when you need effects.

## MIDI Playback Setup

### Virtual Port (Recommended)

When no hardware MIDI ports are available, aldakit creates a virtual port named "AldakitMIDI". This port is visible to DAWs and other MIDI software:

1. Start the REPL: `aldakit repl`
2. In your DAW (Ableton Live, Logic Pro, etc.), look for "AldakitMIDI" in MIDI input settings
3. Play code in the REPL - notes will be sent to your DAW

### Software Synthesizer (FluidSynth)

For high-quality General MIDI playback without hardware, use [FluidSynth](https://www.fluidsynth.org/):

```sh
# Install FluidSynth (macOS)
brew install fluidsynth

# Install FluidSynth (Debian/Ubuntu)
sudo apt install fluidsynth 

# Download a SoundFont (e.g., FluidR3_GM.sf2)
# eg. sudo apt install fluid-soundfont-gm
# Place in ~/Music/sf2/

# Start FluidSynth with CoreMIDI (macOS)
fluidsynth -a coreaudio -m coremidi ~/Music/sf2/FluidR3_GM.sf2

# In another terminal, start aldakit
aldakit repl
# aldakit> piano: c d e f g
```

A helper script is available in the [repository](https://github.com/shakfu/aldakit/tree/main/scripts):

```sh
# Set the SoundFont directory (add to your shell profile)
export ALDAPY_SF2_DIR=~/Music/sf2

# Run with default SoundFont (FluidR3_GM.sf2)
python scripts/fluidsynth-gm.py

# Or specify a SoundFont directly
python scripts/fluidsynth-gm.py /path/to/soundfont.sf2

# List available SoundFonts
python scripts/fluidsynth-gm.py --list
```

### Hardware MIDI

Connect a USB MIDI interface or synthesizer, then:

```sh
# List available ports
aldakit ports

# Play to a specific port
aldakit --port "My MIDI Device" examples/twinkle.alda
```

### MIDI File Export

If you don't have MIDI playback set up, export to a file:

```bash
# Save to MIDI file
aldakit examples/twinkle.alda -o twinkle.mid

# Open with default app
open twinkle.mid
```

## Development

### Setup

```sh
git clone https://github.com/shakfu/aldakit.git
cd aldakit
make  # Build the libremidi extension
```

### Run Tests

```sh
make test
# or
uv run pytest tests/ -v
```

### Architecture

![aldakit architecture](https://raw.githubusercontent.com/shakfu/aldakit/main/docs/assets/architecture.svg)

## License

MIT

## See Also

- [Alda](https://alda.io) - The original Alda language and reference implementation
- [Alda Cheat Sheet](https://alda.io/cheat-sheet/) - Syntax reference
- [Extending aldakit](https://github.com/shakfu/aldakit/blob/main/docs/extending-aldakit.md) - Design document for programmatic API
- [libremidi](https://github.com/celtera/libremidi) - A modern C++ MIDI 1 / MIDI 2 real-time & file I/O library. Supports Windows, macOS, Linux and WebMIDI.
- [TinySoundFont](https://github.com/schellingb/TinySoundFont) - SoundFont2 synthesizer library in a single C/C++ header
- [miniaudio](https://github.com/mackron/miniaudio) - Single-header audio playback and capture library
- [nanobind](https://github.com/wjakob/nanobind) - a tiny and efficient C++/Python bindings