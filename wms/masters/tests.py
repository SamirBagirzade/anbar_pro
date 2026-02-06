from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from wms.masters.models import Vendor, Warehouse, Item
from wms.purchasing.models import PurchaseHeader, PurchaseLine
from wms.inventory.models import StockMovement, StockBalance
from wms.inventory.services import post_purchase


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
