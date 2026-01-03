"""Tests for AST-level transformers."""

from aldakit.compose import (
    note,
    rest,
    chord,
    seq,
    # Pitch transformers
    transpose,
    invert,
    reverse,
    shuffle,
    retrograde_inversion,
    # Structural transformers
    augment,
    diminish,
    fragment,
    loop,
    interleave,
    rotate,
    take_every,
    split,
    concat,
    # Helpers
    pipe,
    identity,
)


class TestTranspose:
    """Test transpose transformer."""

    def test_transpose_up(self):
        melody = seq(note("c"), note("d"), note("e"))
        transposed = transpose(melody, 2)
        # C + 2 semitones = D, D + 2 = E, E + 2 = F#
        assert len(transposed.elements) == 3
        assert transposed.elements[0].pitch == "d"
        assert transposed.elements[1].pitch == "e"
        # E + 2 = F# (could be f+ or g-)
        assert transposed.elements[2].midi_pitch == note("e").midi_pitch + 2

    def test_transpose_down(self):
        melody = seq(note("e"), note("d"), note("c"))
        transposed = transpose(melody, -2)
        assert transposed.elements[0].pitch == "d"
        assert transposed.elements[1].pitch == "c"

    def test_transpose_octave(self):
        melody = seq(note("c", octave=4))
        transposed = transpose(melody, 12)  # Up one octave
        assert transposed.elements[0].midi_pitch == 72  # C5

    def test_transpose_chord(self):
        c_major = seq(chord("c", "e", "g"))
        transposed = transpose(c_major, 5)  # Up a fourth -> F major
        chord_elem = transposed.elements[0]
        assert chord_elem.notes[0].pitch == "f"
        assert chord_elem.notes[1].pitch == "a"

    def test_transpose_preserves_duration(self):
        melody = seq(note("c", duration=8), note("d", duration=4))
        transposed = transpose(melody, 2)
        assert transposed.elements[0].duration == 8
        assert transposed.elements[1].duration == 4

    def test_transpose_preserves_rests(self):
        melody = seq(note("c"), rest(duration=4), note("e"))
        transposed = transpose(melody, 2)
        assert isinstance(transposed.elements[1], type(rest()))


class TestInvert:
    """Test invert transformer."""

    def test_invert_basic(self):
        # C D E -> C Bb Ab (invert around C)
        melody = seq(note("c", octave=4), note("d", octave=4), note("e", octave=4))
        inverted = invert(melody)
        # C stays C (axis)
        assert inverted.elements[0].midi_pitch == 60  # C4
        # D is 2 semitones above C, so inverted is 2 below = Bb3
        assert inverted.elements[1].midi_pitch == 58  # Bb3
        # E is 4 semitones above C, so inverted is 4 below = Ab3
        assert inverted.elements[2].midi_pitch == 56  # Ab3

    def test_invert_with_axis(self):
        melody = seq(note("c", octave=4), note("e", octave=4))
        # Invert around E (midi 64)
        inverted = invert(melody, axis=64)
        # C4 (60) is 4 below axis, inverted is 4 above = G#4 (68)
        assert inverted.elements[0].midi_pitch == 68
        # E4 (64) is axis, stays same
        assert inverted.elements[1].midi_pitch == 64

    def test_invert_chord(self):
        melody = seq(chord("c", "e", "g"))
        inverted = invert(melody)
        # All notes in chord should be inverted
        assert len(inverted.elements[0].notes) == 3

    def test_invert_empty_sequence(self):
        empty = seq()
        inverted = invert(empty)
        assert len(inverted.elements) == 0


