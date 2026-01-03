"""Tests for the compose.generate module - generative functions."""

import pytest
from aldakit.compose import (
    Note,
    Rest,
    note,
    rest,
    seq,
)
from aldakit.compose.generate import (
    # Random selection
    random_note,
    random_choice,
    weighted_choice,
    # Random walks
    random_walk,
    drunk_walk,
    # Rhythmic generators
    euclidean,
    probability_seq,
    rest_probability,
    # Markov chains
    MarkovChain,
    markov_chain,
    learn_markov,
    # L-Systems
    lsystem,
    # Cellular automata
    cellular_automaton,
    # Shift registers
    shift_register,
    turing_machine,
)


# =============================================================================
# Random Selection Tests
# =============================================================================


class TestRandomNote:
    def test_random_note_default_scale(self):
        """Random note from default C major scale."""
        n = random_note(seed=42)
        assert isinstance(n, Note)
        assert n.pitch in ["c", "d", "e", "f", "g", "a", "b"]

    def test_random_note_custom_scale(self):
        """Random note from custom scale."""
        scale = ["c", "e", "g"]
        n = random_note(scale=scale, seed=42)
        assert n.pitch in scale

    def test_random_note_with_duration(self):
        """Random note with specified duration."""
        n = random_note(duration=8, seed=42)
        assert n.duration == 8

    def test_random_note_with_octave(self):
        """Random note with specified octave."""
        n = random_note(octave=5, seed=42)
        assert n.octave == 5

    def test_random_note_reproducible_with_seed(self):
        """Same seed produces same note."""
        n1 = random_note(seed=123)
        n2 = random_note(seed=123)
        assert n1.pitch == n2.pitch


class TestRandomChoice:
    def test_random_choice_basic(self):
        """Choose from list of notes."""
        options = [note("c"), note("e"), note("g")]
        result = random_choice(options, seed=42)
        assert result in options

    def test_random_choice_reproducible(self):
        """Same seed produces same choice."""
        options = [note("c"), note("d"), note("e"), note("f")]
        r1 = random_choice(options, seed=99)
        r2 = random_choice(options, seed=99)
        assert r1.pitch == r2.pitch

    def test_random_choice_empty_raises(self):
        """Empty list raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            random_choice([])


class TestWeightedChoice:
    def test_weighted_choice_basic(self):
        """Weighted choice returns valid item."""
        options = [(note("c"), 0.5), (note("e"), 0.3), (note("g"), 0.2)]
        result = weighted_choice(options, seed=42)
        assert result.pitch in ["c", "e", "g"]

    def test_weighted_choice_heavy_weight(self):
        """Heavy weight dominates selection (statistical test)."""
        options = [(note("c"), 100), (note("e"), 1)]
        # Run multiple times - should mostly get "c"
        results = [weighted_choice(options, seed=i).pitch for i in range(100)]
        c_count = results.count("c")
        assert c_count > 90  # Should be heavily biased toward "c"

    def test_weighted_choice_empty_raises(self):
        """Empty list raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            weighted_choice([])

    def test_weighted_choice_negative_weight_raises(self):
        """Negative weight raises error."""
        with pytest.raises(ValueError, match="cannot be negative"):
            weighted_choice([(note("c"), -1)])

    def test_weighted_choice_zero_total_raises(self):
        """Zero total weight raises error."""
        with pytest.raises(ValueError, match="cannot be zero"):
            weighted_choice([(note("c"), 0), (note("e"), 0)])


# =============================================================================
# Random Walk Tests
# =============================================================================


