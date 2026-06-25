# Data model

```mermaid
erDiagram
    DIM_PROJECT ||--o{ FACT_PROJECT_PROGRESS : tracks
    DIM_DATE ||--o{ FACT_PROJECT_PROGRESS : dated
    DIM_PROJECT ||--o{ FACT_PROJECT_COSTS : incurs
    DIM_DATE ||--o{ FACT_PROJECT_COSTS : dated
    DIM_CONTRACTOR ||--o{ FACT_PROJECT_COSTS : bills
    DIM_MATERIAL o|--o{ FACT_PROJECT_COSTS : consumes
    DIM_PROJECT ||--o{ FACT_EQUIPMENT_USAGE : uses
    DIM_EQUIPMENT ||--o{ FACT_EQUIPMENT_USAGE : operates
    DIM_DATE ||--o{ FACT_EQUIPMENT_USAGE : dated
    DIM_PROJECT ||--o{ FACT_SAFETY_INCIDENTS : records
    DIM_SITE ||--o{ FACT_SAFETY_INCIDENTS : occurs_at
    DIM_CONTRACTOR ||--o{ FACT_SAFETY_INCIDENTS : responsible
    DIM_WORKER o|--o{ FACT_SAFETY_INCIDENTS : involves
    DIM_DATE ||--o{ FACT_SAFETY_INCIDENTS : dated
```

## Fact grain

| Fact table | Grain |
|---|---|
| `fact_project_progress` | One project per report date |
| `fact_project_costs` | One project cost transaction/category per date |
| `fact_equipment_usage` | One equipment item on one project per date |
| `fact_safety_incidents` | One reported safety incident |