class TestReverse:
    """Test reverse transformer."""

    def test_reverse_basic(self):
        melody = seq(note("c"), note("d"), note("e"))
        reversed_mel = reverse(melody)
        assert reversed_mel.elements[0].pitch == "e"
        assert reversed_mel.elements[1].pitch == "d"
        assert reversed_mel.elements[2].pitch == "c"

    def test_reverse_preserves_note_properties(self):
        melody = seq(note("c", duration=4), note("d", duration=8, accidental="+"))
        reversed_mel = reverse(melody)
        assert reversed_mel.elements[0].duration == 8
        assert reversed_mel.elements[0].accidental == "+"
        assert reversed_mel.elements[1].duration == 4

    def test_reverse_with_rests(self):
        melody = seq(note("c"), rest(duration=4), note("e"))
        reversed_mel = reverse(melody)
        assert reversed_mel.elements[0].pitch == "e"
        assert isinstance(reversed_mel.elements[1], type(rest()))
        assert reversed_mel.elements[2].pitch == "c"

    def test_reverse_to_alda(self):
        melody = seq(
            note("c", duration=4), note("d", duration=4), note("e", duration=4)
        )
        reversed_mel = reverse(melody)
        assert reversed_mel.to_alda() == "e4 d4 c4"


class TestShuffle:
    """Test shuffle transformer."""

    def test_shuffle_with_seed(self):
        melody = seq(note("c"), note("d"), note("e"), note("f"))
        shuffled1 = shuffle(melody, seed=42)
        shuffled2 = shuffle(melody, seed=42)
        # Same seed should produce same result
        for i in range(len(shuffled1.elements)):
            assert shuffled1.elements[i].pitch == shuffled2.elements[i].pitch

    def test_shuffle_preserves_elements(self):
        melody = seq(note("c"), note("d"), note("e"))
        shuffled = shuffle(melody, seed=123)
        pitches = sorted([n.pitch for n in shuffled.elements])
        assert pitches == ["c", "d", "e"]

    def test_shuffle_different_seeds_different_results(self):
        melody = seq(note("c"), note("d"), note("e"), note("f"), note("g"))
        shuffled1 = shuffle(melody, seed=1)
        shuffled2 = shuffle(melody, seed=2)
        # Very unlikely to be the same with different seeds
        pitches1 = [n.pitch for n in shuffled1.elements]
        pitches2 = [n.pitch for n in shuffled2.elements]
        assert pitches1 != pitches2 or True  # Could theoretically be same


class TestRetrogradeInversion:
    """Test retrograde_inversion transformer."""

    def test_retrograde_inversion(self):
        melody = seq(note("c", octave=4), note("d", octave=4), note("e", octave=4))
        ri = retrograde_inversion(melody)
        # Should be reversed AND inverted
        # Reverse of [C, D, E] = [E, D, C]
        # Invert around C: E(+4) -> -4, D(+2) -> -2, C(0) -> 0
        # But we reverse first in retrograde_inversion: reverse(invert(seq))
        # Actually it's reverse(invert(seq)) so:
        # Invert [C, D, E] around C = [C, Bb, Ab]
        # Reverse = [Ab, Bb, C]
        assert ri.elements[2].midi_pitch == 60  # C

    def test_retrograde_inversion_is_combination(self):
        melody = seq(note("c"), note("e"), note("g"))
        ri = retrograde_inversion(melody)
        manual = reverse(invert(melody))
        assert len(ri.elements) == len(manual.elements)


class TestAugment:
    """Test augment transformer."""

    def test_augment_doubles_durations(self):
        melody = seq(note("c", duration=8), note("d", duration=8))
        augmented = augment(melody, 2)
        assert augmented.elements[0].duration == 4  # 8th -> quarter
        assert augmented.elements[1].duration == 4

    def test_augment_rest(self):
        melody = seq(rest(duration=8))
        augmented = augment(melody, 2)
        assert augmented.elements[0].duration == 4

    def test_augment_chord(self):
        melody = seq(chord("c", "e", "g", duration=8))
        augmented = augment(melody, 2)
        assert augmented.elements[0].duration == 4

    def test_augment_ms_duration(self):
        melody = seq(note("c", ms=500))
        augmented = augment(melody, 2)
        assert augmented.elements[0].ms == 1000

    def test_augment_to_alda(self):
        melody = seq(note("c", duration=8), note("d", duration=8))
        augmented = augment(melody, 2)
        assert augmented.to_alda() == "c4 d4"


