from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from wms.masters.models import Vendor, Warehouse, Item
from wms.purchasing.models import PurchaseHeader, PurchaseLine
from wms.inventory.models import StockMovement, StockBalance
from wms.inventory.services import post_purchase, delete_purchase_with_inventory, unpost_purchase_inventory
from wms.purchasing.forms import PurchaseLineFormSet


class ItemDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@example.com", "pass")
        self.client.login(username="admin", password="pass")
        self.vendor = Vendor.objects.create(name="Vendor")
        self.warehouse = Warehouse.objects.create(name="WH", location="L")
        self.item = Item.objects.create(name="Item", unit="pcs")

        purchase = PurchaseHeader.objects.create(
            vendor=self.vendor,
            warehouse=self.warehouse,
            invoice_no="",
            invoice_date="2026-02-06",
            created_by=self.user,
        )
        PurchaseLine.objects.create(
            purchase=purchase,
            item=self.item,
            qty=Decimal("5"),
            unit_price=Decimal("10.00"),
            discount=Decimal("0"),
            tax_rate=Decimal("0"),
            line_total=Decimal("50.00"),
        )
        post_purchase(purchase, self.user)

    def test_item_delete_blocked_without_force(self):
        url = reverse("item_delete", args=[self.item.id])
        self.client.post(url)
        self.assertTrue(Item.objects.filter(id=self.item.id).exists())

    def test_item_force_delete_removes_related(self):
        url = reverse("item_delete", args=[self.item.id])
        self.client.post(url, {"force": "1"})
        self.assertFalse(Item.objects.filter(id=self.item.id).exists())
        self.assertEqual(StockMovement.objects.count(), 0)
        self.assertEqual(StockBalance.objects.count(), 0)
        self.assertEqual(PurchaseLine.objects.count(), 0)


class PurchaseDeleteInventoryCleanupTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin2", "admin2@example.com", "pass")
        self.vendor = Vendor.objects.create(name="Vendor 2")
        self.warehouse = Warehouse.objects.create(name="WH2", location="L2")

    def test_delete_purchase_deactivates_orphan_item(self):
        item = Item.objects.create(name="Orphan Item", unit="pcs")
        purchase = PurchaseHeader.objects.create(
            vendor=self.vendor,
            warehouse=self.warehouse,
            invoice_no="INV-1",
            invoice_date="2026-02-10",
            created_by=self.user,
        )
        PurchaseLine.objects.create(
            purchase=purchase,
            item=item,
            qty=Decimal("2"),
            unit_price=Decimal("7.00"),
            discount=Decimal("0"),
            tax_rate=Decimal("0"),
            line_total=Decimal("14.00"),
        )
        post_purchase(purchase, self.user)

        delete_purchase_with_inventory(purchase)
        item.refresh_from_db()
        self.assertFalse(item.is_active)

    def test_delete_purchase_keeps_item_if_other_invoice_exists(self):
        item = Item.objects.create(name="Shared Item", unit="pcs")
        purchase1 = PurchaseHeader.objects.create(
            vendor=self.vendor,
            warehouse=self.warehouse,
            invoice_no="INV-2",
            invoice_date="2026-02-11",
            created_by=self.user,
        )
        purchase2 = PurchaseHeader.objects.create(
            vendor=self.vendor,
            warehouse=self.warehouse,
            invoice_no="INV-3",
            invoice_date="2026-02-12",
            created_by=self.user,
        )
        PurchaseLine.objects.create(
            purchase=purchase1,
            item=item,
            qty=Decimal("1"),
            unit_price=Decimal("5.00"),
            discount=Decimal("0"),
            tax_rate=Decimal("0"),
            line_total=Decimal("5.00"),
        )
        PurchaseLine.objects.create(
            purchase=purchase2,
            item=item,
            qty=Decimal("3"),
            unit_price=Decimal("6.00"),
            discount=Decimal("0"),
            tax_rate=Decimal("0"),
            line_total=Decimal("18.00"),
        )
        post_purchase(purchase1, self.user)
        post_purchase(purchase2, self.user)

        delete_purchase_with_inventory(purchase1)
        item.refresh_from_db()
        self.assertTrue(item.is_active)


class PurchaseEditInventoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin3", "admin3@example.com", "pass")
        self.vendor = Vendor.objects.create(name="Vendor 3")
        self.warehouse = Warehouse.objects.create(name="WH3", location="L3")
        self.item = Item.objects.create(name="Edit Item", unit="pcs")

    def test_edit_purchase_reposts_inventory(self):
        purchase = PurchaseHeader.objects.create(
            vendor=self.vendor,
            warehouse=self.warehouse,
            invoice_no="INV-EDIT",
            invoice_date="2026-02-13",
            created_by=self.user,
        )
        PurchaseLine.objects.create(
            purchase=purchase,
            item=self.item,
            qty=Decimal("5"),
            unit_price=Decimal("4.00"),
            discount=Decimal("0"),
            tax_rate=Decimal("0"),
            line_total=Decimal("20.00"),
        )
        post_purchase(purchase, self.user)

        unpost_purchase_inventory(purchase)
        purchase.lines.all().delete()
        PurchaseLine.objects.create(
            purchase=purchase,
            item=self.item,
            qty=Decimal("2"),
            unit_price=Decimal("4.50"),
            discount=Decimal("0"),
            tax_rate=Decimal("0"),
            line_total=Decimal("9.00"),
        )
        post_purchase(purchase, self.user)

        balance = StockBalance.objects.get(warehouse=self.warehouse, item=self.item)
        self.assertEqual(balance.on_hand, Decimal("2.000"))


class RepurchaseReactivatesItemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin4", "admin4@example.com", "pass")
        self.client.login(username="admin4", password="pass")
        self.vendor = Vendor.objects.create(name="Vendor 4")
        self.warehouse = Warehouse.objects.create(name="WH4", location="L4")

    def test_repurchase_same_name_reactivates_item(self):
        item = Item.objects.create(name="aa", unit="pcs", is_active=True)
        purchase1 = PurchaseHeader.objects.create(
            vendor=self.vendor,
            warehouse=self.warehouse,
            invoice_no="INV-A",
            invoice_date="2026-02-13",
            created_by=self.user,
        )
        PurchaseLine.objects.create(
            purchase=purchase1,
            item=item,
            qty=Decimal("1"),
            unit_price=Decimal("1.00"),
            discount=Decimal("0"),
            tax_rate=Decimal("0"),
            line_total=Decimal("1.00"),
        )
        post_purchase(purchase1, self.user)
        delete_purchase_with_inventory(purchase1)
        item.refresh_from_db()
        self.assertFalse(item.is_active)

        prefix = PurchaseLineFormSet().prefix
        response = self.client.post(
            reverse("purchase_create"),
            {
                "vendor": str(self.vendor.id),
                "warehouse": str(self.warehouse.id),
                "invoice_date": "2026-02-14",
                "currency": "AZN",
                "notes": "",
                f"{prefix}-TOTAL_FORMS": "1",
                f"{prefix}-INITIAL_FORMS": "0",
                f"{prefix}-MIN_NUM_FORMS": "0",
                f"{prefix}-MAX_NUM_FORMS": "1000",
                f"{prefix}-0-item": "",
                f"{prefix}-0-item_name": "aa",
                f"{prefix}-0-unit": "pcs",
                f"{prefix}-0-qty": "2",
                f"{prefix}-0-unit_price": "3",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertTrue(item.is_active)
