CREATE OR REPLACE VIEW {{DATABASE}}.{{SCHEMA}}.vw_project_progress_summary AS
SELECT
    p.project_id,
    p.project_name,
    p.project_type,
    MAX(d.full_date) AS latest_report_date,
    ROUND(MAX(f.planned_progress_pct), 2) AS planned_progress_pct,
    ROUND(MAX(f.actual_progress_pct), 2) AS actual_progress_pct,
    ROUND(MAX(f.actual_progress_pct) - MAX(f.planned_progress_pct), 2) AS schedule_variance_pct,
    SUM(f.delay_hours) AS total_delay_hours,
    ROUND(AVG(f.workers_on_site), 0) AS avg_workers_on_site
FROM {{DATABASE}}.{{SCHEMA}}.fact_project_progress f
JOIN {{DATABASE}}.{{SCHEMA}}.dim_project p USING (project_key)
JOIN {{DATABASE}}.{{SCHEMA}}.dim_date d USING (date_key)
GROUP BY p.project_id, p.project_name, p.project_type;

CREATE OR REPLACE VIEW {{DATABASE}}.{{SCHEMA}}.vw_budget_vs_actual AS
SELECT
    p.project_id,
    p.project_name,
    p.budget_myr,
    SUM(f.planned_cost_myr) AS planned_cost_myr,
    SUM(f.actual_cost_myr) AS actual_cost_myr,
    SUM(f.budget_variance_myr) AS budget_variance_myr,
    ROUND(SUM(f.actual_cost_myr) / NULLIF(p.budget_myr, 0) * 100, 2) AS budget_consumed_pct
FROM {{DATABASE}}.{{SCHEMA}}.fact_project_costs f
JOIN {{DATABASE}}.{{SCHEMA}}.dim_project p USING (project_key)
GROUP BY p.project_id, p.project_name, p.budget_myr;

CREATE OR REPLACE VIEW {{DATABASE}}.{{SCHEMA}}.vw_equipment_utilization AS
SELECT
    p.project_name,
    e.equipment_id,
    e.equipment_name,
    e.equipment_type,
    ROUND(AVG(f.utilization_pct), 2) AS avg_utilization_pct,
    SUM(f.operating_hours) AS total_operating_hours,
    SUM(f.idle_hours) AS total_idle_hours,
    SUM(f.fuel_consumed_litres) AS fuel_consumed_litres,
    SUM(f.maintenance_cost_myr) AS maintenance_cost_myr
FROM {{DATABASE}}.{{SCHEMA}}.fact_equipment_usage f
JOIN {{DATABASE}}.{{SCHEMA}}.dim_project p USING (project_key)
JOIN {{DATABASE}}.{{SCHEMA}}.dim_equipment e USING (equipment_key)
GROUP BY p.project_name, e.equipment_id, e.equipment_name, e.equipment_type;

CREATE OR REPLACE VIEW {{DATABASE}}.{{SCHEMA}}.vw_material_consumption AS
SELECT
    p.project_name,
    m.material_id,
    m.material_name,
    m.category,
    m.unit,
    SUM(f.quantity) AS quantity_consumed,
    SUM(f.actual_cost_myr) AS actual_material_cost_myr,
    ROUND(SUM(f.actual_cost_myr) / NULLIF(SUM(f.quantity), 0), 2) AS realized_unit_cost_myr
FROM {{DATABASE}}.{{SCHEMA}}.fact_project_costs f
JOIN {{DATABASE}}.{{SCHEMA}}.dim_project p USING (project_key)
JOIN {{DATABASE}}.{{SCHEMA}}.dim_material m USING (material_key)
WHERE f.cost_category = 'Material'
GROUP BY p.project_name, m.material_id, m.material_name, m.category, m.unit;

CREATE OR REPLACE VIEW {{DATABASE}}.{{SCHEMA}}.vw_safety_incident_summary AS
SELECT
    p.project_name,
    f.severity,
    COUNT(*) AS incident_count,
    SUM(f.lost_time_days) AS lost_time_days,
    SUM(f.medical_cost_myr) AS medical_cost_myr,
    COUNT_IF(f.reportable) AS reportable_incidents
FROM {{DATABASE}}.{{SCHEMA}}.fact_safety_incidents f
JOIN {{DATABASE}}.{{SCHEMA}}.dim_project p USING (project_key)
GROUP BY p.project_name, f.severity;

CREATE OR REPLACE VIEW {{DATABASE}}.{{SCHEMA}}.vw_project_delay_risk AS
WITH latest AS (
    SELECT
        f.project_key,
        f.actual_progress_pct,
        f.schedule_variance_pct,
        d.full_date
    FROM {{DATABASE}}.{{SCHEMA}}.fact_project_progress f
    JOIN {{DATABASE}}.{{SCHEMA}}.dim_date d USING (date_key)
    QUALIFY ROW_NUMBER() OVER (PARTITION BY f.project_key ORDER BY d.full_date DESC) = 1
), delay_totals AS (
    SELECT project_key, SUM(delay_hours) AS delay_hours
    FROM {{DATABASE}}.{{SCHEMA}}.fact_project_progress
    GROUP BY project_key
)
SELECT
    p.project_id,
    p.project_name,
    l.full_date AS assessment_date,
    l.actual_progress_pct,
    l.schedule_variance_pct,
    dt.delay_hours,
    CASE
        WHEN l.schedule_variance_pct <= -10 OR dt.delay_hours >= 500 THEN 'High'
        WHEN l.schedule_variance_pct <= -5 OR dt.delay_hours >= 250 THEN 'Medium'
        ELSE 'Low'
    END AS delay_risk
FROM latest l
JOIN delay_totals dt USING (project_key)
JOIN {{DATABASE}}.{{SCHEMA}}.dim_project p USING (project_key);

