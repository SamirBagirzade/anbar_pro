from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("masters", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="item",
            name="internal_code",
            field=models.CharField(max_length=100, unique=True, blank=True, null=True),
        ),
    ]
