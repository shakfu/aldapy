"""Generative functions for algorithmic music composition.

This module provides tools for creating musical material algorithmically,
useful for composition, experimentation, and live coding.

Categories:
- Random selection: random_note, random_choice, weighted_choice
- Random walks: random_walk, drunk_walk
- Rhythmic generators: euclidean, probability_seq, rest_probability
- Pattern-based: markov_chain, learn_markov, lsystem, cellular_automaton
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import TYPE_CHECKING, TypeVar

from .base import ComposeElement
from .core import Note, Rest, Seq, note, rest, seq

if TYPE_CHECKING:
    pass

T = TypeVar("T")


# =============================================================================
# Random Selection
# =============================================================================


def random_note(
    scale: list[str] | None = None,
    *,
    duration: int | None = None,
    octave: int | None = None,
    seed: int | None = None,
) -> Note:
    """Generate a random note from a scale.

    Args:
        scale: List of pitch names to choose from. Defaults to C major scale.
        duration: Optional duration for the note.
        octave: Optional octave for the note.
        seed: Optional random seed for reproducibility.

    Returns:
        A randomly selected Note.

    Examples:
        >>> random_note(scale=["c", "d", "e", "g", "a"], seed=42)  # Pentatonic
        >>> random_note(duration=8, octave=5)
    """
    if scale is None:
        scale = ["c", "d", "e", "f", "g", "a", "b"]

    rng = random.Random(seed)
    pitch = rng.choice(scale)
    return note(pitch, duration=duration, octave=octave)


def random_choice(
    options: list[T],
    *,
    seed: int | None = None,
) -> T:
    """Randomly select one item from a list of options.

    Args:
        options: List of items to choose from (notes, chords, sequences, etc.).
        seed: Optional random seed for reproducibility.

    Returns:
        A randomly selected item.

    Examples:
        >>> random_choice([note("c"), note("e"), note("g")])
        >>> random_choice([chord("c", "e", "g"), chord("f", "a", "c")])
    """
    if not options:
        raise ValueError("options list cannot be empty")

    rng = random.Random(seed)
    return rng.choice(options)


def weighted_choice(
    weighted_options: list[tuple[T, float]],
    *,
    seed: int | None = None,
) -> T:
    """Randomly select an item based on probability weights.

    Args:
        weighted_options: List of (item, weight) tuples. Weights don't need
            to sum to 1.0; they will be normalized.
        seed: Optional random seed for reproducibility.

    Returns:
        A randomly selected item based on weights.

    Examples:
        >>> weighted_choice([
        ...     (note("c"), 0.5),  # 50% chance
        ...     (note("e"), 0.3),  # 30% chance
        ...     (note("g"), 0.2),  # 20% chance
        ... ])
    """
    if not weighted_options:
        raise ValueError("weighted_options list cannot be empty")

    items = [item for item, _ in weighted_options]
    weights = [weight for _, weight in weighted_options]

    if any(w < 0 for w in weights):
        raise ValueError("weights cannot be negative")

    total = sum(weights)
    if total == 0:
        raise ValueError("total weight cannot be zero")

    rng = random.Random(seed)
    return rng.choices(items, weights=weights, k=1)[0]


# =============================================================================
# Random Walks
# =============================================================================


def random_walk(
    start: str,
    steps: int,
    *,
    intervals: list[int] | None = None,
    duration: int | None = None,
    octave: int = 4,
    min_pitch: int = 36,
    max_pitch: int = 84,
    seed: int | None = None,
) -> Seq:
    """Generate a melody using a random walk through pitch space.

    Each step moves by a randomly chosen interval from the previous note.

    Args:
        start: Starting pitch name (e.g., "c").
        steps: Number of notes to generate.
        intervals: List of allowed intervals in semitones. Defaults to [-2, -1, 1, 2].
        duration: Duration for all notes.
        octave: Starting octave.
        min_pitch: Minimum MIDI pitch (to constrain range).
        max_pitch: Maximum MIDI pitch (to constrain range).
        seed: Optional random seed for reproducibility.

    Returns:
        A Seq containing the random walk melody.

    Examples:
        >>> random_walk("c", 16, intervals=[-2, -1, 1, 2], duration=8)
        >>> random_walk("e", 8, intervals=[-3, -1, 1, 3], octave=5)
    """
    if intervals is None:
        intervals = [-2, -1, 1, 2]

    if steps < 1:
        return seq()

    rng = random.Random(seed)

    # Start note
    current = note(start, duration=duration, octave=octave)
    elements: list[ComposeElement] = [current]
    current_midi = current.midi_pitch

    for _ in range(steps - 1):
        # Choose a random interval
        interval = rng.choice(intervals)
        new_midi = current_midi + interval

        # Clamp to range, reflecting if necessary
        if new_midi < min_pitch:
            new_midi = min_pitch + (min_pitch - new_midi)
        elif new_midi > max_pitch:
            new_midi = max_pitch - (new_midi - max_pitch)

        # Clamp again in case of double reflection
        new_midi = max(min_pitch, min(max_pitch, new_midi))

        # Create note from MIDI pitch
        new_note = _midi_to_note(new_midi, duration=duration)
        elements.append(new_note)
        current_midi = new_midi

    return Seq(elements=elements)


def drunk_walk(
    start: str,
    steps: int,
    *,
    max_step: int = 3,
    duration: int | None = None,
    octave: int = 4,
    min_pitch: int = 36,
    max_pitch: int = 84,
    bias: float = 0.0,
    seed: int | None = None,
) -> Seq:
    """Generate a melody using a "drunk walk" biased toward smaller intervals.

    Similar to random_walk but with a triangular distribution favoring
    smaller steps, creating more stepwise motion.

    Args:
        start: Starting pitch name (e.g., "c").
        steps: Number of notes to generate.
        max_step: Maximum interval size in semitones.
        duration: Duration for all notes.
        octave: Starting octave.
        min_pitch: Minimum MIDI pitch.
        max_pitch: Maximum MIDI pitch.
        bias: Directional bias (-1 to 1). Positive = upward, negative = downward.
        seed: Optional random seed for reproducibility.

    Returns:
        A Seq containing the drunk walk melody.

    Examples:
        >>> drunk_walk("c", 16, max_step=2, duration=8)  # Mostly stepwise
        >>> drunk_walk("g", 8, max_step=5, bias=0.3)    # Slight upward tendency
    """
    if steps < 1:
        return seq()

    rng = random.Random(seed)

    # Start note
    current = note(start, duration=duration, octave=octave)
    elements: list[ComposeElement] = [current]
    current_midi = current.midi_pitch

    for _ in range(steps - 1):
        # Triangular distribution centered at 0, favoring small steps
        # We generate by summing two uniform random values
        step = rng.randint(-max_step, max_step)

        # Apply bias
        if bias != 0:
            bias_step = int(bias * max_step * rng.random())
            step += bias_step

        # Second random component to create triangular-ish distribution
        step2 = rng.randint(-max_step, max_step)
        interval = (step + step2) // 2

        new_midi = current_midi + interval

        # Clamp to range
        if new_midi < min_pitch:
            new_midi = min_pitch + (min_pitch - new_midi) % (max_pitch - min_pitch)
        elif new_midi > max_pitch:
            new_midi = max_pitch - (new_midi - max_pitch) % (max_pitch - min_pitch)

        new_midi = max(min_pitch, min(max_pitch, new_midi))

        new_note = _midi_to_note(new_midi, duration=duration)
        elements.append(new_note)
        current_midi = new_midi

    return Seq(elements=elements)


# =============================================================================
# Rhythmic Generators
# =============================================================================


def euclidean(
    hits: int,
    steps: int,
    pitch: str = "c",
    *,
    duration: int | None = None,
    rotate: int = 0,
) -> Seq:
    """Generate a Euclidean rhythm pattern.

    Euclidean rhythms distribute k hits as evenly as possible over n steps,
    producing patterns found in many world music traditions.

    Args:
        hits: Number of notes (hits) in the pattern.
        steps: Total number of steps (hits + rests).
        pitch: Pitch for the hit notes.
        duration: Duration for each step.
        rotate: Rotate the pattern by this many positions.

    Returns:
        A Seq with notes for hits and rests for non-hits.

    Examples:
        >>> euclidean(3, 8, "c")   # [x . . x . . x .] - Cuban tresillo
        >>> euclidean(5, 8, "c")   # [x . x x . x x .] - Cinquillo
        >>> euclidean(7, 12, "c")  # West African bell pattern
        >>> euclidean(3, 8, "c", rotate=1)  # Rotated version
    """
    if hits < 0 or steps < 0:
        raise ValueError("hits and steps must be non-negative")
    if hits > steps:
        raise ValueError("hits cannot be greater than steps")
    if steps == 0:
        return seq()

    # Bjorklund's algorithm for Euclidean rhythms
    pattern = _bjorklund(hits, steps)

    # Rotate if requested
    if rotate != 0:
        rotate = rotate % len(pattern)
        pattern = pattern[rotate:] + pattern[:rotate]

    # Convert to notes and rests
    elements = []
    for is_hit in pattern:
        if is_hit:
            elements.append(note(pitch, duration=duration))
        else:
            elements.append(rest(duration=duration))

    return Seq(elements=elements)


def _bjorklund(hits: int, steps: int) -> list[bool]:
    """Bjorklund's algorithm for computing Euclidean rhythms."""
    if hits == 0:
        return [False] * steps
    if hits == steps:
        return [True] * steps

    # Initialize groups
    groups: list[list[bool]] = [[True] for _ in range(hits)]
    remainder: list[list[bool]] = [[False] for _ in range(steps - hits)]

    while len(remainder) > 1:
        new_groups = []
        while groups and remainder:
            g = groups.pop(0)
            r = remainder.pop(0)
            new_groups.append(g + r)

        # Remaining groups become the new remainder
        if groups:
            remainder = groups
        groups = new_groups

    # Flatten
    result = []
    for g in groups + remainder:
        result.extend(g)
    return result