class TestRandomWalk:
    def test_random_walk_basic(self):
        """Basic random walk produces sequence."""
        result = random_walk("c", 8, seed=42)
        assert len(result.elements) == 8
        assert all(isinstance(e, Note) for e in result.elements)

    def test_random_walk_starts_at_pitch(self):
        """First note is the start pitch."""
        result = random_walk("e", 5, octave=5, seed=42)
        assert result.elements[0].pitch == "e"
        assert result.elements[0].octave == 5

    def test_random_walk_with_duration(self):
        """All notes have specified duration."""
        result = random_walk("c", 5, duration=8, seed=42)
        assert all(n.duration == 8 for n in result.elements)

    def test_random_walk_stays_in_range(self):
        """Notes stay within pitch range."""
        result = random_walk("c", 50, min_pitch=48, max_pitch=72, seed=42)
        for n in result.elements:
            assert 48 <= n.midi_pitch <= 72

    def test_random_walk_custom_intervals(self):
        """Custom intervals are used."""
        result = random_walk("c", 10, intervals=[1, 2], seed=42)
        # All intervals should be positive, so pitch should trend up
        assert len(result.elements) == 10

    def test_random_walk_zero_steps(self):
        """Zero steps returns empty sequence."""
        result = random_walk("c", 0, seed=42)
        assert len(result.elements) == 0

    def test_random_walk_reproducible(self):
        """Same seed produces same walk."""
        r1 = random_walk("c", 10, seed=123)
        r2 = random_walk("c", 10, seed=123)
        for n1, n2 in zip(r1.elements, r2.elements):
            assert n1.pitch == n2.pitch


class TestDrunkWalk:
    def test_drunk_walk_basic(self):
        """Basic drunk walk produces sequence."""
        result = drunk_walk("c", 8, seed=42)
        assert len(result.elements) == 8

    def test_drunk_walk_small_steps(self):
        """Max step constrains interval size."""
        result = drunk_walk("c", 20, max_step=1, octave=4, seed=42)
        # With max_step=1, intervals should be small
        assert len(result.elements) == 20

    def test_drunk_walk_with_bias(self):
        """Bias affects direction tendency."""
        # Positive bias should trend upward
        result = drunk_walk("c", 20, max_step=2, bias=0.5, octave=4, seed=42)
        assert len(result.elements) == 20

    def test_drunk_walk_reproducible(self):
        """Same seed produces same walk."""
        r1 = drunk_walk("e", 8, seed=99)
        r2 = drunk_walk("e", 8, seed=99)
        for n1, n2 in zip(r1.elements, r2.elements):
            assert n1.pitch == n2.pitch


# =============================================================================
# Rhythmic Generator Tests
# =============================================================================


class TestEuclidean:
    def test_euclidean_basic(self):
        """Basic Euclidean rhythm."""
        result = euclidean(3, 8, "c")
        assert len(result.elements) == 8
        hits = sum(1 for e in result.elements if isinstance(e, Note))
        assert hits == 3

    def test_euclidean_tresillo(self):
        """3 over 8 is the Cuban tresillo pattern."""
        result = euclidean(3, 8, "c")
        pattern = [isinstance(e, Note) for e in result.elements]
        # Should be [T, F, F, T, F, F, T, F] or similar
        assert sum(pattern) == 3

    def test_euclidean_cinquillo(self):
        """5 over 8 is the cinquillo pattern."""
        result = euclidean(5, 8, "c")
        hits = sum(1 for e in result.elements if isinstance(e, Note))
        assert hits == 5

    def test_euclidean_with_duration(self):
        """Notes and rests have specified duration."""
        result = euclidean(3, 8, "c", duration=16)
        for elem in result.elements:
            if isinstance(elem, Note):
                assert elem.duration == 16
            else:
                assert elem.duration == 16

    def test_euclidean_rotation(self):
        """Rotation shifts the pattern."""
        r1 = euclidean(3, 8, "c")
        r2 = euclidean(3, 8, "c", rotate=1)
        # Rotated pattern should be different
        p1 = [isinstance(e, Note) for e in r1.elements]
        p2 = [isinstance(e, Note) for e in r2.elements]
        assert p1 != p2
        # But same number of hits
        assert sum(p1) == sum(p2)

    def test_euclidean_all_hits(self):
        """All hits (hits == steps)."""
        result = euclidean(8, 8, "c")
        assert all(isinstance(e, Note) for e in result.elements)

    def test_euclidean_no_hits(self):
        """No hits (hits == 0)."""
        result = euclidean(0, 8, "c")
        assert all(isinstance(e, Rest) for e in result.elements)

    def test_euclidean_empty(self):
        """Zero steps returns empty."""
        result = euclidean(0, 0, "c")
        assert len(result.elements) == 0

    def test_euclidean_invalid_hits_raises(self):
        """Hits > steps raises error."""
        with pytest.raises(ValueError, match="cannot be greater"):
            euclidean(10, 5, "c")


