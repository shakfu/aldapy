"""Async playback system for concurrent MIDI playback.

This module provides a slot-based async playback system that allows
multiple MIDI sequences to play simultaneously, similar to alda-midi's
libuv-based concurrent playback.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from ...constants import (
    MAX_PLAYBACK_SLOTS,
    PLAYBACK_SLEEP_THRESHOLD,
    POLL_INTERVAL_DEFAULT,
    SEQUENTIAL_MODE_SLEEP,
    THREAD_JOIN_TIMEOUT,
)

if TYPE_CHECKING:
    from ..types import MidiSequence


@dataclass
class PlaybackEvent:
    """A single playback event."""

    time: float  # Absolute time in seconds
    event_type: str  # "note_on", "note_off", "program", "control"
    args: tuple  # Arguments for the event


@dataclass
class PlaybackSlot:
    """A single concurrent playback unit.

    Each slot can independently play a MIDI sequence while other
    slots continue playing.
    """

    slot_id: int
    active: bool = False
    events: list[PlaybackEvent] = field(default_factory=list)
    event_index: int = 0
    stop_requested: bool = False
    thread: threading.Thread | None = None
    start_time: float = 0.0


class AsyncPlaybackManager:
    """Manages concurrent MIDI playback with multiple slots.

    This class implements a slot-based playback system that allows
    up to MAX_PLAYBACK_SLOTS concurrent sequences to play simultaneously.

    Modes:
        - Concurrent mode (default): New playback starts immediately,
          layering on top of any currently playing sequences.
        - Sequential mode: New playback waits for all previous
          playback to complete before starting.

    Example:
        >>> manager = AsyncPlaybackManager(send_note_on, send_note_off, ...)
        >>> manager.play(sequence1)  # Starts immediately
        >>> manager.play(sequence2)  # Layers on top of sequence1
        >>> manager.stop()  # Stops all playback
    """

    def __init__(
        self,
        send_note_on: Callable[[int, int, int], None],
        send_note_off: Callable[[int, int], None],
        send_program_change: Callable[[int, int], None],
        send_control_change: Callable[[int, int, int], None],
        send_all_notes_off: Callable[[], None] | None = None,
    ):
        """Initialize the async playback manager.

        Args:
            send_note_on: Function to send note on (channel, note, velocity)
            send_note_off: Function to send note off (channel, note)
            send_program_change: Function to send program change (channel, program)
            send_control_change: Function to send CC (channel, control, value)
            send_all_notes_off: Optional function to silence all notes
        """
        self._send_note_on = send_note_on
        self._send_note_off = send_note_off
        self._send_program_change = send_program_change
        self._send_control_change = send_control_change
        self._send_all_notes_off = send_all_notes_off

        self._slots = [PlaybackSlot(slot_id=i) for i in range(MAX_PLAYBACK_SLOTS)]
        self._lock = threading.Lock()
        self._concurrent_mode = True
        self._shutdown = False

    @property
    def concurrent_mode(self) -> bool:
        """Whether concurrent playback is enabled."""
        return self._concurrent_mode

    @concurrent_mode.setter
    def concurrent_mode(self, value: bool) -> None:
        """Set concurrent playback mode."""
        self._concurrent_mode = value

    @property
    def active_count(self) -> int:
        """Number of currently active playback slots."""
        with self._lock:
            return sum(1 for slot in self._slots if slot.active)

    def is_playing(self) -> bool:
        """Check if any slot is currently playing."""
        return self.active_count > 0

    def _find_free_slot(self) -> PlaybackSlot | None:
        """Find a free playback slot."""
        with self._lock:
            for slot in self._slots:
                if not slot.active:
                    return slot
        return None

    def _build_events(self, sequence: MidiSequence) -> list[PlaybackEvent]:
        """Build a sorted list of playback events from a MIDI sequence."""
        events: list[PlaybackEvent] = []

        # Add program changes
        for pc in sequence.program_changes:
            events.append(
                PlaybackEvent(
                    time=pc.time, event_type="program", args=(pc.channel, pc.program)
                )
            )

        # Add control changes
        for cc in sequence.control_changes:
            events.append(
                PlaybackEvent(
                    time=cc.time,
                    event_type="control",
                    args=(cc.channel, cc.control, cc.value),
                )
            )

        # Add note on/off events
        for note in sequence.notes:
            events.append(
                PlaybackEvent(
                    time=note.start_time,
                    event_type="note_on",
                    args=(note.channel, note.pitch, note.velocity),
                )
            )
            events.append(
                PlaybackEvent(
                    time=note.start_time + note.duration,
                    event_type="note_off",
                    args=(note.channel, note.pitch),
                )
            )

        # Sort by time, with note_off before note_on at same time to prevent stuck notes
        events.sort(key=lambda e: (e.time, e.event_type != "note_off"))
        return events

    def _play_slot(self, slot: PlaybackSlot) -> None:
        """Play events in a slot (runs in a thread)."""
        try:
            slot.start_time = time.perf_counter()

            for i, event in enumerate(slot.events):
                if slot.stop_requested or self._shutdown:
                    break

                slot.event_index = i

                # Wait until event time
                target_time = slot.start_time + event.time
                while time.perf_counter() < target_time:
                    if slot.stop_requested or self._shutdown:
                        break
                    remaining = target_time - time.perf_counter()
                    if remaining > PLAYBACK_SLEEP_THRESHOLD:
                        time.sleep(PLAYBACK_SLEEP_THRESHOLD)
                    elif remaining > 0:
                        time.sleep(remaining)
                    else:
                        break

                if slot.stop_requested or self._shutdown:
                    break

                # Send the event
                if event.event_type == "note_on":
                    self._send_note_on(*event.args)
                elif event.event_type == "note_off":
                    self._send_note_off(*event.args)
                elif event.event_type == "program":
                    self._send_program_change(*event.args)
                elif event.event_type == "control":
                    self._send_control_change(*event.args)

        finally:
            with self._lock:
                slot.active = False
                slot.events = []
                slot.event_index = 0
                slot.stop_requested = False

    def play(self, sequence: MidiSequence) -> int | None:
        """Start playing a MIDI sequence asynchronously.

        In concurrent mode, starts immediately alongside any current playback.
        In sequential mode, waits for all current playback to complete first.

        Args:
            sequence: The MIDI sequence to play.

        Returns:
            The slot ID if playback started, or None if all slots are busy.
        """
        if self._shutdown:
            return None

        # In sequential mode, wait for all playback to complete
        if not self._concurrent_mode:
            while self.is_playing():
                time.sleep(SEQUENTIAL_MODE_SLEEP)

        # Find a free slot
        slot = self._find_free_slot()
        if slot is None:
            return None  # All slots busy

        # Build events and start playback
        events = self._build_events(sequence)
        if not events:
            return None

        with self._lock:
            slot.active = True
            slot.events = events
            slot.event_index = 0
            slot.stop_requested = False

        slot.thread = threading.Thread(
            target=self._play_slot, args=(slot,), daemon=True
        )
        slot.thread.start()

        return slot.slot_id

    def stop(self) -> None:
        """Stop all currently playing slots."""
        # Signal all slots to stop
        with self._lock:
            for slot in self._slots:
                if slot.active:
                    slot.stop_requested = True

        # Wait for all threads to finish (with timeout)
        for slot in self._slots:
            if slot.thread and slot.thread.is_alive():
                slot.thread.join(timeout=THREAD_JOIN_TIMEOUT)

        # Send all notes off
        if self._send_all_notes_off:
            self._send_all_notes_off()

    def stop_slot(self, slot_id: int) -> None:
        """Stop a specific playback slot.

        Args:
            slot_id: The slot ID to stop (0 to MAX_PLAYBACK_SLOTS-1).
        """
        if 0 <= slot_id < MAX_PLAYBACK_SLOTS:
            slot = self._slots[slot_id]
            with self._lock:
                if slot.active:
                    slot.stop_requested = True

            if slot.thread and slot.thread.is_alive():
                slot.thread.join(timeout=THREAD_JOIN_TIMEOUT)

    def wait(self, poll_interval: float = POLL_INTERVAL_DEFAULT) -> None:
        """Block until all playback completes.

        Args:
            poll_interval: Seconds between status checks.
        """
        while self.is_playing():
            time.sleep(poll_interval)

    def shutdown(self) -> None:
        """Shutdown the playback manager, stopping all playback."""
        self._shutdown = True
        self.stop()

    def get_slot_info(self) -> list[dict]:
        """Get information about all slots.

        Returns:
            List of dicts with slot status information.
        """
        info = []
        with self._lock:
            for slot in self._slots:
                info.append(
                    {
                        "slot_id": slot.slot_id,
                        "active": slot.active,
                        "event_count": len(slot.events),
                        "event_index": slot.event_index,
                        "progress": (
                            slot.event_index / len(slot.events) if slot.events else 0.0
                        ),
                    }
                )
        return info
