"""Command-line orchestration for extract, transform, quality, and load."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.config import Settings, get_settings
from src.extract import CSVExtractor
from src.logging_config import configure_logging
from src.quality import DataQualityFramework, QualityReport
from src.transform import WarehouseTransformer


def _safe_config_snapshot(settings: Settings, target: str) -> str:
    """Return useful run configuration without credentials."""
    return json.dumps(
        {
            "raw_data_dir": str(settings.raw_data_dir),
            "processed_data_dir": str(settings.processed_data_dir),
            "warehouse_target": target,
            "warehouse_schema": (
                settings.snowflake_schema if target == "snowflake" else settings.warehouse_schema
            ),
            "snowflake_database": (settings.snowflake_database if target == "snowflake" else None),
            "reject_threshold": settings.reject_threshold,
            "batch_size": settings.batch_size,
        }
    )


def _create_loader(settings: Settings, target: str) -> Any:
    """Build only the selected warehouse adapter."""
    if target == "postgresql":
        from src.load import PostgreSQLLoader

        return PostgreSQLLoader(
            settings.database_url,
            settings.project_root / "sql",
            settings.warehouse_schema,
        )
    if target == "snowflake":
        from src.load import SnowflakeLoader

        return SnowflakeLoader(
            account=settings.snowflake_account,
            user=settings.snowflake_user,
            password=settings.snowflake_password,
            database=settings.snowflake_database,
            schema=settings.snowflake_schema,
            warehouse=settings.snowflake_warehouse,
            role=settings.snowflake_role,
            sql_dir=settings.project_root / "sql/snowflake",
            batch_size=settings.batch_size,
        )
    raise ValueError("WAREHOUSE_TARGET must be 'postgresql' or 'snowflake'")


def run_pipeline(
    skip_load: bool = False,
    project_root: Path | None = None,
    config_path: Path | None = None,
    warehouse_target: str | None = None,
) -> QualityReport:
    settings = get_settings(project_root, config_path)
    target = (warehouse_target or settings.warehouse_target).lower()
    if target not in {"postgresql", "snowflake"}:
        raise ValueError("Warehouse target must be 'postgresql' or 'snowflake'")
    run_id = str(uuid4())
    logger = configure_logging(
        settings.project_root / "logs",
        settings.log_level,
        settings.log_max_bytes,
        settings.log_backup_count,
    )
    loader = None
    logger.info(
        "ETL run started",
        extra={"run_id": run_id, "event": "etl_started", "warehouse_target": target},
    )

    try:
        if not skip_load:
            loader = _create_loader(settings, target)
            loader.initialize()
            loader.start_run(run_id, _safe_config_snapshot(settings, target))

        raw = CSVExtractor(settings.raw_data_dir).extract()
        source_rows = sum(map(len, raw.values()))
        logger.info(
            "Source extraction completed",
            extra={"run_id": run_id, "event": "extract_completed", "rows": source_rows},
        )

        result = WarehouseTransformer().transform(raw)
        settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
        reject_dir = settings.processed_data_dir / "rejects"
        reject_dir.mkdir(exist_ok=True)
        for name, frame in result.tables.items():
            frame.to_csv(settings.processed_data_dir / f"{name}.csv", index=False)
        for name, frame in result.rejects.items():
            frame.to_csv(reject_dir / f"{name}_rejects.csv", index=False)

        quality = DataQualityFramework(
            settings.reject_threshold,
            settings.progress_min,
            settings.progress_max,
            settings.equipment_hours_min,
            settings.equipment_hours_max,
        )
        report = quality.evaluate(result, run_id, target)
        report.write_json(settings.metrics_file)
        quality.enforce(report)
        logger.info(
            "Data quality gate passed",
            extra={
                "run_id": run_id,
                "event": "quality_passed",
                "rejected_rows": report.rejected_rows,
                "reject_ratio": report.reject_ratio,
            },
        )

        if loader:
            loaded_rows = loader.load(result.tables)
            loader.complete_run(
                run_id,
                report.input_rows,
                report.accepted_rows,
                report.rejected_rows,
                report.reject_ratio,
            )
            logger.info(
                "Warehouse load completed",
                extra={
                    "run_id": run_id,
                    "event": "load_completed",
                    "rows": loaded_rows,
                    "warehouse_target": target,
                },
            )
        else:
            logger.info(
                "Database load skipped",
                extra={"run_id": run_id, "event": "load_skipped"},
            )
        return report
    except Exception as error:
        if loader:
            try:
                loader.fail_run(run_id, str(error))
            except Exception:
                logger.exception(
                    "Unable to persist failed run status",
                    extra={"run_id": run_id, "event": "run_tracking_failed"},
                )
        logger.exception(
            "ETL run failed",
            extra={"run_id": run_id, "event": "etl_failed"},
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the construction warehouse ETL")
    parser.add_argument(
        "--skip-load", action="store_true", help="Transform only; do not load PostgreSQL"
    )
    parser.add_argument("--config", type=Path, help="Optional path to a YAML settings file")
    parser.add_argument(
        "--target",
        choices=("postgresql", "snowflake"),
        help="Warehouse target; defaults to WAREHOUSE_TARGET or PostgreSQL",
    )
    args = parser.parse_args()
    run_pipeline(
        skip_load=args.skip_load,
        config_path=args.config,
        warehouse_target=args.target,
    )


if __name__ == "__main__":
    main()