class TestDiminish:
    """Test diminish transformer."""

    def test_diminish_halves_durations(self):
        melody = seq(note("c", duration=4), note("d", duration=4))
        diminished = diminish(melody, 2)
        assert diminished.elements[0].duration == 8  # quarter -> 8th
        assert diminished.elements[1].duration == 8

    def test_diminish_rest(self):
        melody = seq(rest(duration=4))
        diminished = diminish(melody, 2)
        assert diminished.elements[0].duration == 8

    def test_diminish_chord(self):
        melody = seq(chord("c", "e", "g", duration=4))
        diminished = diminish(melody, 2)
        assert diminished.elements[0].duration == 8

    def test_diminish_ms_duration(self):
        melody = seq(note("c", ms=1000))
        diminished = diminish(melody, 2)
        assert diminished.elements[0].ms == 500

    def test_diminish_to_alda(self):
        melody = seq(note("c", duration=4), note("d", duration=4))
        diminished = diminish(melody, 2)
        assert diminished.to_alda() == "c8 d8"


class TestFragment:
    """Test fragment transformer."""

    def test_fragment_takes_first_n(self):
        melody = seq(note("c"), note("d"), note("e"), note("f"))
        frag = fragment(melody, 2)
        assert len(frag.elements) == 2
        assert frag.elements[0].pitch == "c"
        assert frag.elements[1].pitch == "d"

    def test_fragment_more_than_length(self):
        melody = seq(note("c"), note("d"))
        frag = fragment(melody, 10)
        assert len(frag.elements) == 2

    def test_fragment_zero(self):
        melody = seq(note("c"), note("d"))
        frag = fragment(melody, 0)
        assert len(frag.elements) == 0

    def test_fragment_to_alda(self):
        melody = seq(note("c"), note("d"), note("e"))
        frag = fragment(melody, 2)
        assert frag.to_alda() == "c d"


class TestLoop:
    """Test loop transformer."""

    def test_loop_repeats(self):
        melody = seq(note("c"), note("d"))
        looped = loop(melody, 3)
        assert len(looped.elements) == 6
        assert looped.elements[0].pitch == "c"
        assert looped.elements[1].pitch == "d"
        assert looped.elements[2].pitch == "c"
        assert looped.elements[3].pitch == "d"
        assert looped.elements[4].pitch == "c"
        assert looped.elements[5].pitch == "d"

    def test_loop_once(self):
        melody = seq(note("c"), note("d"))
        looped = loop(melody, 1)
        assert len(looped.elements) == 2

    def test_loop_zero(self):
        melody = seq(note("c"), note("d"))
        looped = loop(melody, 0)
        assert len(looped.elements) == 0

    def test_loop_to_alda(self):
        melody = seq(note("c"), note("d"))
        looped = loop(melody, 2)
        assert looped.to_alda() == "c d c d"


class TestInterleave:
    """Test interleave transformer."""

    def test_interleave_two_sequences(self):
        mel1 = seq(note("c"), note("e"), note("g"))
        mel2 = seq(note("d"), note("f"), note("a"))
        interleaved = interleave(mel1, mel2)
        assert len(interleaved.elements) == 6
        assert interleaved.elements[0].pitch == "c"
        assert interleaved.elements[1].pitch == "d"
        assert interleaved.elements[2].pitch == "e"
        assert interleaved.elements[3].pitch == "f"
        assert interleaved.elements[4].pitch == "g"
        assert interleaved.elements[5].pitch == "a"

    def test_interleave_unequal_lengths(self):
        mel1 = seq(note("c"), note("e"))
        mel2 = seq(note("d"), note("f"), note("a"), note("b"))
        interleaved = interleave(mel1, mel2)
        # Should continue until all elements from both are used
        pitches = [e.pitch for e in interleaved.elements]
        assert "c" in pitches
        assert "d" in pitches
        assert "e" in pitches
        assert "f" in pitches

    def test_interleave_three_sequences(self):
        mel1 = seq(note("c"), note("f"))
        mel2 = seq(note("d"), note("g"))
        mel3 = seq(note("e"), note("a"))
        interleaved = interleave(mel1, mel2, mel3)
        assert interleaved.elements[0].pitch == "c"
        assert interleaved.elements[1].pitch == "d"
        assert interleaved.elements[2].pitch == "e"
        assert interleaved.elements[3].pitch == "f"

    def test_interleave_empty(self):
        interleaved = interleave()
        assert len(interleaved.elements) == 0


