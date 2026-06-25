# Power BI guide

## Connect

1. Start PostgreSQL and run the ETL using the README instructions.
2. In Power BI Desktop choose **Get data → PostgreSQL database**.
3. Server: `localhost:5432`; database: `construction_dw`.
4. Use Import mode for this portfolio dataset. Sign in with the values from `.env`.
5. Select the seven dimensions, four facts, and six `construction_dw.vw_*` views.

## Recommended pages

1. **Executive overview** — project cards, actual vs planned progress, cost variance, delay-risk matrix.
2. **Project controls** — progress S-curve, monthly actual/planned cost, delay-hours waterfall.
3. **Plant utilization** — utilization by equipment type, idle hours, fuel and maintenance cost.
4. **Materials** — quantity and realized unit cost by project/material.
5. **Safety** — incidents by severity, lost-time days, reportable incident trend.

## Suggested DAX measures

```DAX
Total Actual Cost = SUM(fact_project_costs[actual_cost_myr])
Total Planned Cost = SUM(fact_project_costs[planned_cost_myr])
Cost Variance = [Total Planned Cost] - [Total Actual Cost]
Cost Variance % = DIVIDE([Cost Variance], [Total Planned Cost])
Latest Actual Progress = MAX(fact_project_progress[actual_progress_pct])
Average Utilization % = AVERAGE(fact_equipment_usage[utilization_pct])
Reportable Incidents = CALCULATE(COUNTROWS(fact_safety_incidents), fact_safety_incidents[reportable] = TRUE())
```

Mark `dim_date` as the date table using `full_date`. Keep single-direction one-to-many relationships from dimensions to facts. Hide surrogate keys from report view.

