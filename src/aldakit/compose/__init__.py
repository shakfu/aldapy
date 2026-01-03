"""Compose module for programmatic music creation.

This module provides domain objects for building music programmatically,
generating AST nodes directly without parsing text.

Examples:
    >>> from aldakit.compose import note, rest, chord, seq, part, tempo
    >>> from aldakit import Score
    >>>
    >>> score = Score.from_elements(
    ...     part("piano"),
    ...     tempo(120),
    ...     note("c", duration=4),
    ...     note("d"),
    ...     note("e"),
    ... )
    >>> score.play()
"""

from .base import ComposeElement
from .core import (
    Note,
    Rest,
    Chord,
    Seq,
    Repeat,
    note,
    rest,
    chord,
    seq,
)
from .part import Part, part
from .attributes import (
    Tempo,
    Volume,
    Quant,
    Panning,
    OctaveSet,
    OctaveUp,
    OctaveDown,
    Dynamic,
    tempo,
    volume,
    vol,
    quant,
    panning,
    octave,
    octave_up,
    octave_down,
    pp,
    p,
    mp,
    mf,
    f,
    ff,
)
from .transform import (
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

__all__ = [
    # Base
    "ComposeElement",
    # Core classes
    "Note",
    "Rest",
    "Chord",
    "Seq",
    "Repeat",
    # Core factory functions
    "note",
    "rest",
    "chord",
    "seq",
    # Part
    "Part",
    "part",
    # Attribute classes
    "Tempo",
    "Volume",
    "Quant",
    "Panning",
    "OctaveSet",
    "OctaveUp",
    "OctaveDown",
    "Dynamic",
    # Attribute factory functions
    "tempo",
    "volume",
    "vol",
    "quant",
    "panning",
    "octave",
    "octave_up",
    "octave_down",
    # Dynamics
    "pp",
    "p",
    "mp",
    "mf",
    "f",
    "ff",
    # Pitch transformers
    "transpose",
    "invert",
    "reverse",
    "shuffle",
    "retrograde_inversion",
    # Structural transformers
    "augment",
    "diminish",
    "fragment",
    "loop",
    "interleave",
    "rotate",
    "take_every",
    "split",
    "concat",
    # Helpers
    "pipe",
    "identity",
]