def probability_seq(
    notes: list[str],
    length: int,
    *,
    probability: float = 0.7,
    duration: int | None = None,
    seed: int | None = None,
) -> Seq:
    """Generate a sequence where each step has a probability of being a note.

    Args:
        notes: List of pitch names to randomly choose from.
        length: Number of steps in the sequence.
        probability: Probability (0-1) that each step contains a note vs rest.
        duration: Duration for notes and rests.
        seed: Optional random seed for reproducibility.

    Returns:
        A Seq with notes and rests based on probability.

    Examples:
        >>> probability_seq(["c", "d", "e", "g", "a"], 16, probability=0.7)
        >>> probability_seq(["c"], 8, probability=0.5, duration=16)  # Sparse
    """
    if not notes:
        raise ValueError("notes list cannot be empty")
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1")

    rng = random.Random(seed)
    elements = []

    for _ in range(length):
        if rng.random() < probability:
            pitch = rng.choice(notes)
            elements.append(note(pitch, duration=duration))
        else:
            elements.append(rest(duration=duration))

    return Seq(elements=elements)


def rest_probability(
    sequence: Seq,
    probability: float = 0.2,
    *,
    seed: int | None = None,
) -> Seq:
    """Replace some notes in a sequence with rests based on probability.

    Args:
        sequence: The input sequence.
        probability: Probability (0-1) that each note becomes a rest.
        seed: Optional random seed for reproducibility.

    Returns:
        A new Seq with some notes replaced by rests.

    Examples:
        >>> melody = seq(note("c"), note("d"), note("e"), note("f"))
        >>> sparse = rest_probability(melody, 0.3)  # 30% become rests
    """
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1")

    rng = random.Random(seed)
    elements = []

    for elem in sequence.elements:
        if isinstance(elem, Note) and rng.random() < probability:
            # Replace note with rest of same duration
            elements.append(
                rest(duration=elem.duration, ms=elem.ms, seconds=elem.seconds)
            )
        else:
            elements.append(elem)

    return Seq(elements=elements)


