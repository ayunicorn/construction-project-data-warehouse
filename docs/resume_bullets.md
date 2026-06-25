# Resume bullet points

- Engineered an end-to-end Python and PostgreSQL construction data warehouse processing 18K+ synthetic records across project controls, costs, equipment and safety domains.
- Designed a seven-dimension/four-fact star schema with surrogate keys, referential constraints and six analytics views for Power BI reporting.
- Implemented Pandas data-quality controls for duplicates, missing values, invalid progress/cost/hour ranges, foreign keys and a configurable sub-5% reject gate.
- Containerized PostgreSQL and the SQLAlchemy ETL with Docker Compose and added automated Pytest/Ruff checks in GitHub Actions.
- Built project-control metrics including schedule variance, budget variance, completion ratio, equipment utilization and rules-based delay risk.
- Refactored runtime configuration to YAML with environment overrides and added correlated JSON logging, quality metrics and PostgreSQL ETL run tracking.
- Replaced multi-row inserts with transactional PostgreSQL COPY loading, targeted analytical indexes and post-load statistics collection.
- Extended the PostgreSQL-first warehouse with an optional Snowflake connector adapter, vendor-specific DDL and six Snowflake-compatible analytics views while preserving one shared quality-controlled ETL flow.