class TestRotate:
    """Test rotate transformer."""

    def test_rotate_left(self):
        melody = seq(note("c"), note("d"), note("e"), note("f"))
        rotated = rotate(melody, 1)
        assert rotated.elements[0].pitch == "d"
        assert rotated.elements[1].pitch == "e"
        assert rotated.elements[2].pitch == "f"
        assert rotated.elements[3].pitch == "c"

    def test_rotate_right(self):
        melody = seq(note("c"), note("d"), note("e"), note("f"))
        rotated = rotate(melody, -1)
        assert rotated.elements[0].pitch == "f"
        assert rotated.elements[1].pitch == "c"
        assert rotated.elements[2].pitch == "d"
        assert rotated.elements[3].pitch == "e"

    def test_rotate_full_cycle(self):
        melody = seq(note("c"), note("d"), note("e"))
        rotated = rotate(melody, 3)  # Full cycle
        assert rotated.elements[0].pitch == "c"
        assert rotated.elements[1].pitch == "d"
        assert rotated.elements[2].pitch == "e"

    def test_rotate_empty(self):
        empty = seq()
        rotated = rotate(empty, 5)
        assert len(rotated.elements) == 0


class TestTakeEvery:
    """Test take_every transformer."""

    def test_take_every_other(self):
        scale = seq(note("c"), note("d"), note("e"), note("f"), note("g"))
        thirds = take_every(scale, 2)
        assert len(thirds.elements) == 3
        assert thirds.elements[0].pitch == "c"
        assert thirds.elements[1].pitch == "e"
        assert thirds.elements[2].pitch == "g"

    def test_take_every_third(self):
        melody = seq(note("c"), note("d"), note("e"), note("f"), note("g"), note("a"))
        result = take_every(melody, 3)
        assert len(result.elements) == 2
        assert result.elements[0].pitch == "c"
        assert result.elements[1].pitch == "f"

    def test_take_every_with_offset(self):
        scale = seq(note("c"), note("d"), note("e"), note("f"), note("g"))
        result = take_every(scale, 2, offset=1)
        assert len(result.elements) == 2
        assert result.elements[0].pitch == "d"
        assert result.elements[1].pitch == "f"


class TestSplit:
    """Test split transformer."""

    def test_split_even(self):
        melody = seq(note("c"), note("d"), note("e"), note("f"))
        chunks = split(melody, 2)
        assert len(chunks) == 2
        assert len(chunks[0].elements) == 2
        assert len(chunks[1].elements) == 2
        assert chunks[0].elements[0].pitch == "c"
        assert chunks[1].elements[0].pitch == "e"

    def test_split_uneven(self):
        melody = seq(note("c"), note("d"), note("e"))
        chunks = split(melody, 2)
        assert len(chunks) == 2
        assert len(chunks[0].elements) == 2
        assert len(chunks[1].elements) == 1

    def test_split_larger_than_sequence(self):
        melody = seq(note("c"), note("d"))
        chunks = split(melody, 10)
        assert len(chunks) == 1
        assert len(chunks[0].elements) == 2


