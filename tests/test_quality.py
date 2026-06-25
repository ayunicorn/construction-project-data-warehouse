import json
from pathlib import Path

import pandas as pd

from src.quality import DataQualityFramework
from src.transform import WarehouseTransformer


def test_quality_report_passes_and_writes_json(
    valid_raw: dict[str, pd.DataFrame], tmp_path: Path
) -> None:
    result = WarehouseTransformer().transform(valid_raw)
    report = DataQualityFramework().evaluate(result, "run-123")
    output = tmp_path / "quality_metrics.json"
    report.write_json(output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert report.passed
    assert payload["run_id"] == "run-123"
    assert len(payload["checks"]) == 6


def test_quality_report_detects_duplicate_grain(valid_raw: dict[str, pd.DataFrame]) -> None:
    result = WarehouseTransformer().transform(valid_raw)
    progress = result.tables["fact_project_progress"]
    result.tables["fact_project_progress"] = pd.concat([progress, progress], ignore_index=True)
    report = DataQualityFramework().evaluate(result, "run-duplicate")
    check = next(item for item in report.checks if item.name == "unique_project_date")
    assert not check.passed
    assert check.failed_rows == 1
