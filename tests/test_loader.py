from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from src.load.loader import PostgreSQLLoader


def test_copy_dataframe_uses_postgresql_copy(tmp_path: Path) -> None:
    engine = MagicMock()
    loader = PostgreSQLLoader("unused", tmp_path, engine=engine)
    connection = MagicMock()
    cursor = connection.connection.driver_connection.cursor.return_value.__enter__.return_value
    frame = pd.DataFrame({"project_key": [1], "project_id": ["PRJ001"]})
    loader._copy_dataframe(connection, "dim_project", frame)
    copy_sql, buffer = cursor.copy_expert.call_args.args
    assert 'COPY "construction_dw"."dim_project"' in copy_sql
    assert buffer.read().strip() == "1,PRJ001"


def test_loader_rejects_unsafe_schema(tmp_path: Path) -> None:
    try:
        PostgreSQLLoader("unused", tmp_path, schema="bad;drop schema")
    except ValueError as error:
        assert "valid SQL identifier" in str(error)
    else:
        raise AssertionError("Unsafe schema should be rejected")
