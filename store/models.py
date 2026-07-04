from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

from django.db import models
from django.core.validators import RegexValidator



class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELED = "canceled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELED, "Canceled"),
    ]

    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    session_key = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        db_index=True,
    )

    email = models.EmailField(blank=True, null=True)

    quantity = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(36),
        ]
    )

    subtotal_amount = models.PositiveIntegerField(default=0)
    shipping_amount = models.PositiveIntegerField(default=0)
    tax_amount = models.PositiveIntegerField(default=0)
    discount_amount = models.PositiveIntegerField(default=0)
    total_amount = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_CONFIRMED,
        db_index=True,
    )

    customer_note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.id} - Qty {self.quantity} - {self.status}"
    




phone_validator = RegexValidator(
    regex=r"^\+?[\d\s\-()]{7,20}$",
    message="Enter a valid phone number.",
)


class Address(models.Model):
    session_key = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        db_index=True,
    )

    order = models.OneToOneField(
        "Order",
        on_delete=models.CASCADE,
        related_name="address",
    )

    full_name = models.CharField(max_length=120)

    phone = models.CharField(
        max_length=30,
        validators=[phone_validator],
    )

    address = models.TextField()

    city = models.CharField(max_length=80)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.full_name} - {self.city}"
