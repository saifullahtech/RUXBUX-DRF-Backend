import uuid

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models



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


class CustomerReview(models.Model):
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    name = models.CharField(max_length=80)
    email = models.EmailField()
    text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Customer Review"
        verbose_name_plural = "Customer Reviews"

    def __str__(self):
        return f"{self.stars} stars by {self.name}"


def review_upload_path(instance, filename: str) -> str:
    ext = filename.split(".")[-1].lower()
    return f"reviews/{instance.review_id}/{uuid.uuid4().hex}.{ext}"


class ReviewAttachment(models.Model):
    review = models.ForeignKey(
        CustomerReview,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    image = models.ImageField(upload_to=review_upload_path)
    alt_text = models.CharField(max_length=120, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Review Attachment"
        verbose_name_plural = "Review Attachments"

    def __str__(self):
        return f"Attachment #{self.pk} for Review #{self.review_id}"
