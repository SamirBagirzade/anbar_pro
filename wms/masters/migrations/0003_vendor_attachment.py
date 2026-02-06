from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import wms.masters.models


class Migration(migrations.Migration):

    dependencies = [
        ("masters", "0002_item_internal_code_nullable"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VendorAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to=wms.masters.models.vendor_attachment_path)),
                ("original_name", models.CharField(max_length=255)),
                ("file_type", models.CharField(blank=True, max_length=100)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("vendor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="masters.vendor")),
            ],
        ),
    ]
