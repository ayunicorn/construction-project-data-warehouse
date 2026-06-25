CREATE SCHEMA IF NOT EXISTS {{DATABASE}}.{{SCHEMA}};

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.etl_run (
    run_id VARCHAR(36) PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    ended_at TIMESTAMP_TZ,
    source_rows NUMBER(38,0),
    accepted_rows NUMBER(38,0),
    rejected_rows NUMBER(38,0),
    reject_ratio NUMBER(8,6),
    error_message VARCHAR,
    config_snapshot VARIANT NOT NULL
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.dim_project (
    project_key NUMBER(38,0) PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    project_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL,
    start_date DATE NOT NULL,
    planned_end_date DATE NOT NULL,
    budget_myr NUMBER(18,2) NOT NULL,
    client_name VARCHAR(150) NOT NULL
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.dim_site (
    site_key NUMBER(38,0) PRIMARY KEY,
    site_id VARCHAR(20) NOT NULL,
    project_id VARCHAR(20) NOT NULL,
    site_name VARCHAR(200) NOT NULL,
    city VARCHAR(80) NOT NULL,
    state VARCHAR(80) NOT NULL,
    latitude NUMBER(10,7),
    longitude NUMBER(10,7),
    site_area_hectares NUMBER(12,2)
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.dim_contractor (
    contractor_key NUMBER(38,0) PRIMARY KEY,
    contractor_id VARCHAR(20) NOT NULL,
    contractor_name VARCHAR(200) NOT NULL,
    specialization VARCHAR(100),
    cidb_grade VARCHAR(10),
    safety_rating NUMBER(5,2)
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.dim_worker (
    worker_key NUMBER(38,0) PRIMARY KEY,
    worker_id VARCHAR(20) NOT NULL,
    worker_name VARCHAR(150) NOT NULL,
    contractor_id VARCHAR(20) NOT NULL,
    trade VARCHAR(80) NOT NULL,
    skill_level VARCHAR(40),
    employment_type VARCHAR(40)
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.dim_equipment (
    equipment_key NUMBER(38,0) PRIMARY KEY,
    equipment_id VARCHAR(20) NOT NULL,
    equipment_name VARCHAR(150) NOT NULL,
    equipment_type VARCHAR(80) NOT NULL,
    manufacturer VARCHAR(80),
    model VARCHAR(50),
    ownership_type VARCHAR(30),
    status VARCHAR(30),
    hourly_rate_myr NUMBER(12,2)
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.dim_material (
    material_key NUMBER(38,0) PRIMARY KEY,
    material_id VARCHAR(20) NOT NULL,
    material_name VARCHAR(160) NOT NULL,
    category VARCHAR(80),
    unit VARCHAR(30) NOT NULL,
    unit_cost_myr NUMBER(14,2),
    supplier_name VARCHAR(160)
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.dim_date (
    date_key NUMBER(38,0) PRIMARY KEY,
    full_date DATE NOT NULL,
    day NUMBER(2,0) NOT NULL,
    month NUMBER(2,0) NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    quarter NUMBER(1,0) NOT NULL,
    year NUMBER(4,0) NOT NULL,
    week_of_year NUMBER(2,0) NOT NULL,
    day_of_week VARCHAR(15) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.fact_project_progress (
    progress_key NUMBER(38,0) PRIMARY KEY,
    project_key NUMBER(38,0) NOT NULL,
    date_key NUMBER(38,0) NOT NULL,
    planned_progress_pct NUMBER(6,2) NOT NULL,
    actual_progress_pct NUMBER(6,2) NOT NULL,
    schedule_variance_pct NUMBER(7,2) NOT NULL,
    completion_ratio NUMBER(6,4) NOT NULL,
    work_completed_qty NUMBER(14,2) NOT NULL,
    workers_on_site NUMBER(38,0) NOT NULL,
    weather VARCHAR(30),
    delay_hours NUMBER(8,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.fact_project_costs (
    cost_key NUMBER(38,0) PRIMARY KEY,
    project_key NUMBER(38,0) NOT NULL,
    date_key NUMBER(38,0) NOT NULL,
    contractor_key NUMBER(38,0) NOT NULL,
    material_key NUMBER(38,0),
    cost_category VARCHAR(50) NOT NULL,
    planned_cost_myr NUMBER(18,2) NOT NULL,
    actual_cost_myr NUMBER(18,2) NOT NULL,
    budget_variance_myr NUMBER(18,2) NOT NULL,
    quantity NUMBER(16,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.fact_equipment_usage (
    usage_key NUMBER(38,0) PRIMARY KEY,
    project_key NUMBER(38,0) NOT NULL,
    equipment_key NUMBER(38,0) NOT NULL,
    date_key NUMBER(38,0) NOT NULL,
    operating_hours NUMBER(6,2) NOT NULL,
    idle_hours NUMBER(6,2) NOT NULL,
    available_hours NUMBER(6,2) NOT NULL,
    utilization_pct NUMBER(6,2) NOT NULL,
    fuel_consumed_litres NUMBER(12,2) NOT NULL,
    maintenance_cost_myr NUMBER(14,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.fact_safety_incidents (
    incident_key NUMBER(38,0) PRIMARY KEY,
    project_key NUMBER(38,0) NOT NULL,
    site_key NUMBER(38,0) NOT NULL,
    contractor_key NUMBER(38,0) NOT NULL,
    worker_key NUMBER(38,0),
    date_key NUMBER(38,0) NOT NULL,
    incident_type VARCHAR(80) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    lost_time_days NUMBER(38,0) NOT NULL,
    medical_cost_myr NUMBER(14,2) NOT NULL,
    reportable BOOLEAN NOT NULL
);

