"""MIDI backend implementations."""

from .base import MidiBackend
from .libremidi_backend import LibremidiBackend

# TsfBackend is optional (requires _tsf native module and SoundFont)
try:
    from .tsf_backend import TsfBackend, find_soundfont, list_soundfonts

    HAS_TSF = True
except ImportError:
    HAS_TSF = False
    TsfBackend = None  # type: ignore
    find_soundfont = None  # type: ignore
    list_soundfonts = None  # type: ignore

__all__ = [
    "MidiBackend",
    "LibremidiBackend",
    "TsfBackend",
    "HAS_TSF",
    "find_soundfont",
    "list_soundfonts",
]
