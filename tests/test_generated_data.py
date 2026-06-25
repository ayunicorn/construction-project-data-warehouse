from pathlib import Path

import pandas as pd

from src.extract import CSVExtractor
from src.generate_data import generate_synthetic_data
from src.transform import WarehouseTransformer


def test_generated_data_meets_portfolio_volume(tmp_path: Path) -> None:
    frames = generate_synthetic_data(tmp_path)
    assert len(frames["projects"]) >= 10
    assert len(frames["workers"]) >= 100
    assert len(frames["equipment"]) >= 50
    fact_rows = sum(
        len(frames[name])
        for name in ("daily_progress", "project_costs", "equipment_usage", "safety_incidents")
    )
    assert fact_rows >= 10_000
    assert pd.to_datetime(frames["daily_progress"]["report_date"]).nunique() >= 365


def test_generated_data_passes_quality_gate(tmp_path: Path) -> None:
    generate_synthetic_data(tmp_path)
    result = WarehouseTransformer().transform(CSVExtractor(tmp_path).extract())
    assert result.reject_ratio < 0.05
    assert result.tables["fact_project_progress"]["actual_progress_pct"].between(0, 100).all()
    assert result.tables["fact_project_costs"]["actual_cost_myr"].ge(0).all()
    assert result.tables["fact_equipment_usage"]["operating_hours"].between(0, 24).all()
