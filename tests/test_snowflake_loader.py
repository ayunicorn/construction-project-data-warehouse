from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.load.loader import LOAD_ORDER
from src.load.snowflake_loader import SnowflakeLoader


def _loader(
    sql_dir: Path,
    connection: MagicMock,
    write_pandas: MagicMock | None = None,
) -> SnowflakeLoader:
    return SnowflakeLoader(
        account="example-account",
        user="portfolio_user",
        password="synthetic-test-secret",
        database="portfolio_db",
        schema="construction_dw",
        warehouse="portfolio_wh",
        role="portfolio_role",
        sql_dir=sql_dir,
        connector_factory=MagicMock(return_value=connection),
        write_pandas_fn=write_pandas or MagicMock(),
    )


def test_snowflake_loader_requires_cloud_settings(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="SNOWFLAKE_ACCOUNT"):
        SnowflakeLoader(
            account="",
            user="",
            password="",
            database="CONSTRUCTION_DW",
            schema="CONSTRUCTION_DW",
            warehouse="COMPUTE_WH",
            role="",
            sql_dir=tmp_path,
        )


def test_snowflake_schema_template_is_rendered(project_root: Path) -> None:
    connection = MagicMock()
    loader = _loader(project_root / "sql/snowflake", connection)
    loader.initialize()
    script = connection.execute_string.call_args.args[0]
    assert "PORTFOLIO_DB.CONSTRUCTION_DW.dim_project" in script
    assert "{{DATABASE}}" not in script
    connection.close.assert_called_once()


def test_snowflake_load_uses_write_pandas_for_every_table(project_root: Path) -> None:
    connection = MagicMock()
    write_pandas = MagicMock(
        side_effect=lambda _connection, frame, **_kwargs: (True, 1, len(frame), None)
    )
    loader = _loader(project_root / "sql/snowflake", connection, write_pandas)
    tables = {name: pd.DataFrame({"record_key": [1]}) for name in LOAD_ORDER}
    loaded = loader.load(tables)
    assert loaded == len(LOAD_ORDER)
    assert write_pandas.call_count == len(LOAD_ORDER)
    first_options = write_pandas.call_args_list[0].kwargs
    assert first_options["database"] == "PORTFOLIO_DB"
    assert first_options["schema"] == "CONSTRUCTION_DW"
    assert first_options["quote_identifiers"] is False
    connection.commit.assert_called_once()


def test_snowflake_run_tracking_does_not_store_password(project_root: Path) -> None:
    connection = MagicMock()
    loader = _loader(project_root / "sql/snowflake", connection)
    loader.start_run("run-123", '{"warehouse_target": "snowflake"}')
    cursor = connection.cursor.return_value.__enter__.return_value
    parameters = cursor.execute.call_args.args[1]
    assert parameters == ("run-123", '{"warehouse_target": "snowflake"}')
    assert "synthetic-test-secret" not in str(cursor.execute.call_args)
