from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class NormalizedRecord:
    module_id: str | None = None
    temperature: float | None = None
    voltage: float | None = None
    tx_power: float | None = None
    rx_power: float | None = None
    status: str | None = None
    lane_count: int | None = None
    source_index: int = -1
    source_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RecordValidationResult:
    source_index: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_index": self.source_index,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "diagnostics": self.diagnostics,
        }
