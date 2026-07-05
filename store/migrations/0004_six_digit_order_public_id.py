import random

import django.core.validators
from django.db import migrations, models

import store.models


def assign_six_digit_public_ids(apps, schema_editor):
    order_model = apps.get_model("store", "Order")
    used_public_ids = set(
        order_model.objects.exclude(short_public_id__isnull=True).values_list(
            "short_public_id",
            flat=True,
        )
    )
    random_source = random.SystemRandom()

    for order in order_model.objects.order_by("id").iterator():
        if len(used_public_ids) >= 900000:
            raise RuntimeError("No available 6-digit public order IDs.")

        while True:
            public_id = str(random_source.randint(100000, 999999))
            if public_id not in used_public_ids:
                break

        order.short_public_id = public_id
        order.save(update_fields=["short_public_id"])
        used_public_ids.add(public_id)


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0003_customerreview_reviewattachment"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="short_public_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=6,
                null=True,
            ),
        ),
        migrations.RunPython(assign_six_digit_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="short_public_id",
            field=models.CharField(
                db_index=True,
                max_length=6,
                unique=True,
            ),
        ),
        migrations.RemoveField(
            model_name="order",
            name="public_id",
        ),
        migrations.RenameField(
            model_name="order",
            old_name="short_public_id",
            new_name="public_id",
        ),
        migrations.AlterField(
            model_name="order",
            name="public_id",
            field=models.CharField(
                db_index=True,
                default=store.models.generate_public_order_id,
                editable=False,
                max_length=6,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Public order ID must be a 6-digit number.",
                        regex="^\\d{6}$",
                    )
                ],
            ),
        ),
    ]
