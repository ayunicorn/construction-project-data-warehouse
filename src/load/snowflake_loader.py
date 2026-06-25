"""Optional Snowflake warehouse loader using the official Python connector."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from src.load.loader import LOAD_ORDER

ConnectorFactory = Callable[..., Any]
WritePandas = Callable[..., tuple[bool, int, int, Any]]


class SnowflakeLoader:
    """Load transformed DataFrames into an existing Snowflake database."""

    def __init__(
        self,
        *,
        account: str,
        user: str,
        password: str,
        database: str,
        schema: str,
        warehouse: str,
        role: str,
        sql_dir: Path,
        batch_size: int = 5000,
        connector_factory: ConnectorFactory | None = None,
        write_pandas_fn: WritePandas | None = None,
    ) -> None:
        required = {
            "SNOWFLAKE_ACCOUNT": account,
            "SNOWFLAKE_USER": user,
            "SNOWFLAKE_PASSWORD": password,
            "SNOWFLAKE_DATABASE": database,
            "SNOWFLAKE_SCHEMA": schema,
            "SNOWFLAKE_WAREHOUSE": warehouse,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing Snowflake settings: {', '.join(missing)}")
        for label, identifier in {
            "database": database,
            "schema": schema,
            "warehouse": warehouse,
            "role": role,
        }.items():
            if identifier and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", identifier):
                raise ValueError(f"Snowflake {label} must be a simple SQL identifier")

        self.account = account
        self.user = user
        self.password = password
        self.database = database.upper()
        self.schema = schema.upper()
        self.warehouse = warehouse.upper()
        self.role = role.upper()
        self.sql_dir = sql_dir
        self.batch_size = batch_size
        self._connector_factory = connector_factory
        self._write_pandas_fn = write_pandas_fn

    def _load_connector(self) -> None:
        if self._connector_factory and self._write_pandas_fn:
            return
        try:
            import snowflake.connector
            from snowflake.connector.pandas_tools import write_pandas
        except ImportError as error:
            raise RuntimeError(
                "Snowflake mode requires: pip install -r requirements-snowflake.txt"
            ) from error
        self._connector_factory = snowflake.connector.connect
        self._write_pandas_fn = write_pandas

    def _connect(self) -> Any:
        self._load_connector()
        parameters = {
            "account": self.account,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "warehouse": self.warehouse,
            "application": "construction_project_dw",
        }
        if self.role:
            parameters["role"] = self.role
        return self._connector_factory(**parameters)

    def _sql(self, filename: str) -> str:
        source = (self.sql_dir / filename).read_text(encoding="utf-8")
        return source.replace("{{DATABASE}}", self.database).replace("{{SCHEMA}}", self.schema)

    def initialize(self) -> None:
        connection = self._connect()
        try:
            connection.execute_string(self._sql("01_schema.sql"))
        finally:
            connection.close()

    def start_run(self, run_id: str, config_snapshot: str) -> None:
        sql = f"""
            INSERT INTO {self.database}.{self.schema}.etl_run
                (run_id, status, started_at, config_snapshot)
            SELECT %s, 'RUNNING', CURRENT_TIMESTAMP(), PARSE_JSON(%s)
        """
        self._execute(sql, (run_id, config_snapshot))

    def complete_run(
        self,
        run_id: str,
        source_rows: int,
        accepted_rows: int,
        rejected_rows: int,
        reject_ratio: float,
    ) -> None:
        sql = f"""
            UPDATE {self.database}.{self.schema}.etl_run
            SET status = 'SUCCESS', ended_at = CURRENT_TIMESTAMP(), source_rows = %s,
                accepted_rows = %s, rejected_rows = %s, reject_ratio = %s
            WHERE run_id = %s
        """
        self._execute(
            sql,
            (source_rows, accepted_rows, rejected_rows, reject_ratio, run_id),
        )

    def fail_run(self, run_id: str, error_message: str) -> None:
        sql = f"""
            UPDATE {self.database}.{self.schema}.etl_run
            SET status = 'FAILED', ended_at = CURRENT_TIMESTAMP(), error_message = %s
            WHERE run_id = %s
        """
        self._execute(sql, (error_message[:2000], run_id))

    def _execute(self, sql: str, parameters: tuple[Any, ...]) -> None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, parameters)
            connection.commit()
        finally:
            connection.close()

    def load(self, tables: dict[str, pd.DataFrame]) -> int:
        missing = set(LOAD_ORDER) - tables.keys()
        if missing:
            raise ValueError(f"Missing warehouse tables: {', '.join(sorted(missing))}")

        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                for table in reversed(LOAD_ORDER):
                    cursor.execute(f"TRUNCATE TABLE {self.database}.{self.schema}.{table}")
            for table in LOAD_ORDER:
                success, _, row_count, _ = self._write_pandas_fn(
                    connection,
                    tables[table],
                    table_name=table.upper(),
                    database=self.database,
                    schema=self.schema,
                    chunk_size=self.batch_size,
                    quote_identifiers=False,
                    auto_create_table=False,
                    overwrite=False,
                )
                if not success or row_count != len(tables[table]):
                    raise RuntimeError(
                        f"Snowflake load failed for {table}: expected {len(tables[table])}, "
                        f"loaded {row_count}"
                    )
            connection.execute_string(self._sql("02_views.sql"))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return sum(len(frame) for frame in tables.values())
