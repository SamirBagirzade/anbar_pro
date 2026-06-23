# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repo.

## Commands

```bash
# Run dev server
python manage.py runserver

# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test wms.masters

# Run a single test class or method
python manage.py test wms.masters.tests.ItemDeleteTests
python manage.py test wms.masters.tests.ItemDeleteTests.test_item_force_delete_removes_related

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Compile translations
python manage.py compilemessages

# Update translation strings
python manage.py makemessages -l az
```

## Deployment

```bash
./deploy.sh
```

Runs inside `.venv` virtualenv: pulls latest code, compiles translations, collects static files, restarts `anbar` systemd service.

## Environment

Configure via `.env` in project root. Required vars: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `DJANGO_SECRET_KEY`. Defaults work for local dev with `wms`/`wms` Postgres setup.

Precision constants in `settings.py`: `QUANT_QTY = "0.001"` (3 dp), `QUANT_MONEY = "0.01"` (2 dp), `DEFAULT_CURRENCY = "AZN"`.

## Architecture

Django 5 warehouse management system (WMS) for Azerbaijan. UI: server-rendered templates + HTMX for partial updates. DRF provides read/write REST API at `/api/`. App forced to Azerbaijani locale via `ForceLocaleMiddleware`.

### Apps

- **`wms.masters`** — master data: Vendor, Warehouse, OutgoingLocation, Unit, Item, VendorItem, attachments. Items auto-assign `internal_code` (`ITEM-XXXXXX`) on first save.
- **`wms.purchasing`** — purchase invoices (PurchaseHeader + PurchaseLine + attachments). Creating/editing purchase immediately posts to inventory.
- **`wms.issuing`** — goods issues to outgoing locations (IssueHeader + IssueLine + attachments). Links to source purchase via `source_purchase` FK.
- **`wms.inventory`** — stock ledger: StockBalance (running total per warehouse+item), StockMovement (immutable audit log), TransferHeader/Line, AdjustmentHeader/Line.
- **`wms.accounts`** — thin app, uses Django built-in auth.

### Inventory posting pattern

All stock mutations go through `wms/inventory/services.py`. Core function `apply_movement()` updates `StockBalance` and writes `StockMovement` inside single `select_for_update` transaction. Higher-level functions (`post_purchase`, `post_issue`, `post_transfer`, `post_adjustment`) call `apply_movement` per line. Edit workflows call matching `unpost_*` first to reverse, then re-post.

Negative stock blocked by default; superusers or users with `inventory.override_negative_stock` permission can override.

Deleting posted document uses `delete_purchase_with_inventory` / `delete_issue_with_inventory` — reverses stock and, for purchases, deactivates items no longer referenced anywhere (orphan cleanup).

### Forms and formsets

Purchase and issue create/edit views use Django inline formsets. Purchase lines allow free-text item entry (`item_name`) — form resolves or creates `Item` on save, with unit validation against `Unit` master. `IssueLineForm` uses custom `ItemSelectWithUnit` widget that attaches `data-unit` to each `<option>` so template can populate read-only unit column.

`build_issue_create_formset(extra=N)` dynamically sizes issue formset when pre-filling from source purchase.

### Permissions

All views require login, use `@permission_required` with Django model permissions. REST API uses `DjangoModelPermissions`. Superusers bypass all permission checks including negative-stock override.

### Templates

Base template: `wms/templates/base.html`. App templates in `wms/templates/<app>/`. Partial templates for HTMX responses prefixed with `_` (e.g., `_stock_table.html`). Warehouse stock page returns table partial when request has `HX-Request`.

### REST API

Registered at `/api/` via DRF `DefaultRouter`. Read-only viewsets for StockBalance and StockMovement; full CRUD for Transfers, Adjustments, Vendors, Warehouses, OutgoingLocations, Items, Purchases, and Issues.