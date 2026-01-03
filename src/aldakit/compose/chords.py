"""Chord voicing utilities for building common chord types.

This module provides convenient constructors for building chords by name,
such as major, minor, diminished, augmented, and various seventh chords.
"""

from __future__ import annotations

from .core import Chord, Note, note
from .scales import OFFSET_TO_PITCH, PITCH_TO_OFFSET

# =============================================================================
# Chord Interval Definitions
# =============================================================================

# Intervals from root (in semitones) for common chord types
CHORD_INTERVALS: dict[str, tuple[int, ...]] = {
    # Triads
    "major": (0, 4, 7),
    "minor": (0, 3, 7),
    "diminished": (0, 3, 6),
    "augmented": (0, 4, 8),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    # Seventh chords
    "major7": (0, 4, 7, 11),
    "minor7": (0, 3, 7, 10),
    "dominant7": (0, 4, 7, 10),
    "diminished7": (0, 3, 6, 9),
    "half-diminished7": (0, 3, 6, 10),
    "minor-major7": (0, 3, 7, 11),
    "augmented7": (0, 4, 8, 10),
    "augmented-major7": (0, 4, 8, 11),
    # Sixth chords
    "major6": (0, 4, 7, 9),
    "minor6": (0, 3, 7, 9),
    # Extended chords
    "dominant9": (0, 4, 7, 10, 14),
    "major9": (0, 4, 7, 11, 14),
    "minor9": (0, 3, 7, 10, 14),
    "dominant11": (0, 4, 7, 10, 14, 17),
    "dominant13": (0, 4, 7, 10, 14, 17, 21),
    # Added tone chords
    "add9": (0, 4, 7, 14),
    "add11": (0, 4, 7, 17),
    "madd9": (0, 3, 7, 14),
    # Power chord
    "power": (0, 7),
    "5": (0, 7),
}


# =============================================================================
# Core Chord Builder
# =============================================================================