# =============================================================================
# Markov Chains
# =============================================================================


class MarkovChain:
    """A Markov chain for generating note sequences.

    The chain stores transition probabilities between states (pitches or
    sequences of pitches for higher-order chains).
    """

    def __init__(
        self,
        transitions: dict[str, dict[str, float]] | None = None,
        order: int = 1,
    ):
        """Initialize a Markov chain.

        Args:
            transitions: Dictionary mapping states to dictionaries of
                {next_state: probability}. If None, starts empty.
            order: Order of the Markov chain (1 = first-order, etc.).
        """
        self.transitions: dict[str, dict[str, float]] = transitions or {}
        self.order = order

    def generate(
        self,
        start: str | None = None,
        length: int = 16,
        *,
        duration: int | None = None,
        seed: int | None = None,
    ) -> Seq:
        """Generate a sequence using the Markov chain.

        Args:
            start: Starting state. If None, randomly chosen from states.
            length: Number of notes to generate.
            duration: Duration for all generated notes.
            seed: Optional random seed for reproducibility.

        Returns:
            A Seq of generated notes.

        Examples:
            >>> chain = MarkovChain({
            ...     "c": {"d": 0.5, "e": 0.3, "g": 0.2},
            ...     "d": {"e": 0.6, "c": 0.4},
            ... })
            >>> chain.generate(start="c", length=8)
        """
        if not self.transitions:
            raise ValueError("Markov chain has no transitions defined")

        rng = random.Random(seed)

        # Choose starting state
        if start is None:
            start = rng.choice(list(self.transitions.keys()))
        elif start not in self.transitions:
            # If start state has no transitions, pick a random one
            start = rng.choice(list(self.transitions.keys()))

        elements = [note(start, duration=duration)]
        current = start

        for _ in range(length - 1):
            if current not in self.transitions:
                # Dead end - pick random state
                current = rng.choice(list(self.transitions.keys()))

            trans = self.transitions[current]
            if not trans:
                current = rng.choice(list(self.transitions.keys()))
                elements.append(note(current, duration=duration))
                continue

            # Weighted random choice for next state
            states = list(trans.keys())
            weights = list(trans.values())
            current = rng.choices(states, weights=weights, k=1)[0]
            elements.append(note(current, duration=duration))

        return Seq(elements=elements)


