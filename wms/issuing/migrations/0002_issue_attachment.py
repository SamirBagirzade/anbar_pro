from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("issuing", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IssueAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="issue_attachments/%Y/%m/%d/")),
                ("original_name", models.CharField(max_length=255)),
                ("file_type", models.CharField(blank=True, max_length=100)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("header", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="issuing.issueheader")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
