from pathlib import Path

import pandas as pd
import pytest

from src.extract import CSVExtractor
from src.extract.extractor import REQUIRED_FILES


def test_extractor_reads_all_required_csvs(tmp_path: Path) -> None:
    for name in REQUIRED_FILES:
        pd.DataFrame({"id": [1]}).to_csv(tmp_path / f"{name}.csv", index=False)
    extracted = CSVExtractor(tmp_path).extract()
    assert set(extracted) == set(REQUIRED_FILES)


def test_extractor_reports_missing_files(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Missing raw CSV files"):
        CSVExtractor(tmp_path).extract()
