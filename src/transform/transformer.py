"""Business transformations and data-quality enforcement."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


class DataQualityError(RuntimeError):
    """Raised when a transformation cannot preserve warehouse integrity."""


@dataclass
class TransformResult:
    tables: dict[str, pd.DataFrame]
    rejects: dict[str, pd.DataFrame] = field(default_factory=dict)
    input_rows: int = 0
    rejected_rows: int = 0

    @property
    def reject_ratio(self) -> float:
        return self.rejected_rows / self.input_rows if self.input_rows else 0.0


class WarehouseTransformer:
    @staticmethod
    def _dimension(
        frame: pd.DataFrame, natural_key: str, surrogate_key: str, columns: list[str]
    ) -> pd.DataFrame:
        clean = frame.drop_duplicates(subset=[natural_key], keep="last").copy()
        clean = clean.sort_values(natural_key).reset_index(drop=True)
        clean.insert(0, surrogate_key, np.arange(1, len(clean) + 1, dtype=int))
        return clean[[surrogate_key, *columns]]

    @staticmethod
    def _date_dimension(dates: pd.Series) -> pd.DataFrame:
        values = pd.to_datetime(dates, errors="coerce").dropna().drop_duplicates().sort_values()
        dim = pd.DataFrame({"full_date": values})
        dim["date_key"] = dim["full_date"].dt.strftime("%Y%m%d").astype(int)
        dim["day"] = dim["full_date"].dt.day
        dim["month"] = dim["full_date"].dt.month
        dim["month_name"] = dim["full_date"].dt.month_name()
        dim["quarter"] = dim["full_date"].dt.quarter
        dim["year"] = dim["full_date"].dt.year
        dim["week_of_year"] = dim["full_date"].dt.isocalendar().week.astype(int)
        dim["day_of_week"] = dim["full_date"].dt.day_name()
        dim["is_weekend"] = dim["full_date"].dt.dayofweek.ge(5)
        return dim[
            [
                "date_key",
                "full_date",
                "day",
                "month",
                "month_name",
                "quarter",
                "year",
                "week_of_year",
                "day_of_week",
                "is_weekend",
            ]
        ]

    @staticmethod
    def _reject(
        frame: pd.DataFrame, invalid: pd.Series, reason: str
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        rejected = frame.loc[invalid].copy()
        rejected["reject_reason"] = reason
        return frame.loc[~invalid].copy(), rejected

    @staticmethod
    def _map_key(
        frame: pd.DataFrame, dimension: pd.DataFrame, natural_key: str, surrogate_key: str
    ) -> pd.DataFrame:
        return frame.merge(
            dimension[[natural_key, surrogate_key]],
            on=natural_key,
            how="left",
            validate="many_to_one",
        )

    def transform(self, raw: dict[str, pd.DataFrame]) -> TransformResult:
        source = {name: frame.copy() for name, frame in raw.items()}
        input_rows = sum(len(frame) for frame in source.values())

        date_columns = {
            "projects": ["start_date", "planned_end_date"],
            "daily_progress": ["report_date"],
            "project_costs": ["cost_date"],
            "equipment_usage": ["usage_date"],
            "safety_incidents": ["incident_date"],
        }
        for table, columns in date_columns.items():
            for column in columns:
                source[table][column] = pd.to_datetime(source[table][column], errors="coerce")

        source["projects"]["project_name"] = source["projects"]["project_name"].fillna(
            "Unknown Project"
        )
        source["workers"]["trade"] = source["workers"]["trade"].fillna("General Worker")
        source["equipment"]["status"] = source["equipment"]["status"].fillna("Available")
        source["daily_progress"]["weather"] = source["daily_progress"]["weather"].fillna("Unknown")

        dim_project = self._dimension(
            source["projects"],
            "project_id",
            "project_key",
            [
                "project_id",
                "project_name",
                "project_type",
                "status",
                "start_date",
                "planned_end_date",
                "budget_myr",
                "client_name",
            ],
        )
        dim_site = self._dimension(
            source["sites"],
            "site_id",
            "site_key",
            [
                "site_id",
                "project_id",
                "site_name",
                "city",
                "state",
                "latitude",
                "longitude",
                "site_area_hectares",
            ],
        )
        dim_contractor = self._dimension(
            source["contractors"],
            "contractor_id",
            "contractor_key",
            ["contractor_id", "contractor_name", "specialization", "cidb_grade", "safety_rating"],
        )
        dim_worker = self._dimension(
            source["workers"],
            "worker_id",
            "worker_key",
            [
                "worker_id",
                "worker_name",
                "contractor_id",
                "trade",
                "skill_level",
                "employment_type",
            ],
        )
        dim_equipment = self._dimension(
            source["equipment"],
            "equipment_id",
            "equipment_key",
            [
                "equipment_id",
                "equipment_name",
                "equipment_type",
                "manufacturer",
                "model",
                "ownership_type",
                "status",
                "hourly_rate_myr",
            ],
        )
        dim_material = self._dimension(
            source["materials"],
            "material_id",
            "material_key",
            ["material_id", "material_name", "category", "unit", "unit_cost_myr", "supplier_name"],
        )

        all_dates = pd.concat(
            [
                source["daily_progress"]["report_date"],
                source["project_costs"]["cost_date"],
                source["equipment_usage"]["usage_date"],
                source["safety_incidents"]["incident_date"],
            ],
            ignore_index=True,
        )
        dim_date = self._date_dimension(all_dates)

        rejects: dict[str, pd.DataFrame] = {}
        progress = source["daily_progress"].drop_duplicates(
            subset=["project_id", "report_date"], keep="last"
        )
        invalid = (
            progress["report_date"].isna()
            | ~progress["planned_progress_pct"].between(0, 100)
            | ~progress["actual_progress_pct"].between(0, 100)
            | progress["workers_on_site"].lt(0)
        )
        progress, rejects["fact_project_progress"] = self._reject(
            progress, invalid, "invalid_date_progress_or_worker_count"
        )
        progress = self._map_key(progress, dim_project, "project_id", "project_key")
        progress["date_key"] = progress["report_date"].dt.strftime("%Y%m%d").astype(int)
        progress["schedule_variance_pct"] = (
            progress["actual_progress_pct"] - progress["planned_progress_pct"]
        ).round(2)
        progress["completion_ratio"] = (progress["actual_progress_pct"] / 100).round(4)
        progress.insert(0, "progress_key", np.arange(1, len(progress) + 1))
        fact_progress = progress[
            [
                "progress_key",
                "project_key",
                "date_key",
                "planned_progress_pct",
                "actual_progress_pct",
                "schedule_variance_pct",
                "completion_ratio",
                "work_completed_qty",
                "workers_on_site",
                "weather",
                "delay_hours",
            ]
        ]

        costs = source["project_costs"].drop_duplicates(subset=["cost_id"], keep="last")
        invalid = (
            costs["cost_date"].isna()
            | costs["planned_cost_myr"].lt(0)
            | costs["actual_cost_myr"].lt(0)
        )
        costs, rejects["fact_project_costs"] = self._reject(
            costs, invalid, "invalid_date_or_negative_cost"
        )
        costs = self._map_key(costs, dim_project, "project_id", "project_key")
        costs = self._map_key(costs, dim_contractor, "contractor_id", "contractor_key")
        costs = self._map_key(costs, dim_material, "material_id", "material_key")
        costs["date_key"] = costs["cost_date"].dt.strftime("%Y%m%d").astype(int)
        costs["budget_variance_myr"] = costs["planned_cost_myr"] - costs["actual_cost_myr"]
        costs.insert(0, "cost_key", np.arange(1, len(costs) + 1))
        fact_costs = costs[
            [
                "cost_key",
                "project_key",
                "date_key",
                "contractor_key",
                "material_key",
                "cost_category",
                "planned_cost_myr",
                "actual_cost_myr",
                "budget_variance_myr",
                "quantity",
            ]
        ]

        usage = source["equipment_usage"].drop_duplicates(subset=["usage_id"], keep="last")
        invalid = (
            usage["usage_date"].isna()
            | ~usage["operating_hours"].between(0, 24)
            | usage["idle_hours"].lt(0)
        )
        usage, rejects["fact_equipment_usage"] = self._reject(
            usage, invalid, "invalid_date_or_equipment_hours"
        )
        usage = self._map_key(usage, dim_project, "project_id", "project_key")
        usage = self._map_key(usage, dim_equipment, "equipment_id", "equipment_key")
        usage["date_key"] = usage["usage_date"].dt.strftime("%Y%m%d").astype(int)
        usage["utilization_pct"] = (
            np.where(
                usage["available_hours"].gt(0),
                usage["operating_hours"] / usage["available_hours"] * 100,
                0,
            )
            .clip(0, 100)
            .round(2)
        )
        usage.insert(0, "usage_key", np.arange(1, len(usage) + 1))
        fact_usage = usage[
            [
                "usage_key",
                "project_key",
                "equipment_key",
                "date_key",
                "operating_hours",
                "idle_hours",
                "available_hours",
                "utilization_pct",
                "fuel_consumed_litres",
                "maintenance_cost_myr",
            ]
        ]

        incidents = source["safety_incidents"].drop_duplicates(subset=["incident_id"], keep="last")
        invalid = (
            incidents["incident_date"].isna()
            | incidents["lost_time_days"].lt(0)
            | incidents["medical_cost_myr"].lt(0)
        )
        incidents, rejects["fact_safety_incidents"] = self._reject(
            incidents, invalid, "invalid_date_or_negative_measure"
        )
        incidents = self._map_key(incidents, dim_project, "project_id", "project_key")
        incidents = self._map_key(incidents, dim_site, "site_id", "site_key")
        incidents = self._map_key(incidents, dim_contractor, "contractor_id", "contractor_key")
        incidents = self._map_key(incidents, dim_worker, "worker_id", "worker_key")
        incidents["date_key"] = incidents["incident_date"].dt.strftime("%Y%m%d").astype(int)
        incidents.insert(0, "incident_key", np.arange(1, len(incidents) + 1))
        fact_incidents = incidents[
            [
                "incident_key",
                "project_key",
                "site_key",
                "contractor_key",
                "worker_key",
                "date_key",
                "incident_type",
                "severity",
                "lost_time_days",
                "medical_cost_myr",
                "reportable",
            ]
        ]

        foreign_key_frames = {
            "fact_project_progress": (fact_progress, ["project_key", "date_key"]),
            "fact_project_costs": (fact_costs, ["project_key", "date_key", "contractor_key"]),
            "fact_equipment_usage": (fact_usage, ["project_key", "equipment_key", "date_key"]),
            "fact_safety_incidents": (
                fact_incidents,
                ["project_key", "site_key", "contractor_key", "worker_key", "date_key"],
            ),
        }
        for name, (frame, key_columns) in foreign_key_frames.items():
            if frame[key_columns].isna().any().any():
                raise DataQualityError(f"Foreign key validation failed for {name}")

        rejected_rows = sum(len(frame) for frame in rejects.values())
        result = TransformResult(
            tables={
                "dim_project": dim_project,
                "dim_site": dim_site,
                "dim_contractor": dim_contractor,
                "dim_worker": dim_worker,
                "dim_equipment": dim_equipment,
                "dim_material": dim_material,
                "dim_date": dim_date,
                "fact_project_progress": fact_progress,
                "fact_project_costs": fact_costs,
                "fact_equipment_usage": fact_usage,
                "fact_safety_incidents": fact_incidents,
            },
            rejects=rejects,
            input_rows=input_rows,
            rejected_rows=rejected_rows,
        )
        return result
