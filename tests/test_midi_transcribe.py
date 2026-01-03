"""Tests for MIDI transcription functionality."""

from aldakit.midi.transcriber import (
    TranscribeSession,
    PendingNote,
    RecordedNote,
    list_input_ports,
)
from aldakit.compose.core import Note, Rest


# =============================================================================
# TranscribeSession Unit Tests
# =============================================================================


class TestTranscribeSession:
    """Tests for TranscribeSession internal logic."""

    def test_init_defaults(self):
        """Session initializes with correct defaults."""
        session = TranscribeSession()
        assert session.port_name is None
        assert session.quantize_grid == 0.25
        assert session.default_tempo == 120.0
        assert not session._running

    def test_seconds_to_duration_quarter(self):
        """Quarter note at 120 BPM = 0.5 seconds."""
        session = TranscribeSession(default_tempo=120.0)
        # At 120 BPM, one beat = 0.5s, so 0.5s = 1 beat = quarter note
        duration = session._seconds_to_duration(0.5)
        assert duration == 4  # quarter note

    def test_seconds_to_duration_eighth(self):
        """Eighth note at 120 BPM = 0.25 seconds."""
        session = TranscribeSession(default_tempo=120.0)
        # 0.25s = 0.5 beats = eighth note
        duration = session._seconds_to_duration(0.25)
        assert duration == 8  # eighth note

    def test_seconds_to_duration_half(self):
        """Half note at 120 BPM = 1.0 seconds."""
        session = TranscribeSession(default_tempo=120.0)
        # 1.0s = 2 beats = half note
        duration = session._seconds_to_duration(1.0)
        assert duration == 2  # half note

    def test_seconds_to_duration_whole(self):
        """Whole note at 120 BPM = 2.0 seconds."""
        session = TranscribeSession(default_tempo=120.0)
        # 2.0s = 4 beats = whole note
        duration = session._seconds_to_duration(2.0)
        assert duration == 1  # whole note

    def test_seconds_to_duration_with_quantize(self):
        """Duration quantizes to grid."""
        session = TranscribeSession(default_tempo=120.0, quantize_grid=0.25)
        # 0.3s is close to 0.25s (eighth note)
        duration = session._seconds_to_duration(0.3)
        assert duration == 8  # eighth note

    def test_notes_to_seq_empty(self):
        """Empty notes produce empty Seq."""
        session = TranscribeSession()
        session._recorded_notes = []
        seq = session._notes_to_seq()
        assert len(seq.elements) == 0

    def test_notes_to_seq_single_note(self):
        """Single note converts correctly."""
        session = TranscribeSession(default_tempo=120.0)
        session._recorded_notes = [
            RecordedNote(pitch=60, velocity=100, start_time=0.0, duration=0.5)
        ]
        seq = session._notes_to_seq()
        assert len(seq.elements) == 1
        note = seq.elements[0]
        assert isinstance(note, Note)
        assert note.pitch == "c"
        assert note.octave == 4
        assert note.duration == 4  # quarter note

    def test_notes_to_seq_multiple_notes(self):
        """Multiple notes convert correctly."""
        session = TranscribeSession(default_tempo=120.0)
        session._recorded_notes = [
            RecordedNote(pitch=60, velocity=100, start_time=0.0, duration=0.5),
            RecordedNote(pitch=62, velocity=100, start_time=0.5, duration=0.5),
            RecordedNote(pitch=64, velocity=100, start_time=1.0, duration=0.5),
        ]
        seq = session._notes_to_seq()
        assert len(seq.elements) == 3
        assert all(isinstance(e, Note) for e in seq.elements)
        assert seq.elements[0].pitch == "c"
        assert seq.elements[1].pitch == "d"
        assert seq.elements[2].pitch == "e"

    def test_notes_to_seq_with_gap_inserts_rest(self):
        """Gap between notes inserts a rest."""
        session = TranscribeSession(default_tempo=120.0)
        session._recorded_notes = [
            RecordedNote(pitch=60, velocity=100, start_time=0.0, duration=0.5),
            # 0.5 second gap (one beat at 120 BPM)
            RecordedNote(pitch=62, velocity=100, start_time=1.5, duration=0.5),
        ]
        seq = session._notes_to_seq()
        # Should have: note, rest, note
        assert len(seq.elements) == 3
        assert isinstance(seq.elements[0], Note)
        assert isinstance(seq.elements[1], Rest)
        assert isinstance(seq.elements[2], Note)

    def test_notes_to_seq_accidentals(self):
        """Sharps are correctly detected."""
        session = TranscribeSession(default_tempo=120.0)
        session._recorded_notes = [
            RecordedNote(pitch=61, velocity=100, start_time=0.0, duration=0.5),  # C#
        ]
        seq = session._notes_to_seq()
        assert len(seq.elements) == 1
        note = seq.elements[0]
        assert note.pitch == "c"
        assert note.accidental == "+"

    def test_note_on_off_tracking(self):
        """Note on/off events are tracked correctly."""
        session = TranscribeSession()
        session._running = True
        session._start_time = 0.0

        # Note on
        session._note_on(60, 100, 0.0)
        assert 60 in session._pending_notes
        assert session._pending_notes[60].pitch == 60
        assert session._pending_notes[60].velocity == 100

        # Note off
        session._note_off(60, 0.5)
        assert 60 not in session._pending_notes
        assert len(session._recorded_notes) == 1
        assert session._recorded_notes[0].pitch == 60
        assert session._recorded_notes[0].duration == 0.5

    def test_note_on_callback(self):
        """Note on callback is invoked."""
        session = TranscribeSession()
        session._running = True

        notes_received = []

        def callback(pitch, velocity, is_on):
            notes_received.append((pitch, velocity, is_on))

        session.on_note(callback)

        session._note_on(60, 100, 0.0)
        session._note_off(60, 0.5)

        assert len(notes_received) == 2
        assert notes_received[0] == (60, 100, True)
        assert notes_received[1] == (60, 0, False)


