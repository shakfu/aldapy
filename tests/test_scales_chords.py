"""Tests for scales, chords, and advanced compose elements (cram, voices, variables, markers)."""

import pytest

from aldakit.compose import (
    # Scales
    scale,
    scale_notes,
    scale_degree,
    mode,
    relative_minor,
    relative_major,
    parallel_minor,
    parallel_major,
    transpose_scale,
    interval_name,
    list_scales,
    build_chord,
    major,
    minor,
    dim,
    aug,
    sus2,
    sus4,
    maj7,
    min7,
    dom7,
    dim7,
    half_dim7,
    aug7,
    dom9,
    maj9,
    min9,
    add9,
    power,
    arpeggiate,
    invert_chord,
    voicing,
    list_chord_types,
    Cram,
    Voice,
    Variable,
    VariableRef,
    Marker,
    AtMarker,
    # Core functions
    note,
    cram,
    voice,
    voice_group,
    var,
    var_ref,
    marker,
    at_marker,
    seq,
)


# =============================================================================
# Scale Tests
# =============================================================================


class TestScale:
    """Tests for the scale function."""

    def test_c_major_scale(self):
        """C major scale should return correct pitch names."""
        result = scale("c", "major")
        assert result == ["c", "d", "e", "f", "g", "a", "b"]

    def test_a_minor_scale(self):
        """A minor scale (natural minor / aeolian)."""
        result = scale("a", "minor")
        assert result == ["a", "b", "c", "d", "e", "f", "g"]

    def test_c_pentatonic_scale(self):
        """C major pentatonic scale."""
        result = scale("c", "pentatonic")
        assert result == ["c", "d", "e", "g", "a"]

    def test_a_blues_scale(self):
        """A blues scale."""
        result = scale("a", "blues")
        # a, c, d, d#/eb, e, g
        assert result == ["a", "c", "d", "d+", "e", "g"]

    def test_f_lydian_mode(self):
        """F lydian mode."""
        result = scale("f", "lydian")
        assert result == ["f", "g", "a", "b", "c", "d", "e"]

    def test_d_dorian_mode(self):
        """D dorian mode."""
        result = scale("d", "dorian")
        assert result == ["d", "e", "f", "g", "a", "b", "c"]

    def test_chromatic_scale(self):
        """Chromatic scale has 12 notes."""
        result = scale("c", "chromatic")
        assert len(result) == 12

    def test_unknown_scale_raises(self):
        """Unknown scale type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown scale type"):
            scale("c", "nonexistent")

    def test_invalid_root_raises(self):
        """Invalid root note should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid root note"):
            scale("x", "major")


class TestScaleNotes:
    """Tests for scale_notes function (returns Seq)."""

    def test_returns_seq(self):
        """scale_notes should return a Seq object."""
        result = scale_notes("c", "major")
        assert hasattr(result, "elements")
        assert len(result.elements) == 7

    def test_notes_have_correct_pitches(self):
        """Notes should have correct pitch names."""
        result = scale_notes("c", "major")
        pitches = [n.pitch for n in result.elements]
        assert pitches == ["c", "d", "e", "f", "g", "a", "b"]

    def test_with_duration(self):
        """Duration should be applied to all notes."""
        result = scale_notes("c", "major", duration=8)
        for n in result.elements:
            assert n.duration == 8

    def test_ascending_false(self):
        """Descending scale when ascending=False."""
        result = scale_notes("c", "major", ascending=False)
        pitches = [n.pitch for n in result.elements]
        assert pitches == ["b", "a", "g", "f", "e", "d", "c"]


class TestScaleDegree:
    """Tests for scale_degree function."""

    def test_first_degree_is_root(self):
        """Scale degree 1 should be the root."""
        pitch, acc, oct = scale_degree("c", "major", 1)
        assert pitch == "c"
        assert acc is None
        assert oct == 4

    def test_fifth_degree(self):
        """Scale degree 5 in C major is G."""
        pitch, acc, oct = scale_degree("c", "major", 5)
        assert pitch == "g"
        assert acc is None
        assert oct == 4

    def test_octave_wrapping(self):
        """Scale degree 8 should be root up an octave."""
        pitch, acc, oct = scale_degree("c", "major", 8)
        assert pitch == "c"
        assert oct == 5

    def test_degree_15_is_two_octaves(self):
        """Scale degree 15 should be root up two octaves."""
        pitch, acc, oct = scale_degree("c", "major", 15)
        assert pitch == "c"
        assert oct == 6

    def test_invalid_degree_raises(self):
        """Degree less than 1 should raise ValueError."""
        with pytest.raises(ValueError, match="Scale degree must be >= 1"):
            scale_degree("c", "major", 0)


