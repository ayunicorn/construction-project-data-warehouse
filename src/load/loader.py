"""Fast transactional PostgreSQL loading and ETL run tracking."""

from __future__ import annotations

import re
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Connection, Engine, create_engine, text

LOAD_ORDER = (
    "dim_project",
    "dim_site",
    "dim_contractor",
    "dim_worker",
    "dim_equipment",
    "dim_material",
    "dim_date",
    "fact_project_progress",
    "fact_project_costs",
    "fact_equipment_usage",
    "fact_safety_incidents",
)


class PostgreSQLLoader:
    """Load DataFrames with PostgreSQL COPY, usually much faster than row inserts."""

    def __init__(
        self,
        database_url: str,
        sql_dir: Path,
        schema: str = "construction_dw",
        engine: Engine | None = None,
    ) -> None:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
            raise ValueError("Warehouse schema must be a valid SQL identifier")
        self.engine = engine or create_engine(database_url, pool_pre_ping=True)
        self.sql_dir = sql_dir
        self.schema = schema

    def _sql(self, filename: str) -> str:
        """Apply the validated schema name to version-controlled SQL templates."""
        source = (self.sql_dir / filename).read_text(encoding="utf-8")
        return source.replace("construction_dw", self.schema)

    def initialize(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(text(self._sql("01_schema.sql")))

    def start_run(self, run_id: str, config_snapshot: str) -> None:
        statement = text(
            f"""
            INSERT INTO {self.schema}.etl_run (run_id, status, config_snapshot)
            VALUES (CAST(:run_id AS UUID), 'RUNNING', CAST(:config_snapshot AS JSONB))
            """
        )
        with self.engine.begin() as connection:
            connection.execute(statement, {"run_id": run_id, "config_snapshot": config_snapshot})

    def complete_run(
        self,
        run_id: str,
        source_rows: int,
        accepted_rows: int,
        rejected_rows: int,
        reject_ratio: float,
    ) -> None:
        statement = text(
            f"""
            UPDATE {self.schema}.etl_run
            SET status = 'SUCCESS', ended_at = NOW(), source_rows = :source_rows,
                accepted_rows = :accepted_rows, rejected_rows = :rejected_rows,
                reject_ratio = :reject_ratio
            WHERE run_id = CAST(:run_id AS UUID)
            """
        )
        with self.engine.begin() as connection:
            connection.execute(
                statement,
                {
                    "run_id": run_id,
                    "source_rows": source_rows,
                    "accepted_rows": accepted_rows,
                    "rejected_rows": rejected_rows,
                    "reject_ratio": reject_ratio,
                },
            )

    def fail_run(self, run_id: str, error_message: str) -> None:
        statement = text(
            f"""
            UPDATE {self.schema}.etl_run
            SET status = 'FAILED', ended_at = NOW(), error_message = :error_message
            WHERE run_id = CAST(:run_id AS UUID)
            """
        )
        with self.engine.begin() as connection:
            connection.execute(statement, {"run_id": run_id, "error_message": error_message[:2000]})

    def _copy_dataframe(self, connection: Connection, table: str, frame: pd.DataFrame) -> None:
        """Stream one DataFrame to PostgreSQL without intermediate disk files."""
        buffer = StringIO()
        frame.to_csv(buffer, index=False, header=False, na_rep="\\N", date_format="%Y-%m-%d")
        buffer.seek(0)
        columns = ", ".join(f'"{column}"' for column in frame.columns)
        copy_sql = (
            f'COPY "{self.schema}"."{table}" ({columns}) FROM STDIN WITH (FORMAT CSV, NULL \'\\N\')'
        )
        driver_connection: Any = connection.connection.driver_connection
        with driver_connection.cursor() as cursor:
            cursor.copy_expert(copy_sql, buffer)

    def load(self, tables: dict[str, pd.DataFrame]) -> int:
        """Replace the batch atomically, recreate views, and update planner statistics."""
        missing = set(LOAD_ORDER) - tables.keys()
        if missing:
            raise ValueError(f"Missing warehouse tables: {', '.join(sorted(missing))}")
        table_list = ", ".join(f'"{self.schema}"."{table}"' for table in LOAD_ORDER)
        with self.engine.begin() as connection:
            connection.execute(text(f"TRUNCATE TABLE {table_list} CASCADE"))
            for table in LOAD_ORDER:
                self._copy_dataframe(connection, table, tables[table])
            connection.execute(text(self._sql("02_views.sql")))
            for table in LOAD_ORDER:
                connection.execute(text(f'ANALYZE "{self.schema}"."{table}"'))
        return sum(len(frame) for frame in tables.values())