def markov_chain(transitions: dict[str, dict[str, float]]) -> MarkovChain:
    """Create a Markov chain from transition probabilities.

    Args:
        transitions: Dictionary mapping states to dictionaries of
            {next_state: probability}.

    Returns:
        A MarkovChain instance.

    Examples:
        >>> chain = markov_chain({
        ...     "c": {"d": 0.5, "e": 0.3, "g": 0.2},
        ...     "d": {"e": 0.6, "c": 0.4},
        ...     "e": {"f": 0.5, "g": 0.3, "c": 0.2},
        ... })
        >>> melody = chain.generate(start="c", length=16)
    """
    return MarkovChain(transitions=transitions)


def learn_markov(
    sequence: Seq,
    order: int = 1,
) -> MarkovChain:
    """Learn a Markov chain from an existing sequence.

    Analyzes the sequence to extract transition probabilities.

    Args:
        sequence: A sequence of notes to learn from.
        order: Order of the Markov chain (1 = consider only previous note,
            2 = consider previous 2 notes, etc.).

    Returns:
        A MarkovChain learned from the sequence.

    Examples:
        >>> melody = seq(note("c"), note("d"), note("e"), note("d"), note("c"))
        >>> chain = learn_markov(melody)
        >>> new_melody = chain.generate(length=16)
    """
    # Extract pitches from notes
    pitches: list[str] = []
    for elem in sequence.elements:
        if isinstance(elem, Note):
            pitches.append(elem.pitch)

    if len(pitches) < order + 1:
        raise ValueError(f"Sequence too short for order-{order} Markov chain")

    # Count transitions
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for i in range(len(pitches) - order):
        if order == 1:
            state = pitches[i]
        else:
            state = ",".join(pitches[i : i + order])
        next_pitch = pitches[i + order]
        counts[state][next_pitch] += 1

    # Convert counts to probabilities
    transitions: dict[str, dict[str, float]] = {}
    for state, next_counts in counts.items():
        total = sum(next_counts.values())
        transitions[state] = {
            pitch: count / total for pitch, count in next_counts.items()
        }

    return MarkovChain(transitions=transitions, order=order)


