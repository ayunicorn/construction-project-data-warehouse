"""Dataset-level quality checks executed between transform and load."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.transform.transformer import TransformResult


class QualityGateError(RuntimeError):
    """Raised when one or more blocking data-quality rules fail."""


@dataclass(frozen=True)
class RuleResult:
    name: str
    passed: bool
    failed_rows: int
    description: str


@dataclass(frozen=True)
class QualityReport:
    run_id: str
    warehouse_target: str
    generated_at: str
    input_rows: int
    accepted_rows: int
    rejected_rows: int
    reject_ratio: float
    passed: bool
    checks: list[RuleResult]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


class DataQualityFramework:
    """Evaluate warehouse invariants and emit an auditable report."""

    def __init__(
        self,
        reject_threshold: float = 0.05,
        progress_min: float = 0,
        progress_max: float = 100,
        equipment_hours_min: float = 0,
        equipment_hours_max: float = 24,
    ) -> None:
        self.reject_threshold = reject_threshold
        self.progress_min = progress_min
        self.progress_max = progress_max
        self.equipment_hours_min = equipment_hours_min
        self.equipment_hours_max = equipment_hours_max

    @staticmethod
    def _result(name: str, failed_rows: int, description: str) -> RuleResult:
        return RuleResult(name, failed_rows == 0, failed_rows, description)

    def evaluate(
        self,
        result: TransformResult,
        run_id: str,
        warehouse_target: str = "not_loaded",
    ) -> QualityReport:
        progress = result.tables["fact_project_progress"]
        costs = result.tables["fact_project_costs"]
        usage = result.tables["fact_equipment_usage"]
        required_keys = {
            "fact_project_progress": ["project_key", "date_key"],
            "fact_project_costs": ["project_key", "date_key", "contractor_key"],
            "fact_equipment_usage": ["project_key", "equipment_key", "date_key"],
            "fact_safety_incidents": [
                "project_key",
                "site_key",
                "contractor_key",
                "date_key",
            ],
        }

        checks = [
            self._result(
                "unique_project_date",
                int(progress.duplicated(["project_key", "date_key"]).sum()),
                "One progress record per project and date",
            ),
            self._result(
                "progress_in_range",
                int(
                    (
                        ~progress["planned_progress_pct"].between(
                            self.progress_min, self.progress_max
                        )
                    ).sum()
                    + (
                        ~progress["actual_progress_pct"].between(
                            self.progress_min, self.progress_max
                        )
                    ).sum()
                ),
                "Planned and actual progress remain within configured bounds",
            ),
            self._result(
                "costs_non_negative",
                int((costs[["planned_cost_myr", "actual_cost_myr"]] < 0).any(axis=1).sum()),
                "Planned and actual costs cannot be negative",
            ),
            self._result(
                "equipment_hours_in_range",
                int(
                    (
                        ~usage["operating_hours"].between(
                            self.equipment_hours_min, self.equipment_hours_max
                        )
                    ).sum()
                ),
                "Operating hours remain within configured bounds",
            ),
            self._result(
                "required_foreign_keys_present",
                sum(
                    int(result.tables[name][columns].isna().sum().sum())
                    for name, columns in required_keys.items()
                ),
                "Required warehouse foreign keys resolve to dimensions",
            ),
            RuleResult(
                "reject_ratio_below_threshold",
                result.reject_ratio < self.reject_threshold,
                result.rejected_rows if result.reject_ratio >= self.reject_threshold else 0,
                f"Rejected rows must be below {self.reject_threshold:.2%}",
            ),
        ]
        accepted_rows = result.input_rows - result.rejected_rows
        return QualityReport(
            run_id=run_id,
            warehouse_target=warehouse_target,
            generated_at=datetime.now(UTC).isoformat(),
            input_rows=result.input_rows,
            accepted_rows=accepted_rows,
            rejected_rows=result.rejected_rows,
            reject_ratio=round(result.reject_ratio, 6),
            passed=all(check.passed for check in checks),
            checks=checks,
        )

    @staticmethod
    def enforce(report: QualityReport) -> None:
        failed = [check.name for check in report.checks if not check.passed]
        if failed:
            raise QualityGateError(f"Data quality gate failed: {', '.join(failed)}")