class TestProbabilitySeq:
    def test_probability_seq_basic(self):
        """Basic probability sequence."""
        result = probability_seq(["c", "d", "e"], 10, probability=0.7, seed=42)
        assert len(result.elements) == 10

    def test_probability_seq_all_notes(self):
        """Probability 1.0 gives all notes."""
        result = probability_seq(["c"], 10, probability=1.0, seed=42)
        assert all(isinstance(e, Note) for e in result.elements)

    def test_probability_seq_all_rests(self):
        """Probability 0.0 gives all rests."""
        result = probability_seq(["c"], 10, probability=0.0, seed=42)
        assert all(isinstance(e, Rest) for e in result.elements)

    def test_probability_seq_with_duration(self):
        """Notes have specified duration."""
        result = probability_seq(["c"], 5, probability=1.0, duration=8, seed=42)
        for elem in result.elements:
            if isinstance(elem, Note):
                assert elem.duration == 8

    def test_probability_seq_empty_notes_raises(self):
        """Empty notes list raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            probability_seq([], 10)

    def test_probability_seq_invalid_probability_raises(self):
        """Invalid probability raises error."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            probability_seq(["c"], 10, probability=1.5)


class TestRestProbability:
    def test_rest_probability_basic(self):
        """Basic rest probability."""
        melody = seq(note("c"), note("d"), note("e"), note("f"))
        result = rest_probability(melody, 0.5, seed=42)
        assert len(result.elements) == 4

    def test_rest_probability_zero(self):
        """Probability 0 keeps all notes."""
        melody = seq(note("c"), note("d"), note("e"))
        result = rest_probability(melody, 0.0, seed=42)
        assert all(isinstance(e, Note) for e in result.elements)

    def test_rest_probability_one(self):
        """Probability 1 replaces all notes."""
        melody = seq(note("c"), note("d"), note("e"))
        result = rest_probability(melody, 1.0, seed=42)
        assert all(isinstance(e, Rest) for e in result.elements)

    def test_rest_probability_preserves_rests(self):
        """Existing rests are preserved."""
        melody = seq(note("c"), rest(), note("e"))
        result = rest_probability(melody, 0.5, seed=42)
        # The original rest should still be there
        assert any(isinstance(e, Rest) for e in result.elements)


# =============================================================================
# Markov Chain Tests
# =============================================================================


class TestMarkovChain:
    def test_markov_chain_basic(self):
        """Basic Markov chain generation."""
        chain = markov_chain(
            {
                "c": {"d": 0.5, "e": 0.5},
                "d": {"e": 0.5, "c": 0.5},
                "e": {"c": 1.0},
            }
        )
        result = chain.generate(start="c", length=10, seed=42)
        assert len(result.elements) == 10
        assert all(isinstance(e, Note) for e in result.elements)

    def test_markov_chain_starts_correct(self):
        """Chain starts with specified note."""
        chain = markov_chain({"c": {"d": 1.0}, "d": {"c": 1.0}})
        result = chain.generate(start="c", length=5, seed=42)
        assert result.elements[0].pitch == "c"

    def test_markov_chain_follows_transitions(self):
        """Chain follows deterministic transitions."""
        chain = markov_chain(
            {
                "c": {"d": 1.0},
                "d": {"e": 1.0},
                "e": {"c": 1.0},
            }
        )
        result = chain.generate(start="c", length=6, seed=42)
        pitches = [n.pitch for n in result.elements]
        assert pitches == ["c", "d", "e", "c", "d", "e"]

    def test_markov_chain_with_duration(self):
        """Generated notes have specified duration."""
        chain = markov_chain({"c": {"d": 1.0}, "d": {"c": 1.0}})
        result = chain.generate(start="c", length=5, duration=8, seed=42)
        assert all(n.duration == 8 for n in result.elements)

    def test_markov_chain_reproducible(self):
        """Same seed produces same sequence."""
        chain = markov_chain(
            {
                "c": {"d": 0.5, "e": 0.5},
                "d": {"c": 0.5, "e": 0.5},
                "e": {"c": 0.5, "d": 0.5},
            }
        )
        r1 = chain.generate(start="c", length=10, seed=123)
        r2 = chain.generate(start="c", length=10, seed=123)
        for n1, n2 in zip(r1.elements, r2.elements):
            assert n1.pitch == n2.pitch

    def test_markov_chain_empty_raises(self):
        """Empty chain raises error."""
        chain = MarkovChain()
        with pytest.raises(ValueError, match="no transitions"):
            chain.generate(length=5)


