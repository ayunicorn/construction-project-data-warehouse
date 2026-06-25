from __future__ import annotations

import pandas as pd
import pytest

from src.quality import DataQualityFramework, QualityGateError
from src.transform import DataQualityError, WarehouseTransformer


def test_transform_calculates_business_metrics(valid_raw: dict[str, pd.DataFrame]) -> None:
    result = WarehouseTransformer().transform(valid_raw)
    progress = result.tables["fact_project_progress"].iloc[0]
    costs = result.tables["fact_project_costs"].iloc[0]
    usage = result.tables["fact_equipment_usage"].iloc[0]
    assert progress["schedule_variance_pct"] == -2
    assert progress["completion_ratio"] == 0.08
    assert costs["budget_variance_myr"] == -100
    assert usage["utilization_pct"] == 80
    assert result.reject_ratio == 0


def test_duplicate_project_date_is_removed(valid_raw: dict[str, pd.DataFrame]) -> None:
    valid_raw["daily_progress"] = pd.concat(
        [valid_raw["daily_progress"], valid_raw["daily_progress"]], ignore_index=True
    )
    result = WarehouseTransformer().transform(valid_raw)
    assert len(result.tables["fact_project_progress"]) == 1


@pytest.mark.parametrize(
    ("table", "column", "invalid_value"),
    [
        ("daily_progress", "actual_progress_pct", 101),
        ("project_costs", "actual_cost_myr", -1),
        ("equipment_usage", "operating_hours", 25),
    ],
)
def test_invalid_values_are_rejected(
    valid_raw: dict[str, pd.DataFrame], table: str, column: str, invalid_value: float
) -> None:
    valid_raw[table].loc[0, column] = invalid_value
    result = WarehouseTransformer().transform(valid_raw)
    fact_name = {
        "daily_progress": "fact_project_progress",
        "project_costs": "fact_project_costs",
        "equipment_usage": "fact_equipment_usage",
    }[table]
    assert result.tables[fact_name].empty
    assert len(result.rejects[fact_name]) == 1


def test_reject_threshold_stops_pipeline(valid_raw: dict[str, pd.DataFrame]) -> None:
    valid_raw["daily_progress"].loc[0, "actual_progress_pct"] = 120
    result = WarehouseTransformer().transform(valid_raw)
    framework = DataQualityFramework(reject_threshold=0.01)
    report = framework.evaluate(result, "test-run")
    with pytest.raises(QualityGateError, match="reject_ratio_below_threshold"):
        framework.enforce(report)


def test_unknown_foreign_key_fails(valid_raw: dict[str, pd.DataFrame]) -> None:
    valid_raw["equipment_usage"].loc[0, "equipment_id"] = "MISSING"
    with pytest.raises(DataQualityError, match="Foreign key validation"):
        WarehouseTransformer().transform(valid_raw)
