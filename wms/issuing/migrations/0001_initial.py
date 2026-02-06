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
            name="IssueHeader",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("issue_date", models.DateField()),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_posted", models.BooleanField(default=False)),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("outgoing_location", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.outgoinglocation")),
                ("warehouse", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.warehouse")),
            ],
        ),
        migrations.CreateModel(
            name="IssueLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("qty", models.DecimalField(decimal_places=3, max_digits=14)),
                ("header", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="issuing.issueheader")),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="masters.item")),
            ],
        ),
    ]
