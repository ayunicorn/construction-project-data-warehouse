CREATE SCHEMA IF NOT EXISTS construction_dw;

CREATE TABLE IF NOT EXISTS construction_dw.etl_run (
    run_id UUID PRIMARY KEY,
    status VARCHAR(20) NOT NULL CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    source_rows BIGINT,
    accepted_rows BIGINT,
    rejected_rows BIGINT,
    reject_ratio NUMERIC(8,6),
    error_message TEXT,
    config_snapshot JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS construction_dw.dim_project (
    project_key INTEGER PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    project_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL,
    start_date DATE NOT NULL,
    planned_end_date DATE NOT NULL,
    budget_myr NUMERIC(18,2) NOT NULL CHECK (budget_myr >= 0),
    client_name VARCHAR(150) NOT NULL
);

CREATE TABLE IF NOT EXISTS construction_dw.dim_site (
    site_key INTEGER PRIMARY KEY,
    site_id VARCHAR(20) NOT NULL UNIQUE,
    project_id VARCHAR(20) NOT NULL,
    site_name VARCHAR(200) NOT NULL,
    city VARCHAR(80) NOT NULL,
    state VARCHAR(80) NOT NULL,
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    site_area_hectares NUMERIC(12,2)
);

CREATE TABLE IF NOT EXISTS construction_dw.dim_contractor (
    contractor_key INTEGER PRIMARY KEY,
    contractor_id VARCHAR(20) NOT NULL UNIQUE,
    contractor_name VARCHAR(200) NOT NULL,
    specialization VARCHAR(100),
    cidb_grade VARCHAR(10),
    safety_rating NUMERIC(5,2) CHECK (safety_rating BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS construction_dw.dim_worker (
    worker_key INTEGER PRIMARY KEY,
    worker_id VARCHAR(20) NOT NULL UNIQUE,
    worker_name VARCHAR(150) NOT NULL,
    contractor_id VARCHAR(20) NOT NULL,
    trade VARCHAR(80) NOT NULL,
    skill_level VARCHAR(40),
    employment_type VARCHAR(40)
);

CREATE TABLE IF NOT EXISTS construction_dw.dim_equipment (
    equipment_key INTEGER PRIMARY KEY,
    equipment_id VARCHAR(20) NOT NULL UNIQUE,
    equipment_name VARCHAR(150) NOT NULL,
    equipment_type VARCHAR(80) NOT NULL,
    manufacturer VARCHAR(80),
    model VARCHAR(50),
    ownership_type VARCHAR(30),
    status VARCHAR(30),
    hourly_rate_myr NUMERIC(12,2) CHECK (hourly_rate_myr >= 0)
);

CREATE TABLE IF NOT EXISTS construction_dw.dim_material (
    material_key INTEGER PRIMARY KEY,
    material_id VARCHAR(20) NOT NULL UNIQUE,
    material_name VARCHAR(160) NOT NULL,
    category VARCHAR(80),
    unit VARCHAR(30) NOT NULL,
    unit_cost_myr NUMERIC(14,2) CHECK (unit_cost_myr >= 0),
    supplier_name VARCHAR(160)
);

CREATE TABLE IF NOT EXISTS construction_dw.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    quarter SMALLINT NOT NULL,
    year SMALLINT NOT NULL,
    week_of_year SMALLINT NOT NULL,
    day_of_week VARCHAR(15) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS construction_dw.fact_project_progress (
    progress_key BIGINT PRIMARY KEY,
    project_key INTEGER NOT NULL REFERENCES construction_dw.dim_project(project_key),
    date_key INTEGER NOT NULL REFERENCES construction_dw.dim_date(date_key),
    planned_progress_pct NUMERIC(6,2) NOT NULL CHECK (planned_progress_pct BETWEEN 0 AND 100),
    actual_progress_pct NUMERIC(6,2) NOT NULL CHECK (actual_progress_pct BETWEEN 0 AND 100),
    schedule_variance_pct NUMERIC(7,2) NOT NULL,
    completion_ratio NUMERIC(6,4) NOT NULL CHECK (completion_ratio BETWEEN 0 AND 1),
    work_completed_qty NUMERIC(14,2) NOT NULL,
    workers_on_site INTEGER NOT NULL CHECK (workers_on_site >= 0),
    weather VARCHAR(30),
    delay_hours NUMERIC(8,2) NOT NULL CHECK (delay_hours >= 0),
    CONSTRAINT uq_progress_project_date UNIQUE (project_key, date_key)
);

CREATE TABLE IF NOT EXISTS construction_dw.fact_project_costs (
    cost_key BIGINT PRIMARY KEY,
    project_key INTEGER NOT NULL REFERENCES construction_dw.dim_project(project_key),
    date_key INTEGER NOT NULL REFERENCES construction_dw.dim_date(date_key),
    contractor_key INTEGER NOT NULL REFERENCES construction_dw.dim_contractor(contractor_key),
    material_key INTEGER REFERENCES construction_dw.dim_material(material_key),
    cost_category VARCHAR(50) NOT NULL,
    planned_cost_myr NUMERIC(18,2) NOT NULL CHECK (planned_cost_myr >= 0),
    actual_cost_myr NUMERIC(18,2) NOT NULL CHECK (actual_cost_myr >= 0),
    budget_variance_myr NUMERIC(18,2) NOT NULL,
    quantity NUMERIC(16,2) NOT NULL CHECK (quantity >= 0)
);

CREATE TABLE IF NOT EXISTS construction_dw.fact_equipment_usage (
    usage_key BIGINT PRIMARY KEY,
    project_key INTEGER NOT NULL REFERENCES construction_dw.dim_project(project_key),
    equipment_key INTEGER NOT NULL REFERENCES construction_dw.dim_equipment(equipment_key),
    date_key INTEGER NOT NULL REFERENCES construction_dw.dim_date(date_key),
    operating_hours NUMERIC(6,2) NOT NULL CHECK (operating_hours BETWEEN 0 AND 24),
    idle_hours NUMERIC(6,2) NOT NULL CHECK (idle_hours BETWEEN 0 AND 24),
    available_hours NUMERIC(6,2) NOT NULL CHECK (available_hours BETWEEN 0 AND 24),
    utilization_pct NUMERIC(6,2) NOT NULL CHECK (utilization_pct BETWEEN 0 AND 100),
    fuel_consumed_litres NUMERIC(12,2) NOT NULL CHECK (fuel_consumed_litres >= 0),
    maintenance_cost_myr NUMERIC(14,2) NOT NULL CHECK (maintenance_cost_myr >= 0),
    CONSTRAINT uq_usage_equipment_project_date UNIQUE (equipment_key, project_key, date_key)
);

CREATE TABLE IF NOT EXISTS construction_dw.fact_safety_incidents (
    incident_key BIGINT PRIMARY KEY,
    project_key INTEGER NOT NULL REFERENCES construction_dw.dim_project(project_key),
    site_key INTEGER NOT NULL REFERENCES construction_dw.dim_site(site_key),
    contractor_key INTEGER NOT NULL REFERENCES construction_dw.dim_contractor(contractor_key),
    worker_key INTEGER REFERENCES construction_dw.dim_worker(worker_key),
    date_key INTEGER NOT NULL REFERENCES construction_dw.dim_date(date_key),
    incident_type VARCHAR(80) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    lost_time_days INTEGER NOT NULL CHECK (lost_time_days >= 0),
    medical_cost_myr NUMERIC(14,2) NOT NULL CHECK (medical_cost_myr >= 0),
    reportable BOOLEAN NOT NULL
);

-- Indexes mirror the common Power BI filters and view joins.
CREATE INDEX IF NOT EXISTS ix_progress_date_project
    ON construction_dw.fact_project_progress(date_key, project_key)
    INCLUDE (planned_progress_pct, actual_progress_pct, delay_hours);
CREATE INDEX IF NOT EXISTS ix_costs_project_date
    ON construction_dw.fact_project_costs(project_key, date_key)
    INCLUDE (planned_cost_myr, actual_cost_myr, budget_variance_myr);
CREATE INDEX IF NOT EXISTS ix_costs_material_project
    ON construction_dw.fact_project_costs(material_key, project_key)
    WHERE material_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_usage_project_date
    ON construction_dw.fact_equipment_usage(project_key, date_key)
    INCLUDE (equipment_key, operating_hours, utilization_pct);
CREATE INDEX IF NOT EXISTS ix_incidents_project_date
    ON construction_dw.fact_safety_incidents(project_key, date_key)
    INCLUDE (severity, lost_time_days, medical_cost_myr);
CREATE INDEX IF NOT EXISTS ix_incidents_reportable
    ON construction_dw.fact_safety_incidents(date_key, project_key)
    WHERE reportable IS TRUE;
CREATE INDEX IF NOT EXISTS ix_etl_run_status_started
    ON construction_dw.etl_run(status, started_at DESC);
