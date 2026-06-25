"""Generate deterministic, realistic Malaysian construction source data."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42


def _identifier(prefix: str, number: int, width: int = 4) -> str:
    return f"{prefix}{number:0{width}d}"


def generate_synthetic_data(output_dir: Path, seed: int = SEED) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    project_names = [
        "Kota Emerald Transit Hub",
        "Sungai Besi Urban Residences",
        "Penang South Coastal Link",
        "Cyberjaya Green Tech Park",
        "Rawang Integrated Township Phase 2",
        "Shah Alam Flood Mitigation Works",
        "Johor Bahru Rapid Transit Depot",
        "Klang Valley Hospital Expansion",
        "Seremban Industrial Logistics Park",
        "Puchong Smart Office Campus",
        "Kuantan Port Access Upgrade",
        "Iskandar Affordable Housing Precinct",
    ]
    types = [
        "Infrastructure",
        "Residential",
        "Infrastructure",
        "Commercial",
        "Township",
        "Infrastructure",
        "Infrastructure",
        "Healthcare",
        "Industrial",
        "Commercial",
        "Infrastructure",
        "Residential",
    ]
    cities = [
        ("Rawang", "Selangor", 3.3213, 101.5767),
        ("Kuala Lumpur", "W.P. Kuala Lumpur", 3.0622, 101.7080),
        ("Bayan Lepas", "Pulau Pinang", 5.2970, 100.2770),
        ("Cyberjaya", "Selangor", 2.9213, 101.6559),
        ("Rawang", "Selangor", 3.3370, 101.5720),
        ("Shah Alam", "Selangor", 3.0738, 101.5183),
        ("Johor Bahru", "Johor", 1.4927, 103.7414),
        ("Kuala Lumpur", "W.P. Kuala Lumpur", 3.1710, 101.7020),
        ("Seremban", "Negeri Sembilan", 2.7258, 101.9424),
        ("Puchong", "Selangor", 3.0327, 101.6188),
        ("Kuantan", "Pahang", 3.8077, 103.3260),
        ("Iskandar Puteri", "Johor", 1.4200, 103.6300),
    ]
    project_ids = [_identifier("PRJ", i, 3) for i in range(1, 13)]
    starts = pd.to_datetime(["2024-01-15", "2024-03-01", "2023-07-10", "2024-06-01"] * 3)
    budgets = rng.uniform(85_000_000, 1_250_000_000, 12).round(2)
    projects = pd.DataFrame(
        {
            "project_id": project_ids,
            "project_name": project_names,
            "project_type": types,
            "status": ["In Progress"] * 10 + ["At Risk", "In Progress"],
            "start_date": starts,
            "planned_end_date": starts + pd.to_timedelta(rng.integers(730, 1460, 12), unit="D"),
            "budget_myr": budgets,
            "client_name": rng.choice(
                ["Gamuda Land", "MRT Corp", "JKR Malaysia", "Private Developer", "State Authority"],
                12,
            ),
        }
    )

    sites = pd.DataFrame(
        [
            {
                "site_id": _identifier("SITE", index + 1, 3),
                "project_id": project_ids[index],
                "site_name": f"{project_names[index]} Main Site",
                "city": city,
                "state": state,
                "latitude": latitude + rng.normal(0, 0.005),
                "longitude": longitude + rng.normal(0, 0.005),
                "site_area_hectares": round(float(rng.uniform(4, 95)), 2),
            }
            for index, (city, state, latitude, longitude) in enumerate(cities)
        ]
    )

    specializations = [
        "Civil & Structural",
        "M&E",
        "Earthworks",
        "Rail Systems",
        "Roadworks",
        "Building Works",
        "Piling",
        "Safety Services",
        "Landscaping",
        "Utilities",
    ]
    contractors = pd.DataFrame(
        {
            "contractor_id": [_identifier("CON", i, 3) for i in range(1, 21)],
            "contractor_name": [
                f"{name} Engineering Sdn Bhd"
                for name in [
                    "Bina Teguh",
                    "Maju Jaya",
                    "Cekap",
                    "Metro",
                    "Wawasan",
                    "Puncak",
                    "Sentral",
                    "Dinamik",
                    "Perkasa",
                    "Gemilang",
                    "Ikhlas",
                    "Nusantara",
                    "Titan",
                    "Amanah",
                    "Progresif",
                    "Mega",
                    "Setia",
                    "Kencana",
                    "Prima",
                    "Vista",
                ]
            ],
            "specialization": [specializations[i % len(specializations)] for i in range(20)],
            "cidb_grade": rng.choice(["G5", "G6", "G7"], 20, p=[0.2, 0.25, 0.55]),
            "safety_rating": rng.uniform(72, 99, 20).round(1),
        }
    )

    first_names = [
        "Aiman",
        "Amir",
        "Hafiz",
        "Kumar",
        "Wei Jian",
        "Farid",
        "Daniel",
        "Siti",
        "Nurul",
        "Mei Ling",
        "Raj",
        "Azlan",
    ]
    last_names = [
        "Rahman",
        "Ismail",
        "Tan",
        "Lim",
        "Singh",
        "Yusof",
        "Abdullah",
        "Lee",
        "Kaur",
        "Ong",
        "Hassan",
    ]
    trades = [
        "Carpenter",
        "Electrician",
        "Welder",
        "Steel Fixer",
        "Crane Operator",
        "Site Supervisor",
        "Safety Officer",
        "Surveyor",
        "General Worker",
        "Plumber",
    ]
    worker_count = 150
    workers = pd.DataFrame(
        {
            "worker_id": [_identifier("WRK", i) for i in range(1, worker_count + 1)],
            "worker_name": [
                f"{rng.choice(first_names)} {rng.choice(last_names)}" for _ in range(worker_count)
            ],
            "contractor_id": rng.choice(contractors["contractor_id"], worker_count),
            "trade": rng.choice(trades, worker_count),
            "skill_level": rng.choice(
                ["Apprentice", "Skilled", "Senior", "Supervisor"],
                worker_count,
                p=[0.1, 0.55, 0.25, 0.1],
            ),
            "employment_type": rng.choice(
                ["Permanent", "Contract", "Subcontract"], worker_count, p=[0.25, 0.5, 0.25]
            ),
        }
    )

    equipment_types = [
        "Excavator",
        "Tower Crane",
        "Mobile Crane",
        "Bulldozer",
        "Compactor",
        "Concrete Pump",
        "Generator",
        "Dump Truck",
    ]
    manufacturers = ["Caterpillar", "Komatsu", "Hitachi", "Volvo", "Liebherr", "SANY", "JCB"]
    equipment_count = 60
    equipment = pd.DataFrame(
        {
            "equipment_id": [_identifier("EQP", i, 3) for i in range(1, equipment_count + 1)],
            "equipment_name": [
                f"{equipment_types[i % len(equipment_types)]} Unit {i + 1:02d}"
                for i in range(equipment_count)
            ],
            "equipment_type": [
                equipment_types[i % len(equipment_types)] for i in range(equipment_count)
            ],
            "manufacturer": rng.choice(manufacturers, equipment_count),
            "model": [f"M{rng.integers(200, 990)}" for _ in range(equipment_count)],
            "ownership_type": rng.choice(["Owned", "Leased", "Rented"], equipment_count),
            "status": rng.choice(
                ["Available", "In Use", "Maintenance"], equipment_count, p=[0.2, 0.72, 0.08]
            ),
            "hourly_rate_myr": rng.uniform(90, 850, equipment_count).round(2),
        }
    )

    material_specs = [
        ("Ready-Mix Concrete Grade 40", "Concrete", "m3", 365.0),
        ("Reinforcement Steel Y16", "Steel", "tonne", 3150.0),
        ("Structural Steel", "Steel", "tonne", 4800.0),
        ("Cement OPC", "Cement", "bag", 22.5),
        ("River Sand", "Aggregate", "tonne", 48.0),
        ("Crusher Run", "Aggregate", "tonne", 52.0),
        ("Precast Beam", "Precast", "unit", 14500.0),
        ("HDPE Pipe 600mm", "Utilities", "metre", 720.0),
        ("Electrical Cable 240mm", "Electrical", "metre", 185.0),
        ("Safety Barrier", "Safety", "unit", 295.0),
        ("Asphalt Wearing Course", "Roadworks", "tonne", 280.0),
        ("Glass Curtain Wall Panel", "Finishes", "m2", 1250.0),
    ]
    materials = pd.DataFrame(
        [
            {
                "material_id": _identifier("MAT", i + 1, 3),
                "material_name": name,
                "category": category,
                "unit": unit,
                "unit_cost_myr": cost,
                "supplier_name": f"Supplier {chr(65 + i)} Sdn Bhd",
            }
            for i, (name, category, unit, cost) in enumerate(material_specs)
        ]
    )

    dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    progress_rows: list[dict[str, object]] = []
    for project_id in project_ids:
        start_pct = rng.uniform(4, 28)
        target_pct = rng.uniform(58, 96)
        delay_factor = rng.uniform(0.88, 1.02)
        for day_index, date in enumerate(dates):
            planned = min(100, start_pct + (target_pct - start_pct) * day_index / (len(dates) - 1))
            seasonal_delay = 2.8 if date.month in (10, 11, 12) else 0
            actual = max(0, min(100, planned * delay_factor - seasonal_delay + rng.normal(0, 0.35)))
            progress_rows.append(
                {
                    "report_id": _identifier("DPR", len(progress_rows) + 1, 6),
                    "project_id": project_id,
                    "report_date": date,
                    "planned_progress_pct": round(planned, 2),
                    "actual_progress_pct": round(actual, 2),
                    "work_completed_qty": round(float(rng.uniform(35, 480)), 2),
                    "workers_on_site": int(rng.integers(35, 220)),
                    "weather": rng.choice(
                        ["Clear", "Cloudy", "Light Rain", "Heavy Rain"], p=[0.45, 0.3, 0.2, 0.05]
                    ),
                    "delay_hours": round(
                        float(max(0, rng.normal(0.8 if date.month >= 10 else 0.25, 0.8))), 2
                    ),
                }
            )
    daily_progress = pd.DataFrame(progress_rows)

    cost_rows: list[dict[str, object]] = []
    cost_categories = ["Labour", "Material", "Equipment", "Subcontract", "Site Overhead"]
    for project_index, project_id in enumerate(project_ids):
        daily_budget = budgets[project_index] / 1100
        for date in dates:
            category = rng.choice(cost_categories, p=[0.28, 0.35, 0.17, 0.12, 0.08])
            material_id: object = (
                rng.choice(materials["material_id"]) if category == "Material" else pd.NA
            )
            quantity = round(float(rng.uniform(5, 160)), 2) if category == "Material" else 0.0
            planned = daily_budget * rng.uniform(0.65, 1.35)
            actual = planned * rng.uniform(0.86, 1.22)
            cost_rows.append(
                {
                    "cost_id": _identifier("CST", len(cost_rows) + 1, 6),
                    "project_id": project_id,
                    "contractor_id": rng.choice(contractors["contractor_id"]),
                    "material_id": material_id,
                    "cost_date": date,
                    "cost_category": category,
                    "planned_cost_myr": round(planned, 2),
                    "actual_cost_myr": round(actual, 2),
                    "quantity": quantity,
                }
            )
    project_costs = pd.DataFrame(cost_rows)

    usage_rows: list[dict[str, object]] = []
    for equipment_index, equipment_id in enumerate(equipment["equipment_id"]):
        project_id = project_ids[equipment_index % len(project_ids)]
        selected_dates = rng.choice(dates, size=150, replace=False)
        for date in sorted(selected_dates):
            available = float(rng.choice([8, 10, 12, 16, 24], p=[0.2, 0.35, 0.25, 0.15, 0.05]))
            operating = float(rng.uniform(1.5, available))
            usage_rows.append(
                {
                    "usage_id": _identifier("USE", len(usage_rows) + 1, 6),
                    "project_id": project_id,
                    "equipment_id": equipment_id,
                    "usage_date": pd.Timestamp(date),
                    "operating_hours": round(operating, 2),
                    "idle_hours": round(max(0.0, available - operating), 2),
                    "available_hours": available,
                    "fuel_consumed_litres": round(operating * rng.uniform(5, 22), 2),
                    "maintenance_cost_myr": round(
                        float(rng.choice([0, 0, 0, rng.uniform(150, 3500)])), 2
                    ),
                }
            )
    equipment_usage = pd.DataFrame(usage_rows)

    incident_rows: list[dict[str, object]] = []
    severities = ["Near Miss", "Minor", "Moderate", "Major"]
    for i in range(180):
        project_index = int(rng.integers(0, len(project_ids)))
        severity = rng.choice(severities, p=[0.47, 0.35, 0.15, 0.03])
        worker = workers.iloc[int(rng.integers(0, len(workers)))]
        incident_rows.append(
            {
                "incident_id": _identifier("INC", i + 1, 5),
                "project_id": project_ids[project_index],
                "site_id": _identifier("SITE", project_index + 1, 3),
                "contractor_id": worker["contractor_id"],
                "worker_id": worker["worker_id"],
                "incident_date": rng.choice(dates),
                "incident_type": rng.choice(
                    [
                        "Slip/Trip",
                        "Equipment",
                        "Falling Object",
                        "Manual Handling",
                        "Electrical",
                        "Vehicle",
                    ]
                ),
                "severity": severity,
                "lost_time_days": int(
                    {"Near Miss": 0, "Minor": 0, "Moderate": 2, "Major": 12}[severity]
                    * rng.uniform(0.5, 1.5)
                ),
                "medical_cost_myr": round(
                    float(
                        {"Near Miss": 0, "Minor": 350, "Moderate": 2800, "Major": 18000}[severity]
                        * rng.uniform(0.6, 1.6)
                    ),
                    2,
                ),
                "reportable": severity in ("Moderate", "Major"),
            }
        )
    safety_incidents = pd.DataFrame(incident_rows)

    # Controlled quality defects exercise quarantine logic while staying far below 5%.
    daily_progress.loc[17, "actual_progress_pct"] = 103.5
    project_costs.loc[29, "actual_cost_myr"] = -250.0
    equipment_usage.loc[41, "operating_hours"] = 25.0

    frames = {
        "projects": projects,
        "sites": sites,
        "contractors": contractors,
        "workers": workers,
        "equipment": equipment,
        "materials": materials,
        "daily_progress": daily_progress,
        "project_costs": project_costs,
        "equipment_usage": equipment_usage,
        "safety_incidents": safety_incidents,
    }
    for name, frame in frames.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate construction source CSV files")
    parser.add_argument("--output", type=Path, default=Path("data/raw"))
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    frames = generate_synthetic_data(args.output, args.seed)
    print(f"Generated {sum(map(len, frames.values())):,} source rows in {args.output}")


if __name__ == "__main__":
    main()
