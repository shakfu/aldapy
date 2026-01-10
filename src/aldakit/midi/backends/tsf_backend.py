"""TinySoundFont backend for direct audio synthesis.

This backend renders MIDI to audio directly using SoundFont files,
without requiring an external synthesizer like FluidSynth.
"""

from __future__ import annotations

import time
from pathlib import Path

from .base import MidiBackend
from ..smf import write_midi_file
from ..types import MidiSequence

# Try to import the native module
try:
    from ... import _tsf  # type: ignore[attr-defined]

    HAS_TSF = True
except ImportError:
    HAS_TSF = False
    _tsf = None


def is_available() -> bool:
    """Check if the TinySoundFont backend is available."""
    return HAS_TSF


def find_soundfont() -> Path | None:
    """Search common locations for a General MIDI SoundFont.

    Returns:
        Path to a SoundFont file, or None if not found.
    """
    import os

    # Check environment variable first
    env_path = os.environ.get("ALDAKIT_SOUNDFONT")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    # Common SoundFont names (ordered by preference)
    soundfont_names = [
        "FluidR3_GM.sf2",
        "FluidR3_GS.sf2",
        "GeneralUser_GS.sf2",
        "TimGM6mb.sf2",
        "SGM-V2.01.sf2",
        "Arachno.sf2",
        "default.sf2",
    ]

    # Search paths (platform-dependent)
    search_paths: list[Path] = []

    # User locations (all platforms)
    home = Path.home()
    search_paths.extend(
        [
            home / "Music" / "sf2",
            home / "Music" / "SoundFonts",
            home / ".local" / "share" / "soundfonts",
            home / ".local" / "share" / "sounds" / "sf2",
        ]
    )

    # aldakit data directory
    search_paths.append(home / ".aldakit" / "soundfonts")

    # Linux system locations
    search_paths.extend(
        [
            Path("/usr/share/soundfonts"),
            Path("/usr/share/sounds/sf2"),
            Path("/usr/local/share/soundfonts"),
        ]
    )

    # macOS locations
    search_paths.extend(
        [
            Path("/Library/Audio/Sounds/Banks"),
            home / "Library" / "Audio" / "Sounds" / "Banks",
        ]
    )

    # Windows locations
    search_paths.extend(
        [
            Path("C:/soundfonts"),
            home / "Documents" / "SoundFonts",
        ]
    )

    # Search for specific names first
    for search_path in search_paths:
        if not search_path.exists():
            continue
        for name in soundfont_names:
            sf_path = search_path / name
            if sf_path.exists():
                return sf_path

    # Fall back to any .sf2 file
    for search_path in search_paths:
        if not search_path.exists():
            continue
        sf2_files = sorted(search_path.glob("*.sf2"))
        if sf2_files:
            return sf2_files[0]

    return None


def list_soundfonts() -> list[Path]:
    """List all SoundFont files found in common locations.

    Returns:
        List of paths to SoundFont files.
    """
    import os

    found: list[Path] = []
    seen: set[Path] = set()

    # Check environment variable
    env_path = os.environ.get("ALDAKIT_SOUNDFONT")
    if env_path:
        p = Path(env_path)
        if p.exists() and p not in seen:
            found.append(p)
            seen.add(p)

    # Search paths
    home = Path.home()
    search_paths = [
        home / "Music" / "sf2",
        home / "Music" / "SoundFonts",
        home / ".local" / "share" / "soundfonts",
        home / ".aldakit" / "soundfonts",
        Path("/usr/share/soundfonts"),
        Path("/usr/share/sounds/sf2"),
    ]

    for search_path in search_paths:
        if not search_path.exists():
            continue
        for sf_path in search_path.glob("*.sf2"):
            if sf_path not in seen:
                found.append(sf_path)
                seen.add(sf_path)

    return sorted(found)