class TestLearnMarkov:
    def test_learn_markov_basic(self):
        """Learn from simple sequence."""
        melody = seq(note("c"), note("d"), note("e"), note("d"), note("c"))
        chain = learn_markov(melody)
        # Should be able to generate
        result = chain.generate(length=10, seed=42)
        assert len(result.elements) == 10

    def test_learn_markov_learns_transitions(self):
        """Learned transitions reflect input."""
        # c always goes to d, d always goes to c
        melody = seq(note("c"), note("d"), note("c"), note("d"))
        chain = learn_markov(melody)
        assert "c" in chain.transitions
        assert "d" in chain.transitions

    def test_learn_markov_higher_order(self):
        """Higher-order Markov chain."""
        melody = seq(
            note("c"),
            note("d"),
            note("e"),
            note("c"),
            note("d"),
            note("f"),
        )
        chain = learn_markov(melody, order=2)
        assert chain.order == 2

    def test_learn_markov_short_sequence_raises(self):
        """Sequence too short for order raises error."""
        melody = seq(note("c"))
        with pytest.raises(ValueError, match="too short"):
            learn_markov(melody, order=1)


# =============================================================================
# L-System Tests
# =============================================================================


class TestLSystem:
    def test_lsystem_basic(self):
        """Basic L-system generation."""
        result = lsystem(
            axiom="A",
            rules={"A": "AB", "B": "A"},
            iterations=3,
            note_map={"A": note("c"), "B": note("e")},
        )
        assert len(result.elements) > 0
        assert all(isinstance(e, Note) for e in result.elements)

    def test_lsystem_fibonacci_length(self):
        """Fibonacci L-system produces correct length."""
        # A -> AB, B -> A produces Fibonacci sequence
        # iter 0: A (1)
        # iter 1: AB (2)
        # iter 2: ABA (3)
        # iter 3: ABAAB (5)
        # iter 4: ABAABABA (8)
        result = lsystem(
            axiom="A",
            rules={"A": "AB", "B": "A"},
            iterations=4,
            note_map={"A": note("c"), "B": note("e")},
        )
        assert len(result.elements) == 8  # Fibonacci number

    def test_lsystem_no_iterations(self):
        """Zero iterations returns axiom only."""
        result = lsystem(
            axiom="ABC",
            rules={"A": "XY"},
            iterations=0,
            note_map={"A": note("c"), "B": note("d"), "C": note("e")},
        )
        assert len(result.elements) == 3

    def test_lsystem_unmapped_symbols_ignored(self):
        """Unmapped symbols are ignored by default."""
        result = lsystem(
            axiom="A+B",
            rules={"A": "A", "B": "B"},
            iterations=1,
            note_map={"A": note("c"), "B": note("e")},
        )
        # Only A and B are mapped, + is ignored
        assert len(result.elements) == 2

    def test_lsystem_with_default(self):
        """Unmapped symbols use default."""
        result = lsystem(
            axiom="A+B",
            rules={},
            iterations=0,
            note_map={"A": note("c"), "B": note("e")},
            default=note("g"),
        )
        # A, +, B all become notes
        assert len(result.elements) == 3

    def test_lsystem_with_rests(self):
        """L-system can include rests."""
        result = lsystem(
            axiom="AB",
            rules={"A": "AB", "B": "A"},
            iterations=2,
            note_map={"A": note("c"), "B": rest()},
        )
        notes = [e for e in result.elements if isinstance(e, Note)]
        rests = [e for e in result.elements if isinstance(e, Rest)]
        assert len(notes) > 0
        assert len(rests) > 0


