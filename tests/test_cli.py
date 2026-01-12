"""CLI regression tests."""

import builtins

import pytest

from aldakit import __version__
from aldakit.cli import (
    create_parser,
    stdin_mode,
    _resolve_port_specifier,
    _resolve_output_port,
    _resolve_input_port,
)


def test_cli_version_matches_package(capsys):
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])

    out = capsys.readouterr().out.strip()
    assert out.endswith(__version__)


def test_stdin_mode_uses_backend_context(monkeypatch):
    entered = False
    exited = False

    class DummyBackend:
        def __init__(self, port_name=None, virtual_port_name=None):
            pass

        def __enter__(self):
            nonlocal entered
            entered = True
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            nonlocal exited
            exited = True

        def play(self, sequence):
            return None

        def is_playing(self):
            return False

    def fake_input(prompt: str | None = None):
        raise EOFError

    monkeypatch.setattr("aldakit.cli.LibremidiBackend", DummyBackend)
    monkeypatch.setattr(builtins, "input", fake_input)

    assert (
        stdin_mode(port_name=None, verbose=False, virtual_port_name="AldakitMIDI") == 0
    )
    assert entered and exited


class TestResolvePortSpecifier:
    """Tests for _resolve_port_specifier."""

    def test_none_returns_none_with_multiple_ports(self):
        port, ok = _resolve_port_specifier(None, ["PortA", "PortB"], "output")
        assert port is None
        assert ok is True

    def test_none_returns_none_with_no_ports(self):
        port, ok = _resolve_port_specifier(None, [], "output")
        assert port is None
        assert ok is True

    def test_index_resolves_to_name(self):
        port, ok = _resolve_port_specifier("0", ["FluidSynth", "IAC"], "output")
        assert port == "FluidSynth"
        assert ok is True

    def test_index_second_port(self):
        port, ok = _resolve_port_specifier("1", ["FluidSynth", "IAC"], "output")
        assert port == "IAC"
        assert ok is True

    def test_index_out_of_range_fails(self, capsys):
        port, ok = _resolve_port_specifier("5", ["A", "B"], "output")
        assert port is None
        assert ok is False
        err = capsys.readouterr().err
        assert "out of range" in err

    def test_name_passed_through(self):
        port, ok = _resolve_port_specifier("FluidSynth", ["FluidSynth"], "output")
        assert port == "FluidSynth"
        assert ok is True

    def test_partial_name_passed_through(self):
        # Backend handles partial matching, so we just pass it through
        port, ok = _resolve_port_specifier("Fluid", ["FluidSynth"], "output")
        assert port == "Fluid"
        assert ok is True


class TestResolveOutputPort:
    """Tests for _resolve_output_port auto-selection."""

    def test_auto_selects_single_port(self, monkeypatch):
        class DummyBackend:
            def list_output_ports(self):
                return ["OnlyPort"]

        monkeypatch.setattr("aldakit.cli.LibremidiBackend", DummyBackend)
        port, ok = _resolve_output_port(None)
        assert port == "OnlyPort"
        assert ok is True

    def test_no_auto_select_with_multiple_ports(self, monkeypatch):
        class DummyBackend:
            def list_output_ports(self):
                return ["PortA", "PortB"]

        monkeypatch.setattr("aldakit.cli.LibremidiBackend", DummyBackend)
        port, ok = _resolve_output_port(None)
        assert port is None
        assert ok is True

    def test_no_auto_select_with_no_ports(self, monkeypatch):
        class DummyBackend:
            def list_output_ports(self):
                return []

        monkeypatch.setattr("aldakit.cli.LibremidiBackend", DummyBackend)
        port, ok = _resolve_output_port(None)
        assert port is None
        assert ok is True


class TestResolveInputPort:
    """Tests for _resolve_input_port auto-selection."""

    def test_auto_selects_single_port(self, monkeypatch):
        monkeypatch.setattr(
            "aldakit.midi.transcriber.list_input_ports", lambda: ["OnlyInputPort"]
        )
        port, ok = _resolve_input_port(None)
        assert port == "OnlyInputPort"
        assert ok is True

    def test_no_auto_select_with_multiple_ports(self, monkeypatch):
        monkeypatch.setattr(
            "aldakit.midi.transcriber.list_input_ports", lambda: ["InputA", "InputB"]
        )
        port, ok = _resolve_input_port(None)
        assert port is None
        assert ok is True
