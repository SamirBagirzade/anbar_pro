from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("purchasing", "0001_initial"),
        ("issuing", "0002_issue_attachment"),
    ]

    operations = [
        migrations.AddField(
            model_name="issueheader",
            name="source_purchase",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="purchasing.purchaseheader",
            ),
        ),
    ]