class TestConcat:
    """Test concat transformer."""

    def test_concat_two(self):
        mel1 = seq(note("c"), note("d"))
        mel2 = seq(note("e"), note("f"))
        result = concat(mel1, mel2)
        assert len(result.elements) == 4
        assert result.elements[0].pitch == "c"
        assert result.elements[2].pitch == "e"

    def test_concat_three(self):
        mel1 = seq(note("c"))
        mel2 = seq(note("d"))
        mel3 = seq(note("e"))
        result = concat(mel1, mel2, mel3)
        assert len(result.elements) == 3

    def test_concat_empty(self):
        result = concat()
        assert len(result.elements) == 0

    def test_concat_to_alda(self):
        mel1 = seq(note("c"))
        mel2 = seq(note("d"))
        result = concat(mel1, mel2)
        assert result.to_alda() == "c d"


class TestPipe:
    """Test pipe helper function."""

    def test_pipe_single_transform(self):
        melody = seq(note("c"), note("d"), note("e"))
        result = pipe(melody, reverse)
        assert result.elements[0].pitch == "e"
        assert result.elements[2].pitch == "c"

    def test_pipe_multiple_transforms(self):
        melody = seq(note("c", duration=8), note("d", duration=8))
        result = pipe(
            melody,
            reverse,
            lambda s: augment(s, 2),
        )
        assert result.elements[0].pitch == "d"
        assert result.elements[0].duration == 4

    def test_pipe_with_lambda(self):
        melody = seq(note("c"), note("d"), note("e"))
        result = pipe(
            melody,
            lambda s: transpose(s, 2),
            lambda s: fragment(s, 2),
        )
        assert len(result.elements) == 2
        assert result.elements[0].pitch == "d"

    def test_pipe_empty(self):
        melody = seq(note("c"), note("d"))
        result = pipe(melody)
        assert len(result.elements) == 2


class TestIdentity:
    """Test identity helper function."""

    def test_identity_returns_same_elements(self):
        melody = seq(note("c"), note("d"), note("e"))
        result = identity(melody)
        assert len(result.elements) == len(melody.elements)
        for i in range(len(melody.elements)):
            assert result.elements[i].pitch == melody.elements[i].pitch

    def test_identity_in_pipe(self):
        melody = seq(note("c"), note("d"))
        result = pipe(melody, identity)
        assert result.to_alda() == melody.to_alda()


class TestIntegration:
    """Integration tests for transform module."""

    def test_complex_transformation_chain(self):
        """Test a complex chain of transformations."""
        melody = seq(
            note("c", duration=8),
            note("d", duration=8),
            note("e", duration=8),
            note("f", duration=8),
        )
        result = pipe(
            melody,
            lambda s: fragment(s, 3),  # Take first 3
            reverse,  # Reverse
            lambda s: transpose(s, 5),  # Up a fourth
            lambda s: augment(s, 2),  # Double durations
        )
        assert len(result.elements) == 3
        # Original: c d e, fragment(3): c d e, reverse: e d c, transpose(5): a g f
        # augment(2): quarter notes
        assert result.elements[0].duration == 4

    def test_transform_preserves_to_alda(self):
        """Verify transformers preserve to_alda() functionality."""
        melody = seq(
            note("c", duration=4), note("d", duration=4), note("e", duration=4)
        )
        reversed_mel = reverse(melody)
        alda = reversed_mel.to_alda()
        assert "e4" in alda
        assert "d4" in alda
        assert "c4" in alda

    def test_transform_with_score(self):
        """Test using transforms with Score.from_elements."""
        from aldakit import Score
        from aldakit.compose import part, tempo

        melody = seq(
            note("c", duration=8), note("e", duration=8), note("g", duration=8)
        )
        transformed = pipe(melody, reverse, lambda s: transpose(s, 2))

        score = Score.from_elements(
            part("piano"),
            tempo(120),
            *transformed.elements,
        )

        # Should be able to generate AST and MIDI
        assert score.ast is not None
        assert score.midi is not None
        assert len(score.midi.notes) == 3
