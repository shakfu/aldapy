"""AST-level transformers for musical sequences.

These transformers operate on the symbolic representation (notes, intervals,
durations) and can be exported back to Alda source code.

For MIDI-level transformers (timing, velocity), see aldakit.midi.transform.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Callable, TypeVar

from .core import Chord, Note, Rest, Seq

if TYPE_CHECKING:
    pass

T = TypeVar("T")


# =============================================================================
# Pitch Transformers
# =============================================================================


def transpose(sequence: Seq, semitones: int) -> Seq:
    """Transpose all notes in a sequence by the given number of semitones.

    Args:
        sequence: The sequence to transpose.
        semitones: Number of semitones to transpose (positive = up, negative = down).

    Returns:
        A new sequence with all notes transposed.

    Examples:
        >>> melody = seq(note("c"), note("d"), note("e"))
        >>> transposed = transpose(melody, 5)  # Up a perfect fourth
        >>> transposed.to_alda()
        'f g a'
    """
    new_elements = []
    for elem in sequence.elements:
        if isinstance(elem, Note):
            new_elements.append(elem.transpose(semitones))
        elif isinstance(elem, Chord):
            new_notes = tuple(n.transpose(semitones) for n in elem.notes)
            new_elements.append(Chord(notes=new_notes, duration=elem.duration))
        elif isinstance(elem, Seq):
            new_elements.append(transpose(elem, semitones))
        else:
            # Rest and other elements pass through unchanged
            new_elements.append(elem)
    return Seq(elements=new_elements)


def invert(sequence: Seq, axis: int | None = None) -> Seq:
    """Invert intervals in a sequence around an axis pitch.

    Each note is reflected around the axis: if a note is N semitones above
    the axis, the inverted note will be N semitones below, and vice versa.

    Args:
        sequence: The sequence to invert.
        axis: The MIDI pitch number to invert around. If None, uses the
              first note's pitch as the axis.

    Returns:
        A new sequence with inverted intervals.

    Examples:
        >>> melody = seq(note("c"), note("e"), note("g"))  # C E G (major)
        >>> inverted = invert(melody)  # Invert around C
        >>> # C stays C, E (4 semitones up) becomes Ab (4 down), G (7 up) becomes F (7 down)
    """
    # Find first note to use as axis if not specified
    inversion_axis: int
    if axis is None:
        found_axis: int | None = None
        for elem in sequence.elements:
            if isinstance(elem, Note):
                found_axis = elem.midi_pitch
                break
        if found_axis is None:
            # No notes found, return unchanged
            return Seq(elements=list(sequence.elements))
        inversion_axis = found_axis
    else:
        inversion_axis = axis

    new_elements = []
    for elem in sequence.elements:
        if isinstance(elem, Note):
            # Reflect around axis: new_pitch = 2 * axis - old_pitch
            current_pitch = elem.midi_pitch
            new_midi_pitch = 2 * inversion_axis - current_pitch
            # Calculate the transposition needed
            delta = new_midi_pitch - current_pitch
            new_elements.append(elem.transpose(delta))
        elif isinstance(elem, Chord):
            new_notes = []
            for n in elem.notes:
                current_pitch = n.midi_pitch
                new_midi_pitch = 2 * inversion_axis - current_pitch
                delta = new_midi_pitch - current_pitch
                new_notes.append(n.transpose(delta))
            new_elements.append(Chord(notes=tuple(new_notes), duration=elem.duration))
        elif isinstance(elem, Seq):
            new_elements.append(invert(elem, inversion_axis))
        else:
            new_elements.append(elem)
    return Seq(elements=new_elements)


def reverse(sequence: Seq) -> Seq:
    """Reverse the order of elements in a sequence (retrograde).

    Args:
        sequence: The sequence to reverse.

    Returns:
        A new sequence with elements in reverse order.

    Examples:
        >>> melody = seq(note("c"), note("d"), note("e"))
        >>> reversed_melody = reverse(melody)
        >>> reversed_melody.to_alda()
        'e d c'
    """
    return Seq(elements=list(reversed(sequence.elements)))


def shuffle(sequence: Seq, seed: int | None = None) -> Seq:
    """Randomly shuffle the elements in a sequence.

    Args:
        sequence: The sequence to shuffle.
        seed: Optional random seed for reproducibility.

    Returns:
        A new sequence with elements in random order.

    Examples:
        >>> melody = seq(note("c"), note("d"), note("e"), note("f"))
        >>> shuffled = shuffle(melody, seed=42)  # Reproducible shuffle
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()

    elements = list(sequence.elements)
    rng.shuffle(elements)
    return Seq(elements=elements)


def retrograde_inversion(sequence: Seq, axis: int | None = None) -> Seq:
    """Apply both retrograde (reverse) and inversion.

    This is a common 12-tone technique that combines both transformations.

    Args:
        sequence: The sequence to transform.
        axis: The MIDI pitch to invert around (defaults to first note).

    Returns:
        A new sequence that is both reversed and inverted.
    """
    return reverse(invert(sequence, axis))


