-- Every query should return zero rows (except the reject ratio query, which returns one passing row).
SELECT project_key, date_key, COUNT(*)
FROM construction_dw.fact_project_progress
GROUP BY project_key, date_key HAVING COUNT(*) > 1;

SELECT * FROM construction_dw.fact_project_progress
WHERE planned_progress_pct NOT BETWEEN 0 AND 100 OR actual_progress_pct NOT BETWEEN 0 AND 100;

SELECT * FROM construction_dw.fact_project_costs
WHERE planned_cost_myr < 0 OR actual_cost_myr < 0;

SELECT * FROM construction_dw.fact_equipment_usage
WHERE operating_hours NOT BETWEEN 0 AND 24;

SELECT f.* FROM construction_dw.fact_project_progress f
LEFT JOIN construction_dw.dim_project p USING (project_key)
LEFT JOIN construction_dw.dim_date d USING (date_key)
WHERE p.project_key IS NULL OR d.date_key IS NULL;

