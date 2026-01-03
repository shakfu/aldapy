"""High-level Score class for working with Alda music."""

from __future__ import annotations

import time
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .parser import parse
from .midi.generator import generate_midi
from .midi.backends import LibremidiBackend
from .ast_nodes import RootNode, EventSequenceNode

if TYPE_CHECKING:
    from .midi.types import MidiSequence
    from .compose.base import ComposeElement


class Score:
    """A unified score class for parsing, building, and playing music.

    The Score class provides a high-level interface for working with Alda music.
    It supports multiple construction methods:

    - From Alda source code: `Score("piano: c d e")` or `Score.from_source(...)`
    - From Alda file: `Score.from_file("song.alda")`
    - From compose elements: `Score.from_elements(part("piano"), note("c"), ...)`

    Examples:
        >>> # From source code
        >>> score = Score("piano: c d e f g")
        >>> score.play()

        >>> # From file
        >>> score = Score.from_file("song.alda")
        >>> score.save("output.mid")

        >>> # From compose elements
        >>> from aldakit.compose import part, note, tempo
        >>> score = Score.from_elements(
        ...     part("piano"),
        ...     tempo(120),
        ...     note("c", duration=4),
        ...     note("d"),
        ...     note("e"),
        ... )
        >>> score.play()

        >>> # Builder pattern
        >>> score = Score.from_elements(part("piano"))
        >>> score.add(note("c"), note("d"), note("e"))
        >>> score.play()
    """

    # Mode constants
    _MODE_SOURCE = "source"
    _MODE_ELEMENTS = "elements"

    def __init__(self, source: str, filename: str = "<input>") -> None:
        """Create a Score from Alda source code.

        Args:
            source: Alda source code string.
            filename: Optional filename for error messages.
        """
        self._mode = self._MODE_SOURCE
        self._source = source
        self._filename = filename
        self._elements: list[ComposeElement] = []

    @classmethod
    def from_source(cls, source: str, filename: str = "<input>") -> Score:
        """Create a Score from Alda source code.

        This is equivalent to calling Score(source, filename) directly.

        Args:
            source: Alda source code string.
            filename: Optional filename for error messages.

        Returns:
            A new Score instance.
        """
        return cls(source, filename)

    @classmethod
    def from_file(cls, path: str | Path) -> Score:
        """Create a Score from an Alda file.

        Args:
            path: Path to the Alda file.

        Returns:
            A new Score instance.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = Path(path)
        source = path.read_text(encoding="utf-8")
        return cls(source, filename=str(path))

    @classmethod
    def from_elements(cls, *elements: ComposeElement) -> Score:
        """Create a Score from compose domain objects.

        Args:
            *elements: Compose elements (notes, rests, parts, tempo, etc.).

        Returns:
            A new Score instance.

        Examples:
            >>> from aldakit.compose import part, note, tempo
            >>> score = Score.from_elements(
            ...     part("piano"),
            ...     tempo(120),
            ...     note("c", duration=4),
            ...     note("d"),
            ...     note("e"),
            ... )
        """
        score = cls.__new__(cls)
        score._mode = cls._MODE_ELEMENTS
        score._source = ""
        score._filename = "<compose>"
        score._elements = list(elements)
        return score

    @classmethod
    def from_parts(cls, *parts: Any) -> Score:
        """Create a Score from Part objects.

        This is a convenience method for creating a score from parts only.

        Args:
            *parts: Part objects.

        Returns:
            A new Score instance.
        """
        return cls.from_elements(*parts)

    @property
    def source(self) -> str:
        """The original Alda source code (if created from source)."""
        return self._source

    @cached_property
    def ast(self) -> RootNode:
        """The parsed AST (lazily computed and cached)."""
        if self._mode == self._MODE_SOURCE:
            return parse(self._source, self._filename)
        else:
            return self._build_ast_from_elements()

    @cached_property
    def midi(self) -> MidiSequence:
        """The generated MIDI sequence (lazily computed and cached)."""
        return generate_midi(self.ast)

    @property
    def duration(self) -> float:
        """Total duration of the score in seconds."""
        return self.midi.duration()

    def _build_ast_from_elements(self) -> RootNode:
        """Build AST directly from compose elements."""
        from .compose.part import Part

        children = []
        current_events = []

        for element in self._elements:
            ast_node = element.to_ast()

            # Parts need special handling - they're top-level nodes
            if isinstance(element, Part):
                # Flush any accumulated events first
                if current_events:
                    children.append(
                        EventSequenceNode(events=current_events, position=None)
                    )
                    current_events = []
                # Add part declaration (will be followed by events)
                children.append(ast_node)
            else:
                # Accumulate events
                current_events.append(ast_node)

        # Flush remaining events
        if current_events:
            children.append(EventSequenceNode(events=current_events, position=None))

        return RootNode(children=children, position=None)

    def _invalidate_cache(self) -> None:
        """Invalidate cached properties after modification."""
        # Delete cached properties if they exist
        for attr in ("ast", "midi"):
            if attr in self.__dict__:
                del self.__dict__[attr]

    # Builder methods

    def add(self, *elements: ComposeElement) -> Score:
        """Add elements to the score.

        This method modifies the score in place and returns self for chaining.
        Only works with scores created via from_elements().

        Args:
            *elements: Compose elements to add.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If the score was created from source code.
        """
        if self._mode == self._MODE_SOURCE:
            raise ValueError(
                "Cannot add elements to a source-based score. "
                "Use Score.from_elements() to create a modifiable score."
            )
        self._elements.extend(elements)
        self._invalidate_cache()
        return self

    def with_part(self, *instruments: str, alias: str | None = None) -> Score:
        """Add a part declaration.

        Args:
            *instruments: Instrument names.
            alias: Optional alias for the part.

        Returns:
            Self for method chaining.
        """
        from .compose.part import Part

        return self.add(Part(instruments=instruments, alias=alias))

    def with_tempo(self, bpm: int | float, global_: bool = False) -> Score:
        """Add a tempo attribute.

        Args:
            bpm: Beats per minute.
            global_: If True, applies globally to all parts.

        Returns:
            Self for method chaining.
        """
        from .compose.attributes import Tempo

        return self.add(Tempo(bpm=bpm, global_=global_))

    def with_volume(self, level: int | float) -> Score:
        """Add a volume attribute.

        Args:
            level: Volume level (0-100).

        Returns:
            Self for method chaining.
        """
        from .compose.attributes import Volume

        return self.add(Volume(level=level))

    # Output methods

    def to_alda(self) -> str:
        """Export as Alda source code.

        Returns:
            Alda source code string.
        """
        if self._mode == self._MODE_SOURCE:
            return self._source
        else:
            return " ".join(e.to_alda() for e in self._elements)

    def play(self, port: str | None = None, wait: bool = True) -> None:
        """Play the score through a MIDI port.

        Args:
            port: MIDI output port name. If None, uses the first available
                port or creates a virtual port named "AldaPyMIDI".
            wait: If True (default), block until playback completes.
        """
        with LibremidiBackend(port_name=port) as backend:
            backend.play(self.midi)
            if wait:
                while backend.is_playing():
                    time.sleep(0.1)

    def save(self, path: str | Path) -> None:
        """Save the score to a file.

        Supports both MIDI (.mid, .midi) and Alda (.alda) formats.

        Args:
            path: Output file path.
        """
        path = Path(path)
        if path.suffix in (".mid", ".midi"):
            backend = LibremidiBackend()
            backend.save(self.midi, path)
        elif path.suffix == ".alda":
            path.write_text(self.to_alda(), encoding="utf-8")
        else:
            # Default to MIDI
            backend = LibremidiBackend()
            backend.save(self.midi, path)

    def __repr__(self) -> str:
        if self._mode == self._MODE_SOURCE:
            # Show first 50 chars of source, truncated if longer
            preview = self._source[:50]
            if len(self._source) > 50:
                preview += "..."
            preview = preview.replace("\n", "\\n")
            return f"Score({preview!r})"
        else:
            n = len(self._elements)
            return f"Score.from_elements(<{n} elements>)"
