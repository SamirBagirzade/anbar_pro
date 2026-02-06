from decimal import Decimal
import threading
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import connections
from wms.masters.models import Warehouse, Item, Vendor, OutgoingLocation
from wms.purchasing.models import PurchaseHeader, PurchaseLine
from wms.issuing.models import IssueHeader, IssueLine
from wms.inventory.models import StockBalance
from wms.inventory.services import post_purchase, post_issue, apply_movement


class InventoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u1", password="pass")
        self.warehouse = Warehouse.objects.create(name="WH", location="L")
        self.vendor = Vendor.objects.create(name="Vendor")
        self.outgoing = OutgoingLocation.objects.create(name="Dept", type="department")
        self.item = Item.objects.create(internal_code="I1", name="Item", unit="pcs")

    def _create_purchase(self, qty):
        purchase = PurchaseHeader.objects.create(
            vendor=self.vendor,
            warehouse=self.warehouse,
            invoice_no="INV1",
            invoice_date="2026-02-06",
            created_by=self.user,
        )
        PurchaseLine.objects.create(
            purchase=purchase,
            item=self.item,
            qty=Decimal(qty),
            unit_price=Decimal("10.00"),
            discount=Decimal("0"),
            tax_rate=Decimal("0"),
            line_total=Decimal("10.00"),
        )
        return purchase

    def test_purchase_increases_stock(self):
        purchase = self._create_purchase("5")
        post_purchase(purchase, self.user)
        balance = StockBalance.objects.get(warehouse=self.warehouse, item=self.item)
        self.assertEqual(balance.on_hand, Decimal("5.000"))

    def test_cannot_issue_beyond_on_hand(self):
        purchase = self._create_purchase("5")
        post_purchase(purchase, self.user)

        issue = IssueHeader.objects.create(
            warehouse=self.warehouse,
            outgoing_location=self.outgoing,
            issue_date="2026-02-06",
            created_by=self.user,
        )
        IssueLine.objects.create(header=issue, item=self.item, qty=Decimal("10"))

        with self.assertRaises(PermissionDenied):
            post_issue(issue, self.user)


class ConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user("u2", password="pass")
        self.warehouse = Warehouse.objects.create(name="WH", location="L")
        self.item = Item.objects.create(internal_code="I2", name="Item2", unit="pcs")

    def _apply(self, qty):
        connections.close_all()
        apply_movement(
            user=self.user,
            warehouse=self.warehouse,
            item=self.item,
            qty_delta=Decimal(qty),
            movement_type="ADJUSTMENT",
        )

    def test_concurrent_update_safety(self):
        threads = [
            threading.Thread(target=self._apply, args=("10",)),
            threading.Thread(target=self._apply, args=("10",)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        balance = StockBalance.objects.get(warehouse=self.warehouse, item=self.item)
        self.assertEqual(balance.on_hand, Decimal("20.000"))
