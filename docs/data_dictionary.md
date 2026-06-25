# Data dictionary

All monetary fields are Malaysian ringgit (MYR). Percentages are stored from 0 to 100; `completion_ratio` is stored from 0 to 1.

## Dimensions

| Table | Business purpose | Key attributes |
|---|---|---|
| `dim_project` | Project master and commercial baseline | project name/type, status, dates, budget, client |
| `dim_site` | Physical construction location | city, state, coordinates, site area |
| `dim_contractor` | Delivery partner | specialization, CIDB grade, safety rating |
| `dim_worker` | Workforce roster | contractor, trade, skill level, employment type |
| `dim_equipment` | Plant and machinery master | type, manufacturer, ownership, rate, status |
| `dim_material` | Procured material master | category, unit, standard unit cost, supplier |
| `dim_date` | Shared reporting calendar | day, month, quarter, year, ISO week, weekend flag |

## Facts and measures

| Table | Measure | Definition |
|---|---|---|
| `fact_project_progress` | `schedule_variance_pct` | actual progress minus planned progress |
| `fact_project_progress` | `completion_ratio` | actual progress divided by 100 |
| `fact_project_progress` | `delay_hours` | work hours lost for the reporting day |
| `fact_project_costs` | `budget_variance_myr` | planned cost minus actual cost; negative is overrun |
| `fact_project_costs` | `quantity` | consumed material quantity; zero for non-material cost |
| `fact_equipment_usage` | `utilization_pct` | operating hours divided by available hours, capped at 100 |
| `fact_equipment_usage` | `maintenance_cost_myr` | maintenance spend during usage date |
| `fact_safety_incidents` | `lost_time_days` | productive days lost due to incident |
| `fact_safety_incidents` | `reportable` | whether the incident meets reporting criteria |

Surrogate keys use the `<entity>_key` convention. Natural source identifiers use `<entity>_id` and are retained on dimensions for lineage.

## Operational metadata

| Table | Column | Definition |
|---|---|---|
| `etl_run` | `run_id` | UUID shared with JSON logs and quality metrics |
| `etl_run` | `status` | `RUNNING`, `SUCCESS` or `FAILED` |
| `etl_run` | `started_at`, `ended_at` | UTC-aware run timestamps |
| `etl_run` | `source_rows`, `accepted_rows`, `rejected_rows` | Batch reconciliation counts |
| `etl_run` | `reject_ratio` | Rejected source rows divided by all source rows |
| `etl_run` | `config_snapshot` | Credential-free JSON settings used for the run |
| `etl_run` | `error_message` | Truncated failure detail for unsuccessful runs |
