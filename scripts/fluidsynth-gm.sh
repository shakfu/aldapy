#!/bin/bash
# Start FluidSynth with General MIDI SoundFont for use with pyalda
#
# Usage: ./scripts/fluidsynth-gm.sh [soundfont]
#
# Once running, start pyalda in another terminal:
#   pyalda repl
#   pyalda> piano: c d e f g

SF2_DIR="$HOME/Music/sf2"
DEFAULT_SF2="$SF2_DIR/FluidR3_GM.sf2"

SF2="${1:-$DEFAULT_SF2}"

if [[ ! -f "$SF2" ]]; then
    echo "SoundFont not found: $SF2"
    echo "Available SoundFonts in $SF2_DIR:"
    ls -1 "$SF2_DIR"/*.sf2 "$SF2_DIR"/*.sf3 2>/dev/null
    exit 1
fi

echo "Starting FluidSynth with: $(basename "$SF2")"
echo "Connect pyalda via: pyalda repl"
echo "Press Ctrl+C to stop"
echo

fluidsynth \
    -a coreaudio \
    -m coremidi \
    -g 1.0 \
    "$SF2"
