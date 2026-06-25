# ETL workflow

1. A UUID `run_id` connects logs, quality metrics and PostgreSQL run history.
2. The pipeline loads YAML defaults and applies environment overrides.
3. `CSVExtractor` verifies and reads all ten source files.
4. `WarehouseTransformer` cleans records, creates surrogate keys and quarantines invalid facts.
5. `DataQualityFramework` runs six blocking rules and writes `quality_metrics.json`.
6. The selected adapter publishes the accepted batch: PostgreSQL uses `COPY FROM STDIN`; optional Snowflake mode uses connector-managed `write_pandas` loads.
7. Analytics views are refreshed, tables are analyzed and `etl_run` becomes `SUCCESS`.
8. Any exception is logged with stack context and changes the tracked run to `FAILED`.

## Quality rules

| Rule | Enforcement |
|---|---|
| Unique project/date progress | Quality framework, unique database constraint |
| Progress from 0 to 100 | Row quarantine, quality framework, check constraint |
| Non-negative costs | Row quarantine, quality framework, check constraint |
| Operating hours from 0 to 24 | Row quarantine, quality framework, check constraint |
| Required foreign keys present | Merge validation, quality framework, foreign keys |
| Reject ratio below 5% | Configurable pre-load quality gate |

The JSON artifact makes every quality decision inspectable without database access.
