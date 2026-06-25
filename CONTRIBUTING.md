# Contributing

Thank you for improving this learning project. Keep changes small, synthetic and easy to explain.

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pre-commit install
Copy-Item .env.example .env
```

## Workflow

1. Create a focused branch.
2. Add or update tests with behavior changes.
3. Run `ruff check .`, `ruff format --check .` and `pytest -m "not integration"`.
4. If PostgreSQL is available, set `TEST_DATABASE_URL` and run `pytest -m integration`.
5. Update documentation when configuration, schemas or user commands change.

## Data safety

- Commit only generated synthetic data.
- Never add real names, contact details, commercial records, credentials or client documents.
- Never commit `.env`, database dumps, logs or Power BI files containing connection secrets.
- Preserve deterministic generation by using an explicit random seed.

Pull requests should explain the problem, design choice, tests run and any schema impact.