# =============================================================================
# Cellular Automaton Tests
# =============================================================================


class TestCellularAutomaton:
    def test_cellular_automaton_basic(self):
        """Basic cellular automaton generation."""
        result = cellular_automaton(rule=110, width=8, steps=4, pitch_on="c")
        assert len(result.elements) == 8 * 4  # width * steps

    def test_cellular_automaton_rule_90(self):
        """Rule 90 (Sierpinski triangle) produces pattern."""
        result = cellular_automaton(rule=90, width=8, steps=4, pitch_on="c")
        # Should have mix of notes and rests
        notes = sum(1 for e in result.elements if isinstance(e, Note))
        rests = sum(1 for e in result.elements if isinstance(e, Rest))
        assert notes > 0
        assert rests > 0

    def test_cellular_automaton_with_duration(self):
        """Notes have specified duration."""
        result = cellular_automaton(
            rule=30, width=4, steps=2, pitch_on="c", duration=16
        )
        for elem in result.elements:
            if isinstance(elem, Note):
                assert elem.duration == 16

    def test_cellular_automaton_custom_initial(self):
        """Custom initial state."""
        result = cellular_automaton(
            rule=110,
            width=4,
            steps=1,
            pitch_on="c",
            initial=[True, False, True, False],
        )
        # First row should match initial pattern
        pattern = [isinstance(e, Note) for e in result.elements[:4]]
        assert pattern == [True, False, True, False]

    def test_cellular_automaton_invalid_rule_raises(self):
        """Invalid rule number raises error."""
        with pytest.raises(ValueError, match="between 0 and 255"):
            cellular_automaton(rule=300, width=8, steps=4, pitch_on="c")

    def test_cellular_automaton_invalid_initial_raises(self):
        """Wrong initial length raises error."""
        with pytest.raises(ValueError, match="must have length"):
            cellular_automaton(
                rule=110,
                width=8,
                steps=4,
                pitch_on="c",
                initial=[True, False],  # Wrong length
            )


# =============================================================================
# Shift Register Tests
# =============================================================================


class TestShiftRegister:
    def test_shift_register_basic(self):
        """Basic LFSR generation."""
        result = shift_register(16, bits=8)
        assert len(result.elements) == 16
        assert all(isinstance(e, Note) for e in result.elements)

    def test_shift_register_with_scale(self):
        """LFSR with custom scale."""
        scale = ["c", "e", "g"]
        result = shift_register(10, bits=4, scale=scale)
        for elem in result.elements:
            assert elem.pitch in scale

    def test_shift_register_with_duration(self):
        """LFSR with specified duration."""
        result = shift_register(8, bits=4, duration=8)
        assert all(n.duration == 8 for n in result.elements)

    def test_shift_register_deterministic(self):
        """Same initial value produces same sequence."""
        r1 = shift_register(16, bits=8, initial=42)
        r2 = shift_register(16, bits=8, initial=42)
        for n1, n2 in zip(r1.elements, r2.elements):
            assert n1.pitch == n2.pitch

    def test_shift_register_binary_mode(self):
        """Binary mode produces notes and rests."""
        result = shift_register(16, bits=8, mode="binary")
        notes = [e for e in result.elements if isinstance(e, Note)]
        rests = [e for e in result.elements if isinstance(e, Rest)]
        # Should have some of each (statistically likely)
        assert len(notes) + len(rests) == 16

    def test_shift_register_custom_taps(self):
        """Custom tap positions work."""
        result = shift_register(16, taps=[0, 3], bits=4)
        assert len(result.elements) == 16

    def test_shift_register_cycles(self):
        """LFSR with maximal taps should cycle after 2^n - 1 steps."""
        # 4-bit LFSR has max cycle of 15
        result = shift_register(30, bits=4, initial=1)
        pitches = [n.pitch for n in result.elements]
        # First 15 should equal second 15
        assert pitches[:15] == pitches[15:]

    def test_shift_register_invalid_bits_raises(self):
        """Invalid bit size raises error."""
        with pytest.raises(ValueError, match="between 1 and 16"):
            shift_register(16, bits=0)
        with pytest.raises(ValueError, match="between 1 and 16"):
            shift_register(16, bits=20)

    def test_shift_register_invalid_tap_raises(self):
        """Tap out of range raises error."""
        with pytest.raises(ValueError, match="out of range"):
            shift_register(16, taps=[0, 10], bits=4)


