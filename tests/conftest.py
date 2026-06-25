from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def valid_raw() -> dict[str, pd.DataFrame]:
    return {
        "projects": pd.DataFrame(
            [
                {
                    "project_id": "PRJ001",
                    "project_name": "Test Project",
                    "project_type": "Infrastructure",
                    "status": "In Progress",
                    "start_date": "2025-01-01",
                    "planned_end_date": "2026-01-01",
                    "budget_myr": 1_000_000,
                    "client_name": "Test Client",
                }
            ]
        ),
        "sites": pd.DataFrame(
            [
                {
                    "site_id": "SITE001",
                    "project_id": "PRJ001",
                    "site_name": "Test Site",
                    "city": "Kuala Lumpur",
                    "state": "W.P. Kuala Lumpur",
                    "latitude": 3.1,
                    "longitude": 101.7,
                    "site_area_hectares": 10,
                }
            ]
        ),
        "contractors": pd.DataFrame(
            [
                {
                    "contractor_id": "CON001",
                    "contractor_name": "Test Contractor",
                    "specialization": "Civil",
                    "cidb_grade": "G7",
                    "safety_rating": 95,
                }
            ]
        ),
        "workers": pd.DataFrame(
            [
                {
                    "worker_id": "WRK0001",
                    "worker_name": "Test Worker",
                    "contractor_id": "CON001",
                    "trade": "Welder",
                    "skill_level": "Skilled",
                    "employment_type": "Contract",
                }
            ]
        ),
        "equipment": pd.DataFrame(
            [
                {
                    "equipment_id": "EQP001",
                    "equipment_name": "Excavator 1",
                    "equipment_type": "Excavator",
                    "manufacturer": "Test",
                    "model": "X1",
                    "ownership_type": "Owned",
                    "status": "In Use",
                    "hourly_rate_myr": 250,
                }
            ]
        ),
        "materials": pd.DataFrame(
            [
                {
                    "material_id": "MAT001",
                    "material_name": "Concrete",
                    "category": "Concrete",
                    "unit": "m3",
                    "unit_cost_myr": 350,
                    "supplier_name": "Supplier",
                }
            ]
        ),
        "daily_progress": pd.DataFrame(
            [
                {
                    "report_id": "DPR000001",
                    "project_id": "PRJ001",
                    "report_date": "2025-01-02",
                    "planned_progress_pct": 10,
                    "actual_progress_pct": 8,
                    "work_completed_qty": 100,
                    "workers_on_site": 50,
                    "weather": "Clear",
                    "delay_hours": 1,
                }
            ]
        ),
        "project_costs": pd.DataFrame(
            [
                {
                    "cost_id": "CST000001",
                    "project_id": "PRJ001",
                    "contractor_id": "CON001",
                    "material_id": "MAT001",
                    "cost_date": "2025-01-02",
                    "cost_category": "Material",
                    "planned_cost_myr": 1000,
                    "actual_cost_myr": 1100,
                    "quantity": 3,
                }
            ]
        ),
        "equipment_usage": pd.DataFrame(
            [
                {
                    "usage_id": "USE000001",
                    "project_id": "PRJ001",
                    "equipment_id": "EQP001",
                    "usage_date": "2025-01-02",
                    "operating_hours": 8,
                    "idle_hours": 2,
                    "available_hours": 10,
                    "fuel_consumed_litres": 60,
                    "maintenance_cost_myr": 0,
                }
            ]
        ),
        "safety_incidents": pd.DataFrame(
            [
                {
                    "incident_id": "INC00001",
                    "project_id": "PRJ001",
                    "site_id": "SITE001",
                    "contractor_id": "CON001",
                    "worker_id": "WRK0001",
                    "incident_date": "2025-01-02",
                    "incident_type": "Near Miss",
                    "severity": "Near Miss",
                    "lost_time_days": 0,
                    "medical_cost_myr": 0,
                    "reportable": False,
                }
            ]
        ),
    }