# =============================================================================
# Structural Transformers
# =============================================================================


def augment(sequence: Seq, factor: int = 2) -> Seq:
    """Augment (lengthen) all durations in a sequence.

    Args:
        sequence: The sequence to augment.
        factor: The factor to multiply durations by (default 2 = double).

    Returns:
        A new sequence with longer note values.

    Examples:
        >>> melody = seq(note("c", duration=8), note("d", duration=8))
        >>> augmented = augment(melody, 2)  # 8th notes become quarter notes
        >>> augmented.to_alda()
        'c4 d4'
    """
    new_elements = []
    for elem in sequence.elements:
        if isinstance(elem, Note):
            if elem.duration is not None:
                # Duration denominator: smaller = longer, so divide by factor
                new_dur = max(1, elem.duration // factor)
                new_elements.append(elem.with_duration(new_dur))
            elif elem.ms is not None:
                from dataclasses import replace

                new_elements.append(replace(elem, ms=elem.ms * factor))
            elif elem.seconds is not None:
                from dataclasses import replace

                new_elements.append(replace(elem, seconds=elem.seconds * factor))
            else:
                new_elements.append(elem)
        elif isinstance(elem, Rest):
            if elem.duration is not None:
                from dataclasses import replace

                new_dur = max(1, elem.duration // factor)
                new_elements.append(replace(elem, duration=new_dur))
            elif elem.ms is not None:
                from dataclasses import replace

                new_elements.append(replace(elem, ms=elem.ms * factor))
            elif elem.seconds is not None:
                from dataclasses import replace

                new_elements.append(replace(elem, seconds=elem.seconds * factor))
            else:
                new_elements.append(elem)
        elif isinstance(elem, Chord):
            if elem.duration is not None:
                new_dur = max(1, elem.duration // factor)
                new_elements.append(Chord(notes=elem.notes, duration=new_dur))
            else:
                new_elements.append(elem)
        elif isinstance(elem, Seq):
            new_elements.append(augment(elem, factor))
        else:
            new_elements.append(elem)
    return Seq(elements=new_elements)


def diminish(sequence: Seq, factor: int = 2) -> Seq:
    """Diminish (shorten) all durations in a sequence.

    Args:
        sequence: The sequence to diminish.
        factor: The factor to divide durations by (default 2 = halve).

    Returns:
        A new sequence with shorter note values.

    Examples:
        >>> melody = seq(note("c", duration=4), note("d", duration=4))
        >>> diminished = diminish(melody, 2)  # Quarter notes become 8th notes
        >>> diminished.to_alda()
        'c8 d8'
    """
    new_elements = []
    for elem in sequence.elements:
        if isinstance(elem, Note):
            if elem.duration is not None:
                # Duration denominator: larger = shorter, so multiply by factor
                new_dur = elem.duration * factor
                new_elements.append(elem.with_duration(new_dur))
            elif elem.ms is not None:
                from dataclasses import replace

                new_elements.append(replace(elem, ms=elem.ms / factor))
            elif elem.seconds is not None:
                from dataclasses import replace

                new_elements.append(replace(elem, seconds=elem.seconds / factor))
            else:
                new_elements.append(elem)
        elif isinstance(elem, Rest):
            if elem.duration is not None:
                from dataclasses import replace

                new_dur = elem.duration * factor
                new_elements.append(replace(elem, duration=new_dur))
            elif elem.ms is not None:
                from dataclasses import replace

                new_elements.append(replace(elem, ms=elem.ms / factor))
            elif elem.seconds is not None:
                from dataclasses import replace

                new_elements.append(replace(elem, seconds=elem.seconds / factor))
            else:
                new_elements.append(elem)
        elif isinstance(elem, Chord):
            if elem.duration is not None:
                new_dur = elem.duration * factor
                new_elements.append(Chord(notes=elem.notes, duration=new_dur))
            else:
                new_elements.append(elem)
        elif isinstance(elem, Seq):
            new_elements.append(diminish(elem, factor))
        else:
            new_elements.append(elem)
    return Seq(elements=new_elements)


def fragment(sequence: Seq, length: int) -> Seq:
    """Take the first N elements from a sequence.

    Args:
        sequence: The sequence to fragment.
        length: Number of elements to take.

    Returns:
        A new sequence with only the first N elements.

    Examples:
        >>> melody = seq(note("c"), note("d"), note("e"), note("f"))
        >>> frag = fragment(melody, 2)
        >>> frag.to_alda()
        'c d'
    """
    return Seq(elements=list(sequence.elements[:length]))


def loop(sequence: Seq, times: int) -> Seq:
    """Repeat a sequence a specified number of times.

    Unlike the `*` operator which creates a Repeat node, this function
    explicitly duplicates the elements, which can be useful when you
    want to modify individual repetitions.

    Args:
        sequence: The sequence to repeat.
        times: Number of times to repeat.

    Returns:
        A new sequence with elements repeated.

    Examples:
        >>> motif = seq(note("c"), note("d"))
        >>> looped = loop(motif, 3)
        >>> looped.to_alda()
        'c d c d c d'
    """
    elements = list(sequence.elements) * times
    return Seq(elements=elements)


def interleave(*sequences: Seq) -> Seq:
    """Interleave elements from multiple sequences.

    Takes elements alternately from each sequence until the shortest
    is exhausted.

    Args:
        *sequences: Two or more sequences to interleave.

    Returns:
        A new sequence with interleaved elements.

    Examples:
        >>> melody1 = seq(note("c"), note("e"), note("g"))
        >>> melody2 = seq(note("d"), note("f"), note("a"))
        >>> interleaved = interleave(melody1, melody2)
        >>> interleaved.to_alda()
        'c d e f g a'
    """
    if not sequences:
        return Seq(elements=[])

    result = []
    iterators = [iter(s.elements) for s in sequences]

    while True:
        exhausted = 0
        for it in iterators:
            try:
                result.append(next(it))
            except StopIteration:
                exhausted += 1
        if exhausted == len(iterators):
            break

    return Seq(elements=result)


def rotate(sequence: Seq, positions: int) -> Seq:
    """Rotate elements in a sequence by a number of positions.

    Positive positions rotate left (first element moves to end),
    negative positions rotate right (last element moves to front).

    Args:
        sequence: The sequence to rotate.
        positions: Number of positions to rotate (positive = left, negative = right).

    Returns:
        A new sequence with rotated elements.

    Examples:
        >>> melody = seq(note("c"), note("d"), note("e"), note("f"))
        >>> rotated = rotate(melody, 1)  # c d e f -> d e f c
        >>> rotated.to_alda()
        'd e f c'
    """
    if not sequence.elements:
        return Seq(elements=[])

    n = len(sequence.elements)
    positions = positions % n  # Handle positions > length
    elements = list(sequence.elements)
    rotated = elements[positions:] + elements[:positions]
    return Seq(elements=rotated)


def take_every(sequence: Seq, n: int, offset: int = 0) -> Seq:
    """Take every Nth element from a sequence.

    Args:
        sequence: The sequence to sample from.
        n: Take every Nth element.
        offset: Starting offset (0-indexed).

    Returns:
        A new sequence with sampled elements.

    Examples:
        >>> scale = seq(note("c"), note("d"), note("e"), note("f"),
        ...             note("g"), note("a"), note("b"))
        >>> thirds = take_every(scale, 2)  # c e g b (every other note)
    """
    elements = list(sequence.elements[offset::n])
    return Seq(elements=elements)


def split(sequence: Seq, size: int) -> list[Seq]:
    """Split a sequence into chunks of a given size.

    Args:
        sequence: The sequence to split.
        size: Maximum size of each chunk.

    Returns:
        A list of sequences, each with at most `size` elements.

    Examples:
        >>> melody = seq(note("c"), note("d"), note("e"), note("f"))
        >>> chunks = split(melody, 2)
        >>> [c.to_alda() for c in chunks]
        ['c d', 'e f']
    """
    elements = list(sequence.elements)
    return [Seq(elements=elements[i : i + size]) for i in range(0, len(elements), size)]


def concat(*sequences: Seq) -> Seq:
    """Concatenate multiple sequences into one.

    Args:
        *sequences: Sequences to concatenate.

    Returns:
        A new sequence with all elements combined.

    Examples:
        >>> intro = seq(note("c"), note("d"))
        >>> verse = seq(note("e"), note("f"))
        >>> full = concat(intro, verse)
        >>> full.to_alda()
        'c d e f'
    """
    elements = []
    for s in sequences:
        elements.extend(s.elements)
    return Seq(elements=elements)


# =============================================================================
# Helper Functions
# =============================================================================


def pipe(sequence: Seq, *transforms: Callable[[Seq], Seq]) -> Seq:
    """Apply a series of transformations to a sequence.

    This is a convenience function for chaining multiple transformers.

    Args:
        sequence: The initial sequence.
        *transforms: Functions that take a Seq and return a Seq.

    Returns:
        The sequence after all transformations have been applied.

    Examples:
        >>> melody = seq(note("c"), note("d"), note("e"))
        >>> result = pipe(
        ...     melody,
        ...     lambda s: transpose(s, 5),
        ...     reverse,
        ...     lambda s: augment(s, 2),
        ... )
    """
    result = sequence
    for transform in transforms:
        result = transform(result)
    return result


def identity(sequence: Seq) -> Seq:
    """Return the sequence unchanged.

    Useful as a placeholder in conditional transformation chains.

    Args:
        sequence: The sequence.

    Returns:
        The same sequence (actually a copy with same elements).
    """
    return Seq(elements=list(sequence.elements))