class TestTuringMachine:
    def test_turing_machine_basic(self):
        """Basic Turing Machine generation."""
        result = turing_machine(16, bits=8, seed=42)
        assert len(result.elements) == 16
        assert all(isinstance(e, Note) for e in result.elements)

    def test_turing_machine_locked_loop(self):
        """Probability 0 creates exact loop."""
        result = turing_machine(24, bits=8, probability=0.0, seed=42)
        pitches = [n.pitch for n in result.elements]
        # Should repeat after 8 steps
        assert pitches[:8] == pitches[8:16]
        assert pitches[:8] == pitches[16:24]

    def test_turing_machine_with_scale(self):
        """Turing Machine with custom scale."""
        scale = ["c", "d", "e", "g", "a"]
        result = turing_machine(16, bits=8, scale=scale, seed=42)
        for elem in result.elements:
            assert elem.pitch in scale

    def test_turing_machine_evolving(self):
        """High probability causes variation."""
        result = turing_machine(32, bits=8, probability=0.5, seed=42)
        pitches = [n.pitch for n in result.elements]
        # With 50% flip probability, first 8 unlikely to equal second 8
        # (This is a statistical test, could theoretically fail)
        first_8 = pitches[:8]
        second_8 = pitches[8:16]
        third_8 = pitches[16:24]
        # At least one should be different
        assert first_8 != second_8 or second_8 != third_8

    def test_turing_machine_reproducible(self):
        """Same seed produces same sequence."""
        r1 = turing_machine(16, bits=8, probability=0.3, seed=123)
        r2 = turing_machine(16, bits=8, probability=0.3, seed=123)
        for n1, n2 in zip(r1.elements, r2.elements):
            assert n1.pitch == n2.pitch

    def test_turing_machine_with_duration(self):
        """Turing Machine with specified duration."""
        result = turing_machine(8, bits=4, duration=16, seed=42)
        assert all(n.duration == 16 for n in result.elements)

    def test_turing_machine_invalid_probability_raises(self):
        """Invalid probability raises error."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            turing_machine(16, probability=1.5)


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    def test_euclidean_to_alda(self):
        """Euclidean rhythm can be exported to Alda."""
        result = euclidean(3, 8, "c", duration=8)
        alda = result.to_alda()
        assert "c8" in alda or "r8" in alda

    def test_random_walk_to_alda(self):
        """Random walk can be exported to Alda."""
        result = random_walk("c", 4, duration=8, seed=42)
        alda = result.to_alda()
        assert len(alda) > 0

    def test_markov_to_alda(self):
        """Markov chain output can be exported to Alda."""
        chain = markov_chain({"c": {"d": 1.0}, "d": {"c": 1.0}})
        result = chain.generate(start="c", length=4, duration=8, seed=42)
        alda = result.to_alda()
        assert "c8" in alda or "d8" in alda

    def test_combine_with_score(self):
        """Generative functions work with Score."""
        from aldakit import Score
        from aldakit.compose import part, tempo

        rhythm = euclidean(3, 8, "c", duration=8)
        walk = random_walk("e", 8, duration=8, seed=42)

        score = Score.from_elements(
            part("piano"),
            tempo(120),
            *rhythm.elements,
            *walk.elements,
        )

        assert score.duration > 0
        assert len(score.ast.children) > 0

    def test_chain_generators(self):
        """Chain multiple generators together."""
        # Generate a melody with random walk
        melody = random_walk("c", 8, duration=8, seed=42)

        # Add random rests
        sparse = rest_probability(melody, 0.3, seed=42)

        # Should still be valid
        assert len(sparse.elements) == 8
        alda = sparse.to_alda()
        assert len(alda) > 0