class TsfBackend(MidiBackend):
    """MIDI backend using TinySoundFont for direct audio output.

    This backend synthesizes audio directly from MIDI events using a
    SoundFont file. No external synthesizer is required.

    Example:
        >>> backend = TsfBackend()  # Auto-finds SoundFont
        >>> score = Score("piano: c d e f g")
        >>> backend.play(score.midi)
        >>> while backend.is_playing():
        ...     time.sleep(0.1)

        >>> # Specify SoundFont explicitly
        >>> backend = TsfBackend(soundfont="/path/to/FluidR3_GM.sf2")

    Environment:
        ALDAKIT_SOUNDFONT: Path to default SoundFont file.
    """

    def __init__(
        self,
        soundfont: str | Path | None = None,
        gain: float = 1.0,
    ):
        """Initialize the TinySoundFont backend.

        Args:
            soundfont: Path to a SoundFont file (.sf2). If None, searches
                common locations for a GM SoundFont.
            gain: Global volume gain (0.0 - 2.0, default 1.0).

        Raises:
            RuntimeError: If TinySoundFont module is not available.
            FileNotFoundError: If no SoundFont is found.
        """
        if not HAS_TSF or _tsf is None:
            raise RuntimeError(
                "TinySoundFont backend not available. "
                "The _tsf native module was not built or failed to load."
            )

        self._player = _tsf.TsfPlayer()  # type: ignore[union-attr]
        self._soundfont_path: Path | None = None

        # Find SoundFont
        if soundfont is not None:
            sf_path = Path(soundfont)
        else:
            sf_path = find_soundfont()

        if sf_path is None:
            raise FileNotFoundError(
                "No SoundFont file found. Please either:\n"
                "  1. Set ALDAKIT_SOUNDFONT=/path/to/soundfont.sf2\n"
                "  2. Place a .sf2 file in ~/Music/sf2/\n"
                "  3. Pass soundfont='/path/to/file.sf2' to TsfBackend()"
            )

        if not sf_path.exists():
            raise FileNotFoundError(f"SoundFont file not found: {sf_path}")

        if not self._player.load_soundfont(str(sf_path)):
            raise RuntimeError(f"Failed to load SoundFont: {sf_path}")

        self._soundfont_path = sf_path
        self._player.set_gain(gain)

    @property
    def soundfont(self) -> Path | None:
        """The currently loaded SoundFont path."""
        return self._soundfont_path

    @property
    def preset_count(self) -> int:
        """Number of presets in the loaded SoundFont."""
        return self._player.preset_count()

    def preset_name(self, index: int) -> str:
        """Get the name of a preset by index."""
        return self._player.preset_name(index)

    def set_gain(self, gain: float) -> None:
        """Set global volume gain (0.0 - 2.0)."""
        self._player.set_gain(gain)

    def play(self, sequence: MidiSequence) -> int | None:
        """Play a MIDI sequence through the audio output.

        Note: TsfBackend does not currently support concurrent playback.
        Calling play() will stop any currently playing sequence.

        Args:
            sequence: The MIDI sequence to play.

        Returns:
            0 to indicate playback started (single slot).
        """
        self._player.clear_schedule()

        # Schedule program changes
        for pc in sequence.program_changes:
            self._player.schedule_program(pc.channel, pc.program, pc.time)

        # Schedule notes
        for note in sequence.notes:
            self._player.schedule_note(
                note.channel,
                note.pitch,
                note.velocity / 127.0,  # Convert to 0.0-1.0
                note.start_time,
                note.duration,
            )

        self._player.play()
        return 0

    def save(self, sequence: MidiSequence, path: Path | str) -> None:
        """Save a MIDI sequence to a file.

        Note: This saves as a standard MIDI file, not audio.

        Args:
            sequence: The MIDI sequence to save.
            path: Output file path.
        """
        write_midi_file(sequence, path)

    def stop(self) -> None:
        """Stop playback."""
        self._player.stop()

    def is_playing(self) -> bool:
        """Check if playback is in progress."""
        return self._player.is_playing()

    def current_time(self) -> float:
        """Get current playback position in seconds."""
        return self._player.current_time()

    def wait(self, poll_interval: float = 0.05) -> None:
        """Block until playback completes.

        Args:
            poll_interval: Seconds between status checks.
        """
        while self.is_playing():
            time.sleep(poll_interval)

    def __enter__(self) -> "TsfBackend":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.stop()
        return False

    def __repr__(self) -> str:
        sf = self._soundfont_path.name if self._soundfont_path else "None"
        return f"TsfBackend(soundfont={sf!r}, presets={self.preset_count})"
