"""Backward-compatible import path for document parsers.

Runtime routes import :mod:`core.documents.parsers` so disabling RAG does not
import the optional retrieval package.
"""

from core.documents.parsers import DocumentParser, ParsedDocument

__all__ = ["DocumentParser", "ParsedDocument"]
