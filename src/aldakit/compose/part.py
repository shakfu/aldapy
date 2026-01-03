"""Part class for instrument declarations."""

from __future__ import annotations

from dataclasses import dataclass

from ..ast_nodes import PartDeclarationNode
from .base import ComposeElement


@dataclass(frozen=True)
class Part(ComposeElement):
    """An instrument part declaration.

    Examples:
        >>> part("piano")
        >>> part("violin", alias="v1")
        >>> part("violin", "viola", "cello", alias="strings")
    """

    instruments: tuple[str, ...]
    alias: str | None = None

    def to_ast(self) -> PartDeclarationNode:
        """Convert to AST PartDeclarationNode."""
        return PartDeclarationNode(
            names=list(self.instruments), alias=self.alias, position=None
        )

    def to_alda(self) -> str:
        """Convert to Alda source code."""
        names = "/".join(self.instruments)
        if self.alias:
            return f'{names} "{self.alias}":'
        return f"{names}:"


def part(*instruments: str, alias: str | None = None) -> Part:
    """Create a part declaration.

    Args:
        *instruments: Instrument names (e.g., "piano", "violin").
        alias: Optional alias for the part.

    Returns:
        Part element.

    Examples:
        >>> part("piano")
        >>> part("violin", alias="v1")
        >>> part("violin", "viola", "cello", alias="strings")
    """
    if not instruments:
        raise ValueError("At least one instrument name is required")
    return Part(instruments=instruments, alias=alias)
