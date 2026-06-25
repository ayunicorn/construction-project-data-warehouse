from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest
from sqlalchemy import text

from src.load import PostgreSQLLoader
from src.transform import WarehouseTransformer


@pytest.mark.integration
def test_postgres_copy_load_and_run_tracking(
    valid_raw: dict[str, pd.DataFrame], project_root: Path
) -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests")

    schema = f"test_dw_{uuid4().hex[:8]}"
    loader = PostgreSQLLoader(database_url, project_root / "sql", schema=schema)
    run_id = str(uuid4())
    result = WarehouseTransformer().transform(valid_raw)
    try:
        loader.initialize()
        loader.start_run(run_id, json.dumps({"environment": "test"}))
        loaded_rows = loader.load(result.tables)
        loader.complete_run(run_id, result.input_rows, loaded_rows, 0, 0)
        with loader.engine.connect() as connection:
            progress_count = connection.scalar(
                text(f'SELECT COUNT(*) FROM "{schema}".fact_project_progress')
            )
            status = connection.scalar(
                text(f'SELECT status FROM "{schema}".etl_run WHERE run_id = :run_id'),
                {"run_id": run_id},
            )
            view_count = connection.scalar(
                text(f'SELECT COUNT(*) FROM "{schema}".vw_project_progress_summary')
            )
        assert progress_count == 1
        assert status == "SUCCESS"
        assert view_count == 1
    finally:
        with loader.engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
