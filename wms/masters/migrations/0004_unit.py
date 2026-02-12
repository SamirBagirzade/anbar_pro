from django.db import migrations, models


def seed_units_from_items(apps, schema_editor):
    Item = apps.get_model("masters", "Item")
    Unit = apps.get_model("masters", "Unit")
    names = set()
    for unit_name in Item.objects.exclude(unit__isnull=True).values_list("unit", flat=True):
        cleaned = (unit_name or "").strip()
        if cleaned:
            names.add(cleaned)
    if not names:
        names.add("pcs")
    for name in names:
        Unit.objects.get_or_create(name=name, defaults={"is_active": True})


class Migration(migrations.Migration):

    dependencies = [
        ("masters", "0003_vendor_attachment"),
    ]

    operations = [
        migrations.CreateModel(
            name="Unit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.RunPython(seed_units_from_items, migrations.RunPython.noop),
    ]
