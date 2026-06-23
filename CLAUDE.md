# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## Environment

Configure via `.env` in the project root. Required vars: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `DJANGO_SECRET_KEY`. Defaults work for local dev with a `wms`/`wms` Postgres setup.

Precision constants are in `settings.py`: `QUANT_QTY = "0.001"` (3 dp), `QUANT_MONEY = "0.01"` (2 dp), `DEFAULT_CURRENCY = "AZN"`.

## Architecture

This is a Django 5 warehouse management system (WMS) for Azerbaijan. UI is server-rendered templates with HTMX for partial updates. DRF provides a read/write REST API at `/api/`. The app is always forced to Azerbaijani locale via `ForceLocaleMiddleware`.

### Apps

- **`wms.masters`** — master data: Vendor, Warehouse, OutgoingLocation, Unit, Item, VendorItem, attachments. Items auto-assign `internal_code` (`ITEM-XXXXXX`) on first save.
- **`wms.purchasing`** — purchase invoices (PurchaseHeader + PurchaseLine + attachments). Creating/editing a purchase immediately posts it to inventory.
- **`wms.issuing`** — goods issues to outgoing locations (IssueHeader + IssueLine + attachments). Can be linked to a source purchase via `source_purchase` FK.
- **`wms.inventory`** — stock ledger: StockBalance (running total per warehouse+item), StockMovement (immutable audit log), TransferHeader/Line, AdjustmentHeader/Line.
- **`wms.accounts`** — thin app, uses Django's built-in auth.

### Inventory posting pattern

All stock mutations go through `wms/inventory/services.py`. The core function is `apply_movement()` which updates `StockBalance` and writes a `StockMovement` record inside a single `select_for_update` transaction. Higher-level functions (`post_purchase`, `post_issue`, `post_transfer`, `post_adjustment`) call `apply_movement` per line. Edit workflows call the matching `unpost_*` function first to reverse movements, then re-post.

Negative stock is blocked by default; superusers or users with the `inventory.override_negative_stock` permission can override it.

Deleting a posted document uses `delete_purchase_with_inventory` / `delete_issue_with_inventory` which reverses stock and, for purchases, deactivates items that are no longer referenced anywhere (orphan cleanup).

### Forms and formsets

Purchase and issue create/edit views use Django inline formsets. Purchase lines allow free-text item entry (`item_name`) — the form resolves or creates the `Item` on save, with unit validation against the `Unit` master. The `IssueLineForm` uses a custom `ItemSelectWithUnit` widget that attaches `data-unit` to each `<option>` so the template can populate a read-only unit column.

`build_issue_create_formset(extra=N)` dynamically sizes the issue formset when pre-filling from a source purchase.

### Permissions

All views require login and use `@permission_required` with Django model permissions. The REST API uses `DjangoModelPermissions`. Superusers bypass all permission checks including negative-stock override.

### Templates

Base template: `wms/templates/base.html`. App templates live in `wms/templates/<app>/`. Partial templates for HTMX responses are prefixed with `_` (e.g., `_stock_table.html`). The warehouse stock page responds with just the table partial when the request has `HX-Request`.

### REST API

Registered at `/api/` via DRF `DefaultRouter`. Read-only viewsets for StockBalance and StockMovement; full CRUD for Transfers, Adjustments, Vendors, Warehouses, OutgoingLocations, Items, Purchases, and Issues.
