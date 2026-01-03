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
    Cram,
    Voice,
    VoiceGroup,
    Variable,
    VariableRef,
    Marker,
    AtMarker,
    note,
    rest,
    chord,
    seq,
    cram,
    voice,
    voice_group,
    var,
    var_ref,
    marker,
    at_marker,
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
from .generate import (
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
from .scales import (
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
    SCALE_INTERVALS,
)
from .chords import (
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
    min_maj7,
    aug7,
    maj6,
    min6,
    dom9,
    maj9,
    min9,
    add9,
    power,
    arpeggiate,
    invert as invert_chord,
    voicing,
    list_chord_types,
    CHORD_INTERVALS,
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
    "Cram",
    "Voice",
    "VoiceGroup",
    "Variable",
    "VariableRef",
    "Marker",
    "AtMarker",
    # Core factory functions
    "note",
    "rest",
    "chord",
    "seq",
    "cram",
    "voice",
    "voice_group",
    "var",
    "var_ref",
    "marker",
    "at_marker",
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
    # Random selection
    "random_note",
    "random_choice",
    "weighted_choice",
    # Random walks
    "random_walk",
    "drunk_walk",
    # Rhythmic generators
    "euclidean",
    "probability_seq",
    "rest_probability",
    # Markov chains
    "MarkovChain",
    "markov_chain",
    "learn_markov",
    # L-Systems
    "lsystem",
    # Cellular automata
    "cellular_automaton",
    # Shift registers
    "shift_register",
    "turing_machine",
    # Scales
    "scale",
    "scale_notes",
    "scale_degree",
    "mode",
    "relative_minor",
    "relative_major",
    "parallel_minor",
    "parallel_major",
    "transpose_scale",
    "interval_name",
    "list_scales",
    "SCALE_INTERVALS",
    # Chords
    "build_chord",
    "major",
    "minor",
    "dim",
    "aug",
    "sus2",
    "sus4",
    "maj7",
    "min7",
    "dom7",
    "dim7",
    "half_dim7",
    "min_maj7",
    "aug7",
    "maj6",
    "min6",
    "dom9",
    "maj9",
    "min9",
    "add9",
    "power",
    "arpeggiate",
    "invert_chord",
    "voicing",
    "list_chord_types",
    "CHORD_INTERVALS",
]
