from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Severity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class Finding:
    """A deterministic contract finding."""

    rule_id: str
    severity: Severity
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
