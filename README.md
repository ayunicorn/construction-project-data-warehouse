# Construction Project Data Warehouse

A production-style, beginner-friendly Data Engineering portfolio project based entirely on deterministic synthetic Malaysian construction data.

## What the project demonstrates

- 18,000+ source records across projects, progress, costs, equipment and safety
- YAML configuration with environment-variable overrides
- Modular extract, transform, quality and load layers
- PostgreSQL star schema with seven dimensions and four facts
- PostgreSQL-first design with an optional Snowflake cloud adapter
- Fast PostgreSQL `COPY FROM STDIN` loading inside one transaction
- ETL run history with `RUNNING`, `SUCCESS` and `FAILED` states
- Row quarantine, six quality rules and JSON quality metrics
- Human-readable console logs and rotating structured JSON logs
- Unit tests, PostgreSQL integration tests, Ruff, pre-commit and GitHub Actions
- Six Power BI-ready analytics views

All names and records are generated. The repository contains no real client, worker or commercial data.

## Architecture

```mermaid
flowchart LR
    A["Synthetic CSVs"] --> B["Extract"]
    B --> C["Transform and quarantine"]
    C --> D["Quality framework"]
    D -->|pass| E["PostgreSQL COPY load"]
    D --> F["quality_metrics.json"]
    E --> G[("Star schema")]
    E --> H["etl_run history"]
    G --> I["Analytics views"]
    I --> J["Power BI"]
```

Detailed diagrams: [architecture](docs/architecture.md) and [data model](docs/data_model.md).

## Quick start with Docker

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
docker compose run --rm etl python -m src.generate_data
docker compose run --rm etl python -m src.pipeline
```

The database is available at `localhost:5432`, database `construction_dw`.

This remains the default mode: `WAREHOUSE_TARGET=postgresql`.

## Warehouse modes

| Mode | Intended use | Loader | Cost profile |
|---|---|---|---|
| Local PostgreSQL | Development, interviews and portfolio demos | PostgreSQL `COPY FROM STDIN` | Free local container |
| Cloud Snowflake | Optional cloud warehouse demonstration | Snowflake connector `write_pandas` | Uses your Snowflake account credits |

Both modes use the same synthetic CSVs, transformations, quality gate, metrics and run IDs. PostgreSQL functionality is not replaced or reduced.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m src.generate_data
python -m src.pipeline --skip-load
```

Remove `--skip-load` when PostgreSQL is running.

## Configuration

Version-controlled defaults live in [config/settings.yaml](config/settings.yaml). Operational values in `.env` override YAML, so code never changes between environments.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Override the complete SQLAlchemy connection URL |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB` | Override connection fields |
| `WAREHOUSE_SCHEMA` | Select the target schema |
| `WAREHOUSE_TARGET` | `postgresql` by default; set `snowflake` to opt in |
| `RAW_DATA_DIR`, `PROCESSED_DATA_DIR` | Change pipeline storage paths |
| `REJECT_THRESHOLD` | Maximum allowed rejected-row ratio |
| `LOG_LEVEL`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT` | Control structured log rotation |
| `CONFIG_FILE` | Select another YAML configuration file |

Precedence is environment variables, then `.env`, then YAML defaults.

## Optional Snowflake setup

Snowflake mode is deliberately not installed in the local PostgreSQL image.

1. Install the optional connector dependencies:

```powershell
pip install -r requirements-snowflake.txt
```

2. Copy `.env.example` to `.env`, set `WAREHOUSE_TARGET=snowflake`, then provide your own values for:

```dotenv
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_DATABASE=CONSTRUCTION_DW
SNOWFLAKE_SCHEMA=CONSTRUCTION_DW
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=
```

3. Ensure the database and warehouse already exist and the selected role can use them and create objects in the target schema. The pipeline creates the schema, tables, run-tracking table and views; it does not create accounts, databases, warehouses, users or roles.

4. Run the cloud load explicitly:

```powershell
python -m src.pipeline --target snowflake
```

Use a small auto-suspending warehouse for a portfolio demonstration. Never commit `.env`, access tokens, private keys or copied account URLs. See the [Snowflake architecture and setup guide](docs/snowflake_architecture.md).

## ETL flow in interview language

1. **Extract** checks that all required CSV files exist and reads them with Pandas.
2. **Transform** standardizes dates, handles known missing values, removes duplicates, assigns surrogate keys and quarantines invalid rows.
3. **Quality** independently checks fact-table grain, numeric ranges, required keys and the reject ratio. It writes `data/processed/quality_metrics.json` before loading.
4. **Load** streams DataFrames with PostgreSQL COPY, refreshes views and runs `ANALYZE` in one transaction.
5. **Observe** uses `etl_run` for database run history and `logs/pipeline.jsonl` for machine-readable events tied together by `run_id`.

Transformation fixes or rejects records; the separate quality gate decides whether the batch is safe to publish.

## Commands

```powershell
python -m src.generate_data --seed 42
python -m src.pipeline --skip-load
python -m src.pipeline --config config/settings.yaml
python -m src.pipeline --target postgresql
python -m src.pipeline --target snowflake
ruff check .
ruff format --check .
pytest -m "not integration"
$env:TEST_DATABASE_URL="postgresql+psycopg2://construction:password@localhost:5432/construction_test"
pytest -m integration --no-cov
pre-commit run --all-files
```

## Warehouse objects

Dimensions: `dim_project`, `dim_site`, `dim_contractor`, `dim_worker`, `dim_equipment`, `dim_material`, `dim_date`.

Facts: `fact_project_progress`, `fact_project_costs`, `fact_equipment_usage`, `fact_safety_incidents`.

Views: `vw_project_progress_summary`, `vw_budget_vs_actual`, `vw_equipment_utilization`, `vw_material_consumption`, `vw_safety_incident_summary`, `vw_project_delay_risk`.

Operational metadata: `etl_run` stores timing, status, row counts, reject ratio, errors and a credential-free configuration snapshot.

PostgreSQL DDL and views live in `sql/`. Snowflake-specific DDL and dialect-compatible views live in `sql/snowflake/`.

## Testing strategy

- Unit tests cover configuration precedence, extraction, transformations, quality rules, JSON logging and COPY construction.
- Integration tests create an isolated PostgreSQL schema, COPY all warehouse tables, query a view, verify run tracking and drop the schema.
- CI starts PostgreSQL 16 and runs Ruff, formatting, unit tests and integration tests.

## Documentation

- [Data dictionary](docs/data_dictionary.md)
- [ETL workflow](docs/etl_workflow.md)
- [Snowflake architecture](docs/snowflake_architecture.md)
- [Power BI guide](docs/power_bi_guide.md)
- [Screenshot checklist](docs/screenshots.md)
- [Resume bullets](docs/resume_bullets.md)
- [Contributing](CONTRIBUTING.md) and [security policy](SECURITY.md)

## Design trade-off

Transactional truncate-and-reload keeps this portfolio batch reproducible and easy to explain. A larger production system would use object storage, incremental watermarks, staging tables and merge logic, orchestration, alerting and slowly changing dimensions.
