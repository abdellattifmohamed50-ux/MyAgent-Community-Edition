from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from core.exceptions.base import ValidationError


@dataclass(frozen=True)
class ParsedDocument:
    title: str
    content: str
    source_type: str


class DocumentParser:
    """Strict parser for the text formats accepted by the knowledge API."""

    allowed_types = {"text/plain", "text/markdown", "application/json"}

    def parse_upload(
        self,
        filename: str | None,
        content_type: str | None,
        raw: bytes,
    ) -> ParsedDocument:
        normalized_type = (content_type or "").split(";", 1)[0].strip().lower()
        if normalized_type not in self.allowed_types:
            raise ValidationError("Only TXT, Markdown and JSON files are supported")
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("Knowledge file must use UTF-8 encoding") from exc
        if "\x00" in content:
            raise ValidationError("Knowledge file contains unsupported binary data")
        if normalized_type == "application/json":
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValidationError("Knowledge JSON file is invalid") from exc
            content = json.dumps(parsed, ensure_ascii=False, indent=2)
        content = content.strip()
        if not content:
            raise ValidationError("Knowledge file is empty")
        safe_name = Path((filename or "Uploaded knowledge").replace("\\", "/")).name[:255]
        return ParsedDocument(title=safe_name, content=content, source_type="file")
