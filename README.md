# Sector.ROCPrompt Backend

FastAPI backend foundation for importing the frozen Pharmacy Production Dataset v1.0 into PostgreSQL and exposing read APIs.

## Prerequisites

- Python 3.11+
- PostgreSQL
- Pharmacy_Production_Dataset_v1.0.xlsx
- Pharmacy_Production_Data_Dictionary_v1.0.xlsx for reference

## Setup

```powershell
cd C:\Development\Sector.ROCPrompt\backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set `DATABASE_URL`. Do not hardcode database credentials in source.

## Migrations

```powershell
alembic upgrade head
```

## Import Dataset

```powershell
python scripts\import_pharmacy_dataset.py "C:\Users\megar\Documents\RocPrompt DOC\Pharmacy Reasearch\Pharmacy_Production_Dataset_v1.0.xlsx" --mode upsert
```

Use `--mode truncate` for truncate-and-load reloads.

## Run API

```powershell
uvicorn app.main:app --reload
```

## Endpoints

- `GET /health`
- `GET /sectors`
- `GET /sub-sectors`
- `GET /laws`
- `GET /provisions`
- `GET /compliance-requirements`
- `GET /audit-procedures`
- `GET /evidence`
- `GET /observations`

Supported filters include `sector_id`, `sub_sector_id`, `law_id`, `compliance_area_id`, `provision_id`, `compliance_id`, `audit_id`, `origin`, `risk_level`, and `evidence_type` where applicable.

## Tests

```powershell
pytest
```
