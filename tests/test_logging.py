import json
import logging
from pathlib import Path

from src.logging_config import JsonFormatter, configure_logging


def test_json_formatter_includes_structured_context() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "loaded", (), None)
    record.run_id = "run-123"
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "loaded"
    assert payload["run_id"] == "run-123"
    assert payload["level"] == "INFO"


def test_configure_logging_writes_json_lines(tmp_path: Path) -> None:
    logger = configure_logging(tmp_path, max_bytes=1024, backup_count=1)
    logger.info("quality passed", extra={"run_id": "run-456"})
    for handler in logger.handlers:
        handler.flush()
    payload = json.loads((tmp_path / "pipeline.jsonl").read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-456"
