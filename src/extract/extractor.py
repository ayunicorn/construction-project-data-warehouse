"""CSV extraction with schema presence checks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_FILES = (
    "projects",
    "sites",
    "contractors",
    "workers",
    "equipment",
    "materials",
    "daily_progress",
    "project_costs",
    "equipment_usage",
    "safety_incidents",
)


class CSVExtractor:
    def __init__(self, raw_dir: Path) -> None:
        self.raw_dir = raw_dir

    def extract(self) -> dict[str, pd.DataFrame]:
        missing = [name for name in REQUIRED_FILES if not (self.raw_dir / f"{name}.csv").exists()]
        if missing:
            raise FileNotFoundError(f"Missing raw CSV files: {', '.join(missing)}")
        return {
            name: pd.read_csv(self.raw_dir / f"{name}.csv", low_memory=False)
            for name in REQUIRED_FILES
        }