# =============================================================================
# L-Systems (Lindenmayer Systems)
# =============================================================================


def lsystem(
    axiom: str,
    rules: dict[str, str],
    iterations: int,
    note_map: dict[str, Note | Rest],
    *,
    default: Note | Rest | None = None,
) -> Seq:
    """Generate a sequence using an L-system (Lindenmayer system).

    L-systems use string rewriting rules to generate complex patterns
    from simple axioms.

    Args:
        axiom: The initial string (e.g., "A").
        rules: Dictionary mapping symbols to their replacements.
        iterations: Number of times to apply the rules.
        note_map: Dictionary mapping symbols to Notes or Rests.
        default: Default note/rest for unmapped symbols. If None, unmapped
            symbols are ignored.

    Returns:
        A Seq representing the L-system output.

    Examples:
        >>> # Fibonacci-like pattern
        >>> lsystem(
        ...     axiom="A",
        ...     rules={"A": "AB", "B": "A"},
        ...     iterations=5,
        ...     note_map={"A": note("c", duration=8), "B": note("e", duration=8)}
        ... )

        >>> # More complex pattern
        >>> lsystem(
        ...     axiom="F",
        ...     rules={"F": "F+G", "G": "F-G"},
        ...     iterations=4,
        ...     note_map={
        ...         "F": note("c"), "G": note("g"),
        ...         "+": note("e"), "-": note("d")
        ...     }
        ... )
    """
    if iterations < 0:
        raise ValueError("iterations must be non-negative")

    # Expand the L-system
    current = axiom
    for _ in range(iterations):
        next_str = ""
        for char in current:
            next_str += rules.get(char, char)
        current = next_str

    # Convert to notes
    elements = []
    for char in current:
        if char in note_map:
            # Create a copy of the note/rest
            elem = note_map[char]
            if isinstance(elem, Note):
                elements.append(
                    note(
                        elem.pitch,
                        duration=elem.duration,
                        octave=elem.octave,
                        accidental=elem.accidental,
                        dots=elem.dots,
                        ms=elem.ms,
                        seconds=elem.seconds,
                        slurred=elem.slurred,
                    )
                )
            elif isinstance(elem, Rest):
                elements.append(
                    rest(
                        duration=elem.duration,
                        dots=elem.dots,
                        ms=elem.ms,
                        seconds=elem.seconds,
                    )
                )
        elif default is not None:
            if isinstance(default, Note):
                elements.append(
                    note(
                        default.pitch,
                        duration=default.duration,
                        octave=default.octave,
                        accidental=default.accidental,
                    )
                )
            elif isinstance(default, Rest):
                elements.append(rest(duration=default.duration))

    return Seq(elements=elements)


# =============================================================================
# Cellular Automata
# =============================================================================


