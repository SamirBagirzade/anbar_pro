from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("masters", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StockMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("movement_type", models.CharField(choices=[("IN_PURCHASE", "In Purchase"), ("OUT_ISSUE", "Out Issue"), ("TRANSFER_IN", "Transfer In"), ("TRANSFER_OUT", "Transfer Out"), ("ADJUSTMENT", "Adjustment")], max_length=30)),
                ("qty_delta", models.DecimalField(decimal_places=3, max_digits=14)),
                ("unit_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("currency", models.CharField(default="AZN", max_length=10)),
                ("reference_type", models.CharField(blank=True, max_length=50)),
                ("reference_id", models.PositiveIntegerField(blank=True, null=True)),
                ("note", models.TextField(blank=True)),
                ("override_negative", models.BooleanField(default=False)),
                ("override_reason", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.item")),
                ("warehouse", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.warehouse")),
            ],
            options={
                "permissions": [("override_negative_stock", "Can override negative stock")],
                "indexes": [
                    models.Index(fields=["warehouse", "item"], name="inventory__warehouse_3ce6e6_idx"),
                    models.Index(fields=["created_at"], name="inventory__created_9e52f7_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="StockBalance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("on_hand", models.DecimalField(decimal_places=3, default=0, max_digits=14)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.item")),
                ("warehouse", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.warehouse")),
            ],
            options={
                "indexes": [models.Index(fields=["warehouse", "item"], name="inventory__warehouse_763cf1_idx")],
            },
        ),
        migrations.CreateModel(
            name="TransferHeader",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_posted", models.BooleanField(default=False)),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("from_warehouse", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transfers_out", to="masters.warehouse")),
                ("to_warehouse", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transfers_in", to="masters.warehouse")),
            ],
        ),
        migrations.CreateModel(
            name="TransferLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("qty", models.DecimalField(decimal_places=3, max_digits=14)),
                ("header", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="inventory.transferheader")),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.item")),
            ],
        ),
        migrations.CreateModel(
            name="AdjustmentHeader",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("reason", models.CharField(max_length=255)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_posted", models.BooleanField(default=False)),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("warehouse", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.warehouse")),
            ],
        ),
        migrations.CreateModel(
            name="AdjustmentLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("qty_delta", models.DecimalField(decimal_places=3, max_digits=14)),
                ("header", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="inventory.adjustmentheader")),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.item")),
            ],
        ),
        migrations.AddConstraint(
            model_name="stockbalance",
            constraint=models.UniqueConstraint(fields=("warehouse", "item"), name="uq_stock_balance_wh_item"),
        ),
    ]
