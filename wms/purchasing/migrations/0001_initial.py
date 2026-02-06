from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import wms.purchasing.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("masters", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PurchaseHeader",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("invoice_no", models.CharField(blank=True, max_length=100)),
                ("invoice_date", models.DateField()),
                ("currency", models.CharField(default="AZN", max_length=10)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_posted", models.BooleanField(default=False)),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("vendor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.vendor")),
                ("warehouse", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.warehouse")),
            ],
        ),
        migrations.CreateModel(
            name="PurchaseLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("qty", models.DecimalField(decimal_places=3, max_digits=14)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=14)),
                ("discount", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("tax_rate", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=14)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.item")),
                ("purchase", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="purchasing.purchaseheader")),
            ],
        ),
        migrations.CreateModel(
            name="PurchaseAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to=wms.purchasing.models.purchase_attachment_path)),
                ("original_name", models.CharField(max_length=255)),
                ("file_type", models.CharField(blank=True, max_length=100)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("purchase", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="purchasing.purchaseheader")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