def build_chord(
    root: str,
    chord_type: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build a chord from a root note and chord type.

    Args:
        root: Root note of the chord (e.g., "c", "f", "b").
        chord_type: Type of chord (e.g., "major", "minor7", "diminished").
        octave: Octave for the root note.
        duration: Duration for the chord.
        inversion: Chord inversion (0 = root position, 1 = first inversion, etc.).

    Returns:
        A Chord instance.

    Examples:
        >>> build_chord("c", "major")  # C major: C E G
        >>> build_chord("a", "minor7", duration=2)  # A minor 7
        >>> build_chord("g", "dominant7", inversion=1)  # G7 first inversion
    """
    if chord_type not in CHORD_INTERVALS:
        available = ", ".join(sorted(CHORD_INTERVALS.keys()))
        raise ValueError(f"Unknown chord type: {chord_type}. Available: {available}")

    # Parse root note
    if len(root) > 1 and root[1] in "+-":
        base_pitch = root[0].lower()
        root_acc = root[1]
        root_offset = PITCH_TO_OFFSET[base_pitch]
        if root_acc == "+":
            root_offset += 1
        elif root_acc == "-":
            root_offset -= 1
        root_offset = root_offset % 12
    else:
        base_pitch = root.lower()
        root_offset = PITCH_TO_OFFSET[base_pitch]
        root_acc = None

    intervals = list(CHORD_INTERVALS[chord_type])

    # Apply inversion by rotating intervals and adjusting octaves
    if inversion > 0:
        inversion = inversion % len(intervals)
        # Move lower notes up an octave
        for i in range(inversion):
            intervals[i] += 12
        # Sort to maintain ascending order
        intervals.sort()

    # Build notes
    notes = []
    for interval in intervals:
        pitch_offset = (root_offset + interval) % 12
        octave_offset = (root_offset + interval) // 12
        pitch_name, accidental = OFFSET_TO_PITCH[pitch_offset]
        notes.append(
            note(
                pitch_name,
                octave=octave + octave_offset,
                accidental=accidental,
                duration=None,  # Chord duration is set on the Chord itself
            )
        )

    return Chord(notes=tuple(notes), duration=duration)


# =============================================================================
# Triad Constructors
# =============================================================================


def major(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build a major triad.

    Args:
        root: Root note.
        octave: Octave for root.
        duration: Chord duration.
        inversion: Chord inversion.

    Returns:
        Major triad chord.

    Examples:
        >>> major("c")  # C E G
        >>> major("g", duration=2)
    """
    return build_chord(
        root, "major", octave=octave, duration=duration, inversion=inversion
    )


def minor(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build a minor triad.

    Examples:
        >>> minor("a")  # A C E
        >>> minor("d", inversion=1)  # First inversion
    """
    return build_chord(
        root, "minor", octave=octave, duration=duration, inversion=inversion
    )


def dim(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build a diminished triad.

    Examples:
        >>> dim("b")  # B D F
    """
    return build_chord(
        root, "diminished", octave=octave, duration=duration, inversion=inversion
    )


def aug(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build an augmented triad.

    Examples:
        >>> aug("c")  # C E G#
    """
    return build_chord(
        root, "augmented", octave=octave, duration=duration, inversion=inversion
    )


def sus2(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
) -> Chord:
    """Build a sus2 chord.

    Examples:
        >>> sus2("c")  # C D G
    """
    return build_chord(root, "sus2", octave=octave, duration=duration)


def sus4(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
) -> Chord:
    """Build a sus4 chord.

    Examples:
        >>> sus4("c")  # C F G
    """
    return build_chord(root, "sus4", octave=octave, duration=duration)


# =============================================================================
# Seventh Chord Constructors
# =============================================================================


def maj7(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build a major seventh chord.

    Examples:
        >>> maj7("c")  # C E G B
    """
    return build_chord(
        root, "major7", octave=octave, duration=duration, inversion=inversion
    )


def min7(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build a minor seventh chord.

    Examples:
        >>> min7("a")  # A C E G
    """
    return build_chord(
        root, "minor7", octave=octave, duration=duration, inversion=inversion
    )


def dom7(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build a dominant seventh chord.

    Examples:
        >>> dom7("g")  # G B D F
    """
    return build_chord(
        root, "dominant7", octave=octave, duration=duration, inversion=inversion
    )


def dim7(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build a fully diminished seventh chord.

    Examples:
        >>> dim7("b")  # B D F Ab
    """
    return build_chord(
        root, "diminished7", octave=octave, duration=duration, inversion=inversion
    )


def half_dim7(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build a half-diminished seventh chord (minor 7 flat 5).

    Examples:
        >>> half_dim7("b")  # B D F A
    """
    return build_chord(
        root, "half-diminished7", octave=octave, duration=duration, inversion=inversion
    )


def min_maj7(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build a minor-major seventh chord.

    Examples:
        >>> min_maj7("c")  # C Eb G B
    """
    return build_chord(
        root, "minor-major7", octave=octave, duration=duration, inversion=inversion
    )


def aug7(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
    inversion: int = 0,
) -> Chord:
    """Build an augmented seventh chord.

    Examples:
        >>> aug7("c")  # C E G# Bb
    """
    return build_chord(
        root, "augmented7", octave=octave, duration=duration, inversion=inversion
    )


# =============================================================================
# Sixth Chord Constructors
# =============================================================================


def maj6(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
) -> Chord:
    """Build a major sixth chord.

    Examples:
        >>> maj6("c")  # C E G A
    """
    return build_chord(root, "major6", octave=octave, duration=duration)


def min6(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
) -> Chord:
    """Build a minor sixth chord.

    Examples:
        >>> min6("a")  # A C E F#
    """
    return build_chord(root, "minor6", octave=octave, duration=duration)


# =============================================================================
# Extended Chord Constructors
# =============================================================================


def dom9(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
) -> Chord:
    """Build a dominant ninth chord.

    Examples:
        >>> dom9("g")  # G B D F A
    """
    return build_chord(root, "dominant9", octave=octave, duration=duration)


def maj9(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
) -> Chord:
    """Build a major ninth chord.

    Examples:
        >>> maj9("c")  # C E G B D
    """
    return build_chord(root, "major9", octave=octave, duration=duration)


def min9(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
) -> Chord:
    """Build a minor ninth chord.

    Examples:
        >>> min9("a")  # A C E G B
    """
    return build_chord(root, "minor9", octave=octave, duration=duration)


def add9(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
) -> Chord:
    """Build an add9 chord (major triad plus 9th, no 7th).

    Examples:
        >>> add9("c")  # C E G D
    """
    return build_chord(root, "add9", octave=octave, duration=duration)


def power(
    root: str,
    *,
    octave: int = 4,
    duration: int | None = None,
) -> Chord:
    """Build a power chord (root and fifth only).

    Examples:
        >>> power("e")  # E B
    """
    return build_chord(root, "power", octave=octave, duration=duration)


# =============================================================================
# Chord Utilities
# =============================================================================


def arpeggiate(
    chord: Chord,
    pattern: list[int] | None = None,
    *,
    duration: int | None = None,
) -> list[Note]:
    """Arpeggiate a chord into individual notes.

    Args:
        chord: The chord to arpeggiate.
        pattern: List of indices into the chord notes (0-based).
            If None, plays notes in order.
        duration: Duration for each note.

    Returns:
        List of notes forming the arpeggio.

    Examples:
        >>> c_maj = major("c")
        >>> arpeggiate(c_maj, [0, 1, 2, 1])  # C E G E
        >>> arpeggiate(c_maj, duration=16)  # C E G as 16th notes
    """
    notes = list(chord.notes)

    if pattern is None:
        pattern = list(range(len(notes)))

    result = []
    for idx in pattern:
        n = notes[idx % len(notes)]
        result.append(
            note(
                n.pitch,
                duration=duration if duration else n.duration,
                octave=n.octave,
                accidental=n.accidental,
            )
        )

    return result


def invert(chord: Chord, inversion: int) -> Chord:
    """Return an inverted version of a chord.

    Args:
        chord: The chord to invert.
        inversion: Inversion number (1 = first, 2 = second, etc.).

    Returns:
        Inverted chord.

    Examples:
        >>> c_maj = major("c")
        >>> invert(c_maj, 1)  # First inversion: E G C
    """
    notes = list(chord.notes)
    n = len(notes)

    if inversion <= 0:
        return chord

    inversion = inversion % n

    # Move lower notes up an octave
    new_notes = []
    for i, nt in enumerate(notes):
        if i < inversion:
            new_octave = (nt.octave or 4) + 1
            new_notes.append(
                note(
                    nt.pitch,
                    duration=nt.duration,
                    octave=new_octave,
                    accidental=nt.accidental,
                )
            )
        else:
            new_notes.append(nt)

    # Sort by pitch to maintain ascending order
    new_notes.sort(key=lambda x: x.midi_pitch)

    return Chord(notes=tuple(new_notes), duration=chord.duration)


def voicing(
    chord: Chord,
    octaves: list[int],
) -> Chord:
    """Apply specific octave voicing to a chord.

    Args:
        chord: The chord to voice.
        octaves: List of octaves for each note (must match chord size).

    Returns:
        Chord with new voicing.

    Examples:
        >>> c_maj = major("c")
        >>> voicing(c_maj, [3, 4, 5])  # C3 E4 G5 (spread voicing)
    """
    notes = list(chord.notes)

    if len(octaves) != len(notes):
        raise ValueError(f"octaves list must have {len(notes)} elements")

    new_notes = []
    for nt, oct in zip(notes, octaves):
        new_notes.append(
            note(
                nt.pitch,
                duration=nt.duration,
                octave=oct,
                accidental=nt.accidental,
            )
        )

    return Chord(notes=tuple(new_notes), duration=chord.duration)


def list_chord_types() -> list[str]:
    """Get a list of all available chord types.

    Returns:
        Sorted list of chord type names.

    Examples:
        >>> "major7" in list_chord_types()
        True
    """
    return sorted(CHORD_INTERVALS.keys())