class TestModeFunction:
    """Tests for mode function (alias for scale)."""

    def test_mode_is_alias_for_scale(self):
        """mode() should return same as scale()."""
        assert mode("d", "dorian") == scale("d", "dorian")


class TestRelativeMinorMajor:
    """Tests for relative minor/major functions."""

    def test_relative_minor_of_c(self):
        """Relative minor of C major is A minor."""
        assert relative_minor("c") == "a"

    def test_relative_minor_of_g(self):
        """Relative minor of G major is E minor."""
        assert relative_minor("g") == "e"

    def test_relative_major_of_a(self):
        """Relative major of A minor is C major."""
        assert relative_major("a") == "c"

    def test_relative_major_of_e(self):
        """Relative major of E minor is G major."""
        assert relative_major("e") == "g"

    def test_round_trip(self):
        """Relative major of relative minor should return original."""
        assert relative_major(relative_minor("c")) == "c"


class TestParallelMinorMajor:
    """Tests for parallel minor/major functions."""

    def test_parallel_minor_same_root(self):
        """Parallel minor has same root."""
        assert parallel_minor("c") == "c"

    def test_parallel_major_same_root(self):
        """Parallel major has same root."""
        assert parallel_major("a") == "a"


class TestTransposeScale:
    """Tests for transpose_scale function."""

    def test_transpose_up_fifth(self):
        """Transposing C D E up a fifth (7 semitones)."""
        result = transpose_scale(["c", "d", "e"], 7)
        assert result == ["g", "a", "b"]

    def test_transpose_up_fourth(self):
        """Transposing C D E up a fourth (5 semitones)."""
        result = transpose_scale(["c", "d", "e"], 5)
        assert result == ["f", "g", "a"]

    def test_transpose_with_accidentals(self):
        """Transposing notes with accidentals."""
        result = transpose_scale(["c+", "d+"], 2)
        assert result == ["d+", "f"]


class TestIntervalName:
    """Tests for interval_name function."""

    def test_unison(self):
        assert interval_name(0) == "unison"

    def test_perfect_fifth(self):
        assert interval_name(7) == "perfect fifth"

    def test_major_third(self):
        assert interval_name(4) == "major third"

    def test_octave(self):
        assert interval_name(12) == "octave"


class TestListScales:
    """Tests for list_scales function."""

    def test_returns_list(self):
        result = list_scales()
        assert isinstance(result, list)

    def test_contains_common_scales(self):
        result = list_scales()
        assert "major" in result
        assert "minor" in result
        assert "pentatonic" in result


# =============================================================================
# Chord Tests
# =============================================================================