def cellular_automaton(
    rule: int,
    width: int,
    steps: int,
    pitch_on: str = "c",
    *,
    duration: int | None = None,
    initial: list[bool] | None = None,
    wrap: bool = True,
) -> Seq:
    """Generate a sequence using a 1D elementary cellular automaton.

    Uses Wolfram's elementary cellular automata rules (0-255).
    Each step of the automaton produces one beat, with cells mapped
    to notes (on) or rests (off).

    Args:
        rule: Wolfram rule number (0-255).
        width: Width of the automaton (number of cells).
        steps: Number of time steps to generate.
        pitch_on: Pitch for "on" cells.
        duration: Duration for each note/rest.
        initial: Initial state. If None, starts with single cell in center.
        wrap: Whether edges wrap around (True) or stay fixed (False).

    Returns:
        A Seq alternating between automaton rows.

    Examples:
        >>> cellular_automaton(rule=110, width=8, steps=16, pitch_on="c")
        >>> cellular_automaton(rule=30, width=16, steps=8)  # Chaotic pattern
        >>> cellular_automaton(rule=90, width=8, steps=8)   # Sierpinski triangle
    """
    if not 0 <= rule <= 255:
        raise ValueError("rule must be between 0 and 255")
    if width < 1 or steps < 1:
        raise ValueError("width and steps must be positive")

    # Parse rule into lookup table
    rule_table = [(rule >> i) & 1 for i in range(8)]

    # Initialize state
    if initial is not None:
        if len(initial) != width:
            raise ValueError(f"initial must have length {width}")
        state = list(initial)
    else:
        state = [False] * width
        state[width // 2] = True

    elements = []

    for _ in range(steps):
        # Convert current row to notes
        for cell in state:
            if cell:
                elements.append(note(pitch_on, duration=duration))
            else:
                elements.append(rest(duration=duration))

        # Compute next state
        new_state = []
        for i in range(width):
            if wrap:
                left = state[(i - 1) % width]
                center = state[i]
                right = state[(i + 1) % width]
            else:
                left = state[i - 1] if i > 0 else False
                center = state[i]
                right = state[i + 1] if i < width - 1 else False

            # Compute neighborhood index
            idx = (int(left) << 2) | (int(center) << 1) | int(right)
            new_state.append(bool(rule_table[idx]))

        state = new_state

    return Seq(elements=elements)


# =============================================================================
# Shift Register (LFSR)
# =============================================================================


def shift_register(
    length: int,
    taps: list[int] | None = None,
    *,
    bits: int = 8,
    scale: list[str] | None = None,
    duration: int | None = None,
    initial: int | None = None,
    mode: str = "pitch",
) -> Seq:
    """Generate a sequence using a Linear Feedback Shift Register (LFSR).

    LFSRs are used in analog synthesizers to generate pseudo-random
    but deterministic and cyclic patterns. The register shifts bits
    and feeds back an XOR of selected "tap" positions.

    Args:
        length: Number of notes to generate.
        taps: Bit positions to XOR for feedback (0-indexed from LSB).
            If None, uses maximal-length taps for the given bit size.
        bits: Size of the shift register in bits (1-16).
        scale: List of pitches to map register values to. If None, uses
            chromatic scale from C.
        duration: Duration for each note.
        initial: Initial register value. If None, starts at 1.
        mode: Output mode:
            - "pitch": Map full register value to scale index
            - "binary": Output note (bit=1) or rest (bit=0) based on LSB
            - "velocity": Use register value for velocity (requires scale)

    Returns:
        A Seq of notes based on the shift register output.

    Examples:
        >>> # 8-bit LFSR mapped to pentatonic scale
        >>> shift_register(16, scale=["c", "d", "e", "g", "a"])

        >>> # Classic analog sequencer pattern (4-bit)
        >>> shift_register(32, bits=4, scale=["c", "e", "g", "b"])

        >>> # Binary rhythm pattern
        >>> shift_register(16, bits=8, mode="binary")

        >>> # Custom taps for different pattern
        >>> shift_register(16, taps=[0, 2, 3, 5], bits=8)
    """
    if bits < 1 or bits > 16:
        raise ValueError("bits must be between 1 and 16")
    if length < 1:
        raise ValueError("length must be positive")

    # Default maximal-length LFSR taps (produces longest cycle before repeating)
    default_taps: dict[int, list[int]] = {
        1: [0],
        2: [0, 1],
        3: [0, 2],
        4: [0, 3],
        5: [1, 4],
        6: [0, 5],
        7: [0, 6],
        8: [1, 2, 3, 7],  # x^8 + x^4 + x^3 + x^2 + 1
        9: [3, 8],
        10: [2, 9],
        11: [1, 10],
        12: [0, 3, 5, 11],
        13: [0, 2, 3, 12],
        14: [0, 2, 4, 13],
        15: [0, 14],
        16: [1, 2, 4, 15],
    }

    if taps is None:
        taps = default_taps.get(bits, [0, bits - 1])

    # Validate taps
    for tap in taps:
        if tap < 0 or tap >= bits:
            raise ValueError(f"tap {tap} is out of range for {bits}-bit register")

    # Default scale (C major - chromatic would require accidental handling)
    if scale is None:
        scale = ["c", "d", "e", "f", "g", "a", "b"]

    # Initialize register
    max_val = (1 << bits) - 1
    if initial is None:
        register = 1  # Can't start at 0 (would stay 0)
    else:
        register = initial & max_val
        if register == 0:
            register = 1  # Prevent stuck state

    elements: list[ComposeElement] = []

    for _ in range(length):
        if mode == "binary":
            # Output based on LSB
            if register & 1:
                elements.append(note(scale[0], duration=duration))
            else:
                elements.append(rest(duration=duration))
        elif mode == "velocity":
            # Map register to scale (velocity mode uses same pitch mapping,
            # actual velocity would be applied via MIDI transform post-generation)
            scale_idx = register % len(scale)
            elements.append(note(scale[scale_idx], duration=duration))
        else:  # mode == "pitch"
            # Map register value to scale
            scale_idx = register % len(scale)
            elements.append(note(scale[scale_idx], duration=duration))

        # Compute feedback (XOR of tap positions)
        feedback = 0
        for tap in taps:
            feedback ^= (register >> tap) & 1

        # Shift register and insert feedback at MSB
        register = ((register >> 1) | (feedback << (bits - 1))) & max_val

    return Seq(elements=elements)


def turing_machine(
    length: int,
    *,
    bits: int = 8,
    scale: list[str] | None = None,
    probability: float = 0.0,
    duration: int | None = None,
    initial: int | None = None,
    seed: int | None = None,
) -> Seq:
    """Generate a sequence using a Turing Machine-style shift register.

    Inspired by the Music Thing Modular Turing Machine, this generates
    looping patterns that can gradually evolve. With probability=0, it
    produces a fixed repeating pattern. Higher probabilities introduce
    random bit flips, causing the pattern to evolve.

    Args:
        length: Number of notes to generate.
        bits: Size of the shift register (loop length when probability=0).
        scale: List of pitches. If None, uses pentatonic scale.
        probability: Chance (0-1) of flipping a bit each step.
            0 = locked loop, 1 = completely random.
        duration: Duration for each note.
        initial: Initial register value. If None, random.
        seed: Random seed for reproducibility.

    Returns:
        A Seq of notes based on the Turing Machine output.

    Examples:
        >>> # Locked 8-step loop
        >>> turing_machine(32, bits=8, probability=0)

        >>> # Slowly evolving pattern
        >>> turing_machine(64, probability=0.1)

        >>> # Chaotic, mostly random
        >>> turing_machine(32, probability=0.9)
    """
    if bits < 1 or bits > 16:
        raise ValueError("bits must be between 1 and 16")
    if length < 1:
        raise ValueError("length must be positive")
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1")

    rng = random.Random(seed)

    # Default to pentatonic scale
    if scale is None:
        scale = ["c", "d", "e", "g", "a"]

    # Initialize register
    max_val = (1 << bits) - 1
    if initial is None:
        register = rng.randint(1, max_val)
    else:
        register = initial & max_val
        if register == 0:
            register = 1

    elements: list[ComposeElement] = []

    for _ in range(length):
        # Map register to scale
        scale_idx = register % len(scale)
        elements.append(note(scale[scale_idx], duration=duration))

        # Get the bit that's about to be shifted out
        lsb = register & 1

        # Maybe flip it
        if rng.random() < probability:
            lsb ^= 1

        # Shift and insert (possibly flipped) bit at MSB
        register = ((register >> 1) | (lsb << (bits - 1))) & max_val

    return Seq(elements=elements)


# =============================================================================
# Helper Functions
# =============================================================================


def _midi_to_note(midi_pitch: int, *, duration: int | None = None) -> Note:
    """Convert a MIDI pitch number to a Note.

    Args:
        midi_pitch: MIDI pitch number (0-127).
        duration: Optional duration for the note.

    Returns:
        A Note with the appropriate pitch and octave.
    """
    pitch_names = ["c", "c", "d", "d", "e", "f", "f", "g", "g", "a", "a", "b"]
    accidentals = [None, "+", None, "+", None, None, "+", None, "+", None, "+", None]

    pitch_class = midi_pitch % 12
    octave = (midi_pitch // 12) - 1

    return note(
        pitch_names[pitch_class],
        duration=duration,
        octave=octave,
        accidental=accidentals[pitch_class],
    )
