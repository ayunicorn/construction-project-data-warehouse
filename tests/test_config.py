from pathlib import Path

from src.config import get_settings
from src.pipeline import _safe_config_snapshot


def test_yaml_configuration_loads_defaults(project_root: Path) -> None:
    settings = get_settings(project_root)
    assert settings.warehouse_schema == "construction_dw"
    assert settings.reject_threshold == 0.05
    assert settings.raw_data_dir == project_root / "data/raw"


def test_environment_overrides_yaml(project_root: Path, monkeypatch) -> None:
    monkeypatch.setenv("REJECT_THRESHOLD", "0.02")
    monkeypatch.setenv("WAREHOUSE_SCHEMA", "portfolio_dw")
    monkeypatch.setenv("BATCH_SIZE", "1000")
    settings = get_settings(project_root)
    assert settings.reject_threshold == 0.02
    assert settings.warehouse_schema == "portfolio_dw"
    assert settings.batch_size == 1000


def test_snowflake_environment_overrides_are_loaded(project_root: Path, monkeypatch) -> None:
    monkeypatch.setenv("WAREHOUSE_TARGET", "snowflake")
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "example-account")
    monkeypatch.setenv("SNOWFLAKE_USER", "portfolio_user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "synthetic-test-secret")
    monkeypatch.setenv("SNOWFLAKE_DATABASE", "PORTFOLIO_DB")
    monkeypatch.setenv("SNOWFLAKE_SCHEMA", "CONSTRUCTION_DW")
    monkeypatch.setenv("SNOWFLAKE_WAREHOUSE", "PORTFOLIO_WH")
    monkeypatch.setenv("SNOWFLAKE_ROLE", "PORTFOLIO_ROLE")
    settings = get_settings(project_root)
    assert settings.warehouse_target == "snowflake"
    assert settings.snowflake_account == "example-account"
    assert settings.snowflake_database == "PORTFOLIO_DB"
    assert settings.snowflake_role == "PORTFOLIO_ROLE"
    snapshot = _safe_config_snapshot(settings, "snowflake")
    assert "synthetic-test-secret" not in snapshot
    assert "portfolio_user" not in snapshot
