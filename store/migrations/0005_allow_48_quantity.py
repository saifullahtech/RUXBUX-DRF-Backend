from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0004_six_digit_order_public_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="quantity",
            field=models.PositiveSmallIntegerField(
                validators=[MinValueValidator(1), MaxValueValidator(48)]
            ),
        ),
    ]
