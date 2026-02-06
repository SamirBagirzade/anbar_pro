from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Vendor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("contact_person", models.CharField(blank=True, max_length=255)),
                ("phone", models.CharField(blank=True, max_length=100)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("tax_id", models.CharField(blank=True, max_length=100)),
                ("address", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Warehouse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="OutgoingLocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("type", models.CharField(choices=[("department", "Department"), ("project", "Project"), ("client", "Client")], max_length=50)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("internal_code", models.CharField(max_length=100, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("category", models.CharField(blank=True, max_length=255)),
                ("unit", models.CharField(max_length=50)),
                ("min_stock", models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("photo", models.ImageField(blank=True, null=True, upload_to="item_photos/")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["internal_code"], name="masters_it_internal_91be3f_idx"),
                    models.Index(fields=["name"], name="masters_it_name_6af15d_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="VendorItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vendor_part_number", models.CharField(blank=True, max_length=100, null=True)),
                ("preferred", models.BooleanField(default=False)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="masters.item")),
                ("vendor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="masters.vendor")),
            ],
        ),
        migrations.AddConstraint(
            model_name="vendoritem",
            constraint=models.UniqueConstraint(fields=("vendor", "item", "vendor_part_number"), name="uq_vendor_item_part"),
        ),
    ]