class TestListInputPorts:
    """Tests for list_input_ports function."""

    def test_returns_list(self):
        """Function returns a list."""
        ports = list_input_ports()
        assert isinstance(ports, list)
        # Note: May be empty if no MIDI devices connected


class TestPendingNote:
    """Tests for PendingNote dataclass."""

    def test_creation(self):
        """PendingNote can be created."""
        note = PendingNote(pitch=60, velocity=100, start_time=0.5)
        assert note.pitch == 60
        assert note.velocity == 100
        assert note.start_time == 0.5


class TestRecordedNote:
    """Tests for RecordedNote dataclass."""

    def test_creation(self):
        """RecordedNote can be created."""
        note = RecordedNote(pitch=60, velocity=100, start_time=0.5, duration=1.0)
        assert note.pitch == 60
        assert note.velocity == 100
        assert note.start_time == 0.5
        assert note.duration == 1.0


# =============================================================================
# MidiIn Binding Tests
# =============================================================================


class TestMidiInBindings:
    """Tests for MidiIn C++ bindings."""

    def test_midi_in_creation(self):
        """MidiIn can be instantiated."""
        from aldakit._libremidi import MidiIn

        midi_in = MidiIn()
        assert midi_in is not None

    def test_midi_in_poll_empty(self):
        """Poll returns empty list when no messages."""
        from aldakit._libremidi import MidiIn

        midi_in = MidiIn()
        messages = midi_in.poll()
        assert isinstance(messages, list)
        assert len(messages) == 0

    def test_midi_in_has_messages(self):
        """has_messages returns False when empty."""
        from aldakit._libremidi import MidiIn

        midi_in = MidiIn()
        assert not midi_in.has_messages()

    def test_midi_in_is_port_open(self):
        """is_port_open returns False before opening."""
        from aldakit._libremidi import MidiIn

        midi_in = MidiIn()
        assert not midi_in.is_port_open()


class TestMidiMessage:
    """Tests for MidiMessage binding."""

    def test_midi_message_creation(self):
        """MidiMessage can be instantiated."""
        from aldakit._libremidi import MidiMessage

        msg = MidiMessage()
        assert msg is not None
        assert hasattr(msg, "bytes")
        assert hasattr(msg, "timestamp")
