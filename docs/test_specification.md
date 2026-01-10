# Alda Language Test Specification

This document defines language-agnostic test cases for validating Alda implementations. Tests are specified as input/expected output pairs that any implementation should satisfy.

## Notation

- `input:` The Alda source code to parse/execute
- `expect:` The expected MIDI output or behavior
- `notes:` Implementation notes

---

## 1. Note Basics

### 1.1 Single Note

```yaml
input: "c"
expect:
  notes: 1
  pitch: 60  # C4 (middle C)
  octave: 4  # default
```

### 1.2 All Note Letters

```yaml
input: "c d e f g a b"
expect:
  notes: 7
  pitches: [60, 62, 64, 65, 67, 69, 71]  # C4 to B4
```

### 1.3 Rest

```yaml
input: "c r d"
expect:
  notes: 2  # rest produces no note
  # d should start after c's duration + rest duration
```

---

## 2. Accidentals

### 2.1 Sharp

```yaml
input: "c+"
expect:
  pitch: 61  # C#4
```

### 2.2 Flat

```yaml
input: "b-"
expect:
  pitch: 70  # Bb4
```

### 2.3 Natural

```yaml
input: "f_"
expect:
  pitch: 65  # F4 (natural, same as f)
```

### 2.4 Double Sharp

```yaml
input: "c++"
expect:
  pitch: 62  # C##4 = D4
```

### 2.5 Double Flat

```yaml
input: "d--"
expect:
  pitch: 60  # Dbb4 = C4
```

---

## 3. Octaves

### 3.1 Octave Set

```yaml
input: "o5 c"
expect:
  pitch: 72  # C5
```

### 3.2 Octave Up

```yaml
input: "> c"
expect:
  pitch: 72  # C5 (default is o4, so >c = o5 c)
```

### 3.3 Octave Down

```yaml
input: "< c"
expect:
  pitch: 48  # C3
```

### 3.4 Multiple Octave Shifts

```yaml
input: ">> c"
expect:
  pitch: 84  # C6
```

### 3.5 Octave Range

```yaml
input: "o0 c"
expect:
  pitch: 12  # C0

input: "o8 c"
expect:
  pitch: 108  # C8
```

---

## 4. Durations

### 4.1 Quarter Note (Default Tempo 120 BPM)

```yaml
input: "c4"
expect:
  duration_seconds: 0.5  # 60/120 BPM
  # Note: actual sounding duration affected by quantization (default 90%)
```

### 4.2 Half Note

```yaml
input: "c2"
expect:
  duration_seconds: 1.0
```

### 4.3 Whole Note

```yaml
input: "c1"
expect:
  duration_seconds: 2.0
```

### 4.4 Eighth Note

```yaml
input: "c8"
expect:
  duration_seconds: 0.25
```

### 4.5 Dotted Quarter

```yaml
input: "c4."
expect:
  duration_seconds: 0.75  # quarter + eighth = 0.5 + 0.25
```

### 4.6 Double-Dotted Quarter

```yaml
input: "c4.."
expect:
  duration_seconds: 0.875  # 0.5 + 0.25 + 0.125
```

### 4.7 Milliseconds Duration

```yaml
input: "c500ms"
expect:
  duration_seconds: 0.5
```

### 4.8 Seconds Duration

```yaml
input: "c2s"
expect:
  duration_seconds: 2.0
```

### 4.9 Default Duration Persistence

```yaml
input: "c4 d e f"
expect:
  notes: 4
  # all notes should have quarter note duration
```

### 4.10 Tied Durations

```yaml
input: "c4~4"
expect:
  notes: 1  # single note held
  duration_seconds: 1.0  # quarter + quarter
```

---

## 5. Chords

### 5.1 Simple Triad

```yaml
input: "c/e/g"
expect:
  notes: 3
  pitches: [60, 64, 67]  # C, E, G
  # all notes start at same time
  same_start_time: true
```

### 5.2 Chord with Duration

```yaml
input: "c1/e/g"
expect:
  notes: 3
  # all notes have whole note duration
```

### 5.3 Chord with Octave Changes

```yaml
input: "c/>e/g"
expect:
  pitches: [60, 76, 79]  # C4, E5, G5
```

---

## 6. Tempo

### 6.1 Set Tempo

```yaml
input: "(tempo 60) c4"
expect:
  duration_seconds: 1.0  # 60/60 BPM = 1 second per beat
```

### 6.2 Global Tempo

```yaml
input: "(tempo! 240) c4"
expect:
  duration_seconds: 0.25  # 60/240 = 0.25 seconds
```

---

## 7. Volume

### 7.1 Volume Attribute

```yaml
input: "(vol 50) c"
expect:
  velocity: 63  # 50% of 127 ≈ 63
```

### 7.2 Full Volume

```yaml
input: "(volume 100) c"
expect:
  velocity: 127
```

### 7.3 Dynamic Markings

```yaml
input: "(ff) c"
expect:
  velocity: 100  # or implementation-specific ff value
```

