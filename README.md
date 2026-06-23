# Anbar Pro

Warehouse management system (WMS) for Azerbaijan, built with Django 5.

## Features

- Purchase invoices with automatic inventory posting
- Goods issues to departments, projects, or clients
- Stock transfers between warehouses
- Stock adjustments
- Historical stock levels by date
- CSV and Excel export
- REST API
- Azerbaijani locale

## Tech Stack

- **Backend:** Django 5, Django REST Framework, PostgreSQL
- **Frontend:** Server-rendered templates, HTMX, Bootstrap
- **Auth:** Django built-in auth with model-level permissions

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit with your DB credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py compilemessages
python manage.py runserver
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_DB` | `wms` | Database name |
| `POSTGRES_USER` | `wms` | Database user |
| `POSTGRES_PASSWORD` | `wms` | Database password |
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `DJANGO_SECRET_KEY` | *(unsafe default)* | Django secret key |

## Deployment

```bash
./deploy.sh
```

Pulls latest code, compiles translations, collects static files, restarts the `anbar` systemd service.

## API

REST API available at `/api/`. Requires session authentication. Endpoints: vendors, warehouses, outgoing-locations, items, purchases, issues, transfers, adjustments, stock-balances, stock-movements.
