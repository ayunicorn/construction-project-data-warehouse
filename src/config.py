"""Load typed settings from YAML, then apply environment-variable overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Runtime settings used by every ETL layer."""

    project_root: Path
    raw_data_dir: Path
    processed_data_dir: Path
    metrics_file: Path
    warehouse_target: str
    database_url: str
    warehouse_schema: str
    snowflake_account: str
    snowflake_user: str
    snowflake_password: str
    snowflake_database: str
    snowflake_schema: str
    snowflake_warehouse: str
    snowflake_role: str
    batch_size: int
    reject_threshold: float
    log_level: str
    log_max_bytes: int
    log_backup_count: int
    progress_min: float
    progress_max: float
    equipment_hours_min: float
    equipment_hours_max: float


def _env(name: str, default: Any) -> Any:
    """Return an environment override or the YAML/default value."""
    return os.getenv(name, default)


def get_settings(project_root: Path | None = None, config_path: Path | None = None) -> Settings:
    """Load settings with precedence: environment > .env > YAML."""
    root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    load_dotenv(root / ".env")
    yaml_path = config_path or Path(os.getenv("CONFIG_FILE", root / "config/settings.yaml"))
    if not yaml_path.is_absolute():
        yaml_path = root / yaml_path
    with yaml_path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream) or {}

    pipeline = config.get("pipeline", {})
    warehouse = config.get("warehouse", {})
    quality = config.get("quality", {})
    logging_config = config.get("logging", {})
    snowflake = config.get("snowflake", {})

    host = _env("POSTGRES_HOST", warehouse.get("host", "localhost"))
    port = _env("POSTGRES_PORT", warehouse.get("port", 5432))
    database = _env("POSTGRES_DB", warehouse.get("database", "construction_dw"))
    user = _env("POSTGRES_USER", warehouse.get("user", "construction"))
    password = quote_plus(str(_env("POSTGRES_PASSWORD", warehouse.get("password", "construction"))))
    raw_dir = root / _env("RAW_DATA_DIR", pipeline.get("raw_data_dir", "data/raw"))
    processed_dir = root / _env(
        "PROCESSED_DATA_DIR", pipeline.get("processed_data_dir", "data/processed")
    )

    return Settings(
        project_root=root,
        raw_data_dir=raw_dir,
        processed_data_dir=processed_dir,
        metrics_file=processed_dir
        / _env("QUALITY_METRICS_FILE", quality.get("metrics_file", "quality_metrics.json")),
        warehouse_target=str(
            _env("WAREHOUSE_TARGET", warehouse.get("target", "postgresql"))
        ).lower(),
        database_url=str(
            _env(
                "DATABASE_URL",
                f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
            )
        ),
        warehouse_schema=str(_env("WAREHOUSE_SCHEMA", warehouse.get("schema", "construction_dw"))),
        snowflake_account=str(_env("SNOWFLAKE_ACCOUNT", snowflake.get("account", ""))),
        snowflake_user=str(_env("SNOWFLAKE_USER", snowflake.get("user", ""))),
        snowflake_password=str(_env("SNOWFLAKE_PASSWORD", snowflake.get("password", ""))),
        snowflake_database=str(
            _env("SNOWFLAKE_DATABASE", snowflake.get("database", "CONSTRUCTION_DW"))
        ),
        snowflake_schema=str(_env("SNOWFLAKE_SCHEMA", snowflake.get("schema", "CONSTRUCTION_DW"))),
        snowflake_warehouse=str(
            _env("SNOWFLAKE_WAREHOUSE", snowflake.get("warehouse", "COMPUTE_WH"))
        ),
        snowflake_role=str(_env("SNOWFLAKE_ROLE", snowflake.get("role", ""))),
        batch_size=int(_env("BATCH_SIZE", pipeline.get("batch_size", 5000))),
        reject_threshold=float(_env("REJECT_THRESHOLD", quality.get("reject_threshold", 0.05))),
        log_level=str(_env("LOG_LEVEL", logging_config.get("level", "INFO"))),
        log_max_bytes=int(_env("LOG_MAX_BYTES", logging_config.get("max_bytes", 5_000_000))),
        log_backup_count=int(_env("LOG_BACKUP_COUNT", logging_config.get("backup_count", 3))),
        progress_min=float(_env("PROGRESS_MIN", quality.get("progress_min", 0))),
        progress_max=float(_env("PROGRESS_MAX", quality.get("progress_max", 100))),
        equipment_hours_min=float(
            _env("EQUIPMENT_HOURS_MIN", quality.get("equipment_hours_min", 0))
        ),
        equipment_hours_max=float(
            _env("EQUIPMENT_HOURS_MAX", quality.get("equipment_hours_max", 24))
        ),
    )