class TestBuildChord:
    """Tests for build_chord function."""

    def test_c_major_chord(self):
        """C major chord should have C E G."""
        chord = build_chord("c", "major")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["c", "e", "g"]

    def test_a_minor_chord(self):
        """A minor chord should have A C E."""
        chord = build_chord("a", "minor")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["a", "c", "e"]

    def test_chord_with_duration(self):
        """Chord should accept duration parameter."""
        chord = build_chord("c", "major", duration=2)
        assert chord.duration == 2

    def test_chord_inversion(self):
        """First inversion moves root up an octave."""
        chord = build_chord("c", "major", inversion=1)
        # First inversion: E G C
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["e", "g", "c"]
        # Check octaves
        octaves = [n.octave for n in chord.notes]
        assert octaves[2] > octaves[0]  # C is higher than E

    def test_unknown_chord_raises(self):
        """Unknown chord type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown chord type"):
            build_chord("c", "nonexistent")


class TestTriadConstructors:
    """Tests for triad constructor functions."""

    def test_major_function(self):
        chord = major("c")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["c", "e", "g"]

    def test_minor_function(self):
        chord = minor("a")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["a", "c", "e"]

    def test_dim_function(self):
        chord = dim("b")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["b", "d", "f"]

    def test_aug_function(self):
        chord = aug("c")
        pitches = [n.pitch for n in chord.notes]
        accidentals = [n.accidental for n in chord.notes]
        assert pitches == ["c", "e", "g"]
        assert accidentals == [None, None, "+"]  # G# is stored as g with + accidental

    def test_sus2_function(self):
        chord = sus2("c")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["c", "d", "g"]

    def test_sus4_function(self):
        chord = sus4("c")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["c", "f", "g"]


class TestSeventhChords:
    """Tests for seventh chord constructors."""

    def test_maj7(self):
        chord = maj7("c")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["c", "e", "g", "b"]

    def test_min7(self):
        chord = min7("a")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["a", "c", "e", "g"]

    def test_dom7(self):
        chord = dom7("g")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["g", "b", "d", "f"]

    def test_dim7(self):
        chord = dim7("b")
        # B D F Ab (Ab is g+ in our notation)
        assert len(chord.notes) == 4

    def test_half_dim7(self):
        chord = half_dim7("b")
        assert len(chord.notes) == 4

    def test_aug7(self):
        chord = aug7("c")
        assert len(chord.notes) == 4


class TestExtendedChords:
    """Tests for extended chord constructors."""

    def test_dom9(self):
        chord = dom9("g")
        assert len(chord.notes) == 5

    def test_maj9(self):
        chord = maj9("c")
        assert len(chord.notes) == 5

    def test_min9(self):
        chord = min9("a")
        assert len(chord.notes) == 5

    def test_add9(self):
        chord = add9("c")
        # Major triad plus 9th (no 7th)
        assert len(chord.notes) == 4

    def test_power(self):
        chord = power("e")
        pitches = [n.pitch for n in chord.notes]
        assert pitches == ["e", "b"]


class TestArpeggiate:
    """Tests for arpeggiate function."""

    def test_default_pattern(self):
        """Default pattern plays notes in order."""
        chord = major("c")
        arp = arpeggiate(chord)
        pitches = [n.pitch for n in arp]
        assert pitches == ["c", "e", "g"]

    def test_custom_pattern(self):
        """Custom pattern plays notes in specified order."""
        chord = major("c")
        arp = arpeggiate(chord, [0, 1, 2, 1])
        pitches = [n.pitch for n in arp]
        assert pitches == ["c", "e", "g", "e"]

    def test_with_duration(self):
        """Duration applied to all notes."""
        chord = major("c")
        arp = arpeggiate(chord, duration=16)
        for n in arp:
            assert n.duration == 16


class TestInvertChord:
    """Tests for invert_chord function."""

    def test_first_inversion(self):
        """First inversion moves root up."""
        chord = major("c")
        inverted = invert_chord(chord, 1)
        # Should have E G C (with C an octave higher)
        pitches = [n.pitch for n in inverted.notes]
        assert pitches == ["e", "g", "c"]

    def test_zero_inversion_returns_same(self):
        """Inversion 0 returns original chord."""
        chord = major("c")
        inverted = invert_chord(chord, 0)
        assert inverted == chord


class TestVoicing:
    """Tests for voicing function."""

    def test_spread_voicing(self):
        """Spread voicing puts notes in different octaves."""
        chord = major("c")
        voiced = voicing(chord, [3, 4, 5])
        octaves = [n.octave for n in voiced.notes]
        assert octaves == [3, 4, 5]

    def test_wrong_length_raises(self):
        """Wrong number of octaves should raise ValueError."""
        chord = major("c")
        with pytest.raises(ValueError):
            voicing(chord, [3, 4])  # Only 2 octaves for 3 notes


class TestListChordTypes:
    """Tests for list_chord_types function."""

    def test_returns_list(self):
        result = list_chord_types()
        assert isinstance(result, list)

    def test_contains_common_types(self):
        result = list_chord_types()
        assert "major" in result
        assert "minor" in result
        assert "dominant7" in result


# =============================================================================
# Cram Tests
# =============================================================================


class TestCram:
    """Tests for Cram class (tuplets)."""

    def test_cram_creation(self):
        """Basic Cram creation."""
        c = cram(note("c"), note("d"), note("e"), duration=4)
        assert len(c.elements) == 3
        assert c.duration == 4

    def test_cram_to_alda(self):
        """Cram should generate Alda syntax."""
        c = cram(note("c"), note("d"), note("e"), duration=4)
        result = c.to_alda()
        assert "{" in result
        assert "}" in result
        assert "4" in result

    def test_cram_class_directly(self):
        """Using Cram class directly."""
        c = Cram(elements=[note("c"), note("d")], duration=8)
        assert c.duration == 8

    def test_cram_to_ast(self):
        """Cram should produce valid AST node."""
        c = cram(note("c"), note("d"), duration=4)
        ast = c.to_ast()
        assert ast is not None


# =============================================================================
# Voice Tests
# =============================================================================


class TestVoice:
    """Tests for Voice class."""

    def test_voice_creation(self):
        """Basic Voice creation."""
        v = voice(1, note("c"), note("d"))
        assert v.number == 1
        assert len(v.elements) == 2

    def test_voice_to_alda(self):
        """Voice should generate Alda syntax."""
        v = voice(1, note("c"))
        result = v.to_alda()
        assert "V1:" in result

    def test_voice_zero_ends_voice(self):
        """Voice 0 ends the voice section."""
        v = voice(0)
        result = v.to_alda()
        assert "V0:" in result

    def test_voice_class_directly(self):
        """Using Voice class directly."""
        v = Voice(number=2, elements=[note("e"), note("f")])
        assert v.number == 2


class TestVoiceGroup:
    """Tests for VoiceGroup class."""

    def test_voice_group_creation(self):
        """VoiceGroup with multiple voices."""
        v1 = voice(1, note("c"))
        v2 = voice(2, note("e"))
        vg = voice_group(v1, v2)
        assert len(vg.voices) == 2

    def test_voice_group_to_alda(self):
        """VoiceGroup should generate Alda syntax."""
        v1 = voice(1, note("c"))
        v2 = voice(2, note("e"))
        vg = voice_group(v1, v2)
        result = vg.to_alda()
        assert "V1:" in result
        assert "V2:" in result


# =============================================================================
# Variable Tests
# =============================================================================


class TestVariable:
    """Tests for Variable class."""

    def test_variable_creation(self):
        """Basic Variable creation."""
        v = var("riff", note("c"), note("d"), note("e"))
        assert v.name == "riff"
        assert len(v.elements) == 3

    def test_variable_to_alda(self):
        """Variable should generate Alda syntax."""
        v = var("melody", note("c"))
        result = v.to_alda()
        assert "melody" in result
        assert "=" in result

    def test_variable_class_directly(self):
        """Using Variable class directly."""
        v = Variable(name="theme", elements=[note("g")])
        assert v.name == "theme"


class TestVariableRef:
    """Tests for VariableRef class."""

    def test_variable_ref_creation(self):
        """Basic VariableRef creation."""
        ref = var_ref("riff")
        assert ref.name == "riff"

    def test_variable_ref_to_alda(self):
        """VariableRef should generate Alda syntax."""
        ref = var_ref("melody")
        result = ref.to_alda()
        assert "melody" in result

    def test_variable_ref_class_directly(self):
        """Using VariableRef class directly."""
        ref = VariableRef(name="theme")
        assert ref.name == "theme"


# =============================================================================
# Marker Tests
# =============================================================================


class TestMarker:
    """Tests for Marker class."""

    def test_marker_creation(self):
        """Basic Marker creation."""
        m = marker("chorus")
        assert m.name == "chorus"

    def test_marker_to_alda(self):
        """Marker should generate Alda syntax."""
        m = marker("verse")
        result = m.to_alda()
        assert "%" in result
        assert "verse" in result

    def test_marker_class_directly(self):
        """Using Marker class directly."""
        m = Marker(name="bridge")
        assert m.name == "bridge"


class TestAtMarker:
    """Tests for AtMarker class."""

    def test_at_marker_creation(self):
        """Basic AtMarker creation."""
        am = at_marker("chorus")
        assert am.name == "chorus"

    def test_at_marker_to_alda(self):
        """AtMarker should generate Alda syntax."""
        am = at_marker("verse")
        result = am.to_alda()
        assert "@" in result
        assert "verse" in result

    def test_at_marker_class_directly(self):
        """Using AtMarker class directly."""
        am = AtMarker(name="bridge")
        assert am.name == "bridge"


# =============================================================================
# Integration Tests
# =============================================================================


class TestScaleChordIntegration:
    """Integration tests for scales and chords."""

    def test_scale_to_chord_progression(self):
        """Use scale to build chord progression."""
        pitches = scale("c", "major")
        # I-IV-V-I progression
        chords = [
            major(pitches[0]),  # C
            major(pitches[3]),  # F
            major(pitches[4]),  # G
            major(pitches[0]),  # C
        ]
        assert len(chords) == 4

    def test_arpeggiated_sequence(self):
        """Arpeggiate chords into a sequence."""
        chord = maj7("c")
        arp = arpeggiate(chord, [0, 1, 2, 3, 2, 1], duration=16)
        s = seq(*arp)
        assert len(s.elements) == 6

    def test_voice_with_scale(self):
        """Create voices from scales."""
        melody = voice(1, *scale_notes("c", "major", duration=4).elements)
        bass = voice(2, *scale_notes("c", "major", octave=3, duration=2).elements)
        vg = voice_group(melody, bass)
        assert len(vg.voices) == 2

    def test_variable_with_chord_sequence(self):
        """Store chord sequence in variable."""
        progression = var(
            "progression",
            major("c", duration=2),
            minor("a", duration=2),
            major("f", duration=2),
            major("g", duration=2),
        )
        assert progression.name == "progression"
        assert len(progression.elements) == 4