---

## 8. Parts

### 8.1 Piano Part

```yaml
input: "piano: c d e"
expect:
  notes: 3
  program: 0  # GM Piano
```

### 8.2 Violin Part

```yaml
input: "violin: c d e"
expect:
  program: 40  # GM Violin
```

### 8.3 Multiple Parts

```yaml
input: |
  piano: c d e
  violin: f g a
expect:
  notes: 6
  programs: [0, 40]
```

### 8.4 Part Groups

```yaml
input: "piano/violin: c d e"
expect:
  notes: 6  # 3 notes on each instrument
```

---

## 9. Variables

### 9.1 Definition Does Not Emit

```yaml
input: "theme = c d e"
expect:
  notes: 0  # definition stores, doesn't play
```

### 9.2 Reference Plays

```yaml
input: |
  theme = c d e
  theme
expect:
  notes: 3
```

### 9.3 Multiple References

```yaml
input: |
  theme = c d e
  theme theme
expect:
  notes: 6
```

---

## 10. Markers

### 10.1 Marker Definition

```yaml
input: "c d e %verse f g"
expect:
  notes: 5
  # %verse records the time position after 'e'
```

### 10.2 Marker Jump

```yaml
input: |
  piano: c d e %verse f g
  violin: @verse a b
expect:
  # violin's 'a' starts at the same time as piano's 'f'
```

---

## 11. Voices

### 11.1 Two Voices

```yaml
input: "V1: c4 d4 V2: e4 f4 V0:"
expect:
  notes: 4
  # V1 notes at times: 0, 0.5
  # V2 notes at times: 0, 0.5 (parallel)
```

### 11.2 Voice Merge

```yaml
input: |
  V1: c4 d4
  V2: e2
  V0: g4
expect:
  notes: 4
  # g4 starts after both V1 and V2 complete
```

---

## 12. Repeats

### 12.1 Repeat Note

```yaml
input: "c*4"
expect:
  notes: 4
  pitches: [60, 60, 60, 60]
```

### 12.2 Repeat Sequence

```yaml
input: "[c d]*3"
expect:
  notes: 6
  pitches: [60, 62, 60, 62, 60, 62]
```

### 12.3 On-Repetitions (Alternate Endings)

```yaml
input: "[c'1 d'2]*2"
expect:
  notes: 2
  # First iteration: plays 'c' (repetition 1)
  # Second iteration: plays 'd' (repetition 2)
```

---

## 13. Cram (Tuplets)

### 13.1 Triplet

```yaml
input: "{c d e}2"
expect:
  notes: 3
  # 3 notes fit into a half note duration
  # Each note: half_note_duration / 3
```

### 13.2 Quintuplet

```yaml
input: "{c d e f g}4"
expect:
  notes: 5
  # 5 notes fit into a quarter note
```

---

## 14. Quantization

### 14.1 Default Quantization

```yaml
input: "c4"
expect:
  # At 90% quantization, note sounds for 90% of its value
  sounding_duration: 0.45  # 0.5 * 0.9
```

### 14.2 Legato

```yaml
input: "(quant 100) c4"
expect:
  sounding_duration: 0.5  # full duration
```

### 14.3 Staccato

```yaml
input: "(quant 50) c4"
expect:
  sounding_duration: 0.25  # half duration
```

---

## 15. Slurs

### 15.1 Slurred Notes

```yaml
input: "c~d"
expect:
  notes: 2
  # first note (c) has full duration (no quantization cut)
  # indicates legato connection
```

---

## 16. Barlines

### 16.1 Barlines Are Visual Only

```yaml
input: "c | d | e | f"
expect:
  notes: 4
  # barlines have no effect on timing
```

---

## 17. MIDI Pitch Reference

| Note | Octave 0 | Octave 4 | Octave 8 |
|------|----------|----------|----------|
| C    | 12       | 60       | 108      |
| D    | 14       | 62       | 110      |
| E    | 16       | 64       | 112      |
| F    | 17       | 65       | 113      |
| G    | 19       | 67       | 115      |
| A    | 21       | 69       | 117      |
| B    | 23       | 71       | 119      |

---

## 18. Default Values

| Parameter | Default |
|-----------|---------|
| Tempo | 120 BPM |
| Octave | 4 |
| Volume/Velocity | ~80% (102/127) |
| Quantization | 90% |
| Duration | Quarter note (4) |

---

## Implementation Notes

1. **Timing precision**: Implementations may differ slightly in floating-point timing calculations. Tests should allow for small tolerances (e.g., 0.01 seconds).

2. **MIDI ticks**: Internal tick resolution may vary. aldakit uses seconds; alda-midi uses 480 ticks per quarter note.

3. **Velocity mapping**: Dynamic markings (pp, mf, ff) may have slightly different velocity values between implementations.

4. **Channel assignment**: Implementations should assign channels sequentially, skipping channel 10 (percussion).

5. **Voice termination**: aldakit requires explicit `V0:` to terminate voice groups in certain contexts.
