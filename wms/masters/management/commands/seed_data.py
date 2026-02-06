from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from wms.masters.models import Vendor, Warehouse, OutgoingLocation, Item


ROLE_PERMS = {
    "Admin": "*",
    "Manager": [
        "add_vendor", "change_vendor", "view_vendor",
        "add_warehouse", "change_warehouse", "view_warehouse",
        "add_outgoinglocation", "change_outgoinglocation", "view_outgoinglocation",
        "add_item", "change_item", "view_item",
        "add_purchaseheader", "change_purchaseheader", "view_purchaseheader",
        "add_issueheader", "change_issueheader", "view_issueheader",
        "add_transferheader", "change_transferheader", "view_transferheader",
        "add_adjustmentheader", "change_adjustmentheader", "view_adjustmentheader",
        "view_stockbalance", "view_stockmovement",
    ],
    "Clerk": [
        "add_purchaseheader", "view_purchaseheader",
        "add_issueheader", "view_issueheader",
        "view_vendor", "view_warehouse", "view_outgoinglocation", "view_item",
        "view_stockbalance", "view_stockmovement",
    ],
    "Viewer": [
        "view_vendor", "view_warehouse", "view_outgoinglocation", "view_item",
        "view_purchaseheader", "view_issueheader",
        "view_transferheader", "view_adjustmentheader",
        "view_stockbalance", "view_stockmovement",
    ],
}


class Command(BaseCommand):
    help = "Seed initial data and roles"

    def handle(self, *args, **options):
        self.stdout.write("Creating groups and permissions...")
        all_perms = Permission.objects.all()
        for role, perms in ROLE_PERMS.items():
            group, _ = Group.objects.get_or_create(name=role)
            if perms == "*":
                group.permissions.set(all_perms)
            else:
                selected = Permission.objects.filter(codename__in=perms)
                group.permissions.set(selected)

        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser("admin", "admin@example.com", "admin123")
            admin.groups.add(Group.objects.get(name="Admin"))
            self.stdout.write("Created admin user: admin / admin123")

        if not Warehouse.objects.exists():
            Warehouse.objects.create(name="Main Warehouse", location="HQ")
            Warehouse.objects.create(name="Secondary Warehouse", location="Branch")

        if not Vendor.objects.exists():
            Vendor.objects.create(name="Default Vendor", contact_person="N/A")

        if not OutgoingLocation.objects.exists():
            OutgoingLocation.objects.create(name="Maintenance", type="department")
            OutgoingLocation.objects.create(name="Project A", type="project")

        if not Item.objects.exists():
            Item.objects.create(internal_code="ITEM-001", name="Sample Item", category="General", unit="pcs", min_stock=5)

        self.stdout.write(self.style.SUCCESS("Seed data completed."))
