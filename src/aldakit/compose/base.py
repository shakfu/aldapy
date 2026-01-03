"""Base classes and protocols for compose elements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ast_nodes import ASTNode


class ComposeElement(ABC):
    """Base class for all compose elements.

    All compose elements can generate AST nodes directly and
    serialize to Alda source code.
    """

    @abstractmethod
    def to_ast(self) -> ASTNode:
        """Convert this element to an AST node."""
        ...

    @abstractmethod
    def to_alda(self) -> str:
        """Convert this element to Alda source code."""
        ...
