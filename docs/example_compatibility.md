# Example File Compatibility Report

This document tracks the compatibility of example `.alda` files between [aldakit](https://github.com/shakfu/aldakit) and [alda-midi](https://github.com/shakfu/midi-langs) implementations.

## Summary

- **Total examples**: 40
- **Compatible**: 40 (100%)

## Compatible Examples (40/40)

All examples parse and generate MIDI correctly in aldakit:

| Example | Description |
|---------|-------------|
| across_the_sea.alda | Multi-instrument piece |
| all-instruments.alda | All 128 GM instruments |
| alternate-endings.alda | Repeat with alternate endings |
| awobmolg.alda | Complex piece |
| bach-prelude.alda | Bach Prelude |
| bach_cello_suite_no_1.alda | Bach Cello Suite |
| chords.alda | Chord notation |
| cram.alda | Cram/tuplet expressions |
| debussy_quartet.alda | Debussy String Quartet excerpt |
| dot_accessor.alda | Dot duration accessor |
| duet.alda | Two-instrument piece |
| dynamics.alda | Dynamic markings (pp to ff) |
| gau.alda | Complex rhythmic piece |
| hello_world.alda | Basic example |
| jazz.alda | Jazz piece |
| jimenez-divertimento.alda | Jimenez Divertimento |
| key_signature.alda | Key signature examples |
| midi-channel-management.alda | Multi-part channel handling |
| midi-channel-management-2.alda | Extended channel management |
| modes.alda | Musical modes |
| multi-poly.alda | Multiple polyphonic voices |
| nesting.alda | Nested structures |
| nicechord-alda-demo.alda | Demo piece |
| nicechord-transposed-variable.alda | Variables with transposition |
| orchestra.alda | Full orchestra |
| overriding-a-global-attribute.alda | Attribute scoping |
| panning.alda | Stereo panning |
| percussion.alda | Percussion notation |
| phase.alda | Phase music |
| poly.alda | Polyphonic voices |
| rachmaninoff_piano_concerto_2_mvmt_2.alda | Rachmaninoff excerpt |
| repeats.alda | Repeat syntax |
| seconds_and_milliseconds.alda | Duration in seconds/ms |
| simple.alda | Simple scale |
| track-volume.alda | Volume control |
| twinkle.alda | Twinkle Twinkle Little Star |
| variables-2.alda | Variable usage |
| variables.alda | Variable definitions |
| voices.alda | Voice groups |

## Fixes Applied

1. **midi-channel-management.alda**: Added `V0:` to close voice group inside bracketed variable definition. aldakit requires explicit voice group termination.

2. **Quoted list syntax**: Added support for Lisp-style quoted lists `'(...)` in S-expressions, enabling files using `(key-signature '(g minor))` syntax.

## Feature Status

All Alda language features are now fully implemented in aldakit:

- **key-signature**: Fully implemented and applies accidentals correctly
- **transpose**: Fully implemented with semitone offsets

All 40 example files parse and generate MIDI correctly with full feature support.
