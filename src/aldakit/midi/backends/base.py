"""Abstract base class for MIDI backends."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..types import MidiSequence


class MidiBackend(ABC):
    """Abstract base class for MIDI output backends.

    Backends may support concurrent playback mode, where multiple
    sequences can play simultaneously (up to a backend-specific limit).
    """

    @abstractmethod
    def play(self, sequence: MidiSequence) -> int | None:
        """Play a MIDI sequence in realtime.

        In concurrent mode, the sequence starts playing immediately
        alongside any currently playing sequences.

        In sequential mode, waits for current playback to complete first.

        Args:
            sequence: The MIDI sequence to play.

        Returns:
            A slot ID if playback started (for backends that support concurrent
            playback), or None if playback could not start.
        """
        pass

    @abstractmethod
    def save(self, sequence: MidiSequence, path: Path | str) -> None:
        """Save a MIDI sequence to a file.

        Args:
            sequence: The MIDI sequence to save.
            path: The output file path.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop all currently playing sequences."""
        pass

    def is_playing(self) -> bool:
        """Check if any sequence is currently playing.

        Returns:
            True if playing, False otherwise.
        """
        return False

    def wait(self, poll_interval: float = 0.05) -> None:
        """Block until all playback completes.

        Args:
            poll_interval: Seconds between status checks.
        """
        import time

        while self.is_playing():
            time.sleep(poll_interval)

    @property
    def concurrent_mode(self) -> bool:
        """Whether concurrent playback is enabled.

        When True, multiple sequences can play simultaneously.
        When False, new playback waits for current playback to complete.

        Not all backends support concurrent playback.
        """
        return False

    @concurrent_mode.setter
    def concurrent_mode(self, value: bool) -> None:
        """Set concurrent playback mode."""
        pass  # Override in subclasses that support concurrent mode
