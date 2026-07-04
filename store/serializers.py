from django.db import transaction
from rest_framework import serializers

from .models import Order, Address


def calculate_order_amounts(quantity):
    """
    Single-product RUXBUX pricing logic.
    Adjust these values according to your final pricing table.
    """

    pricing_table = {
        6: {
            "subtotal_amount": 1400,
            "discount_amount": 0,
            "shipping_amount": 250,
        },
        12: {
            "subtotal_amount": 2800,
            "discount_amount": 280,
            "shipping_amount": 250,
        },
        18: {
            "subtotal_amount": 4200,
            "discount_amount": 630,
            "shipping_amount": 0,
        },
        24: {
            "subtotal_amount": 5600,
            "discount_amount": 1120,
            "shipping_amount": 0,
        },
        30: {
            "subtotal_amount": 7000,
            "discount_amount": 1488,
            "shipping_amount": 0,
        },
        36: {
            "subtotal_amount": 8400,
            "discount_amount": 1764,
            "shipping_amount": 0,
        },
    }

    if quantity not in pricing_table:
        raise serializers.ValidationError(
            {
                "quantity": "Invalid quantity selected."
            }
        )

    data = pricing_table[quantity]

    tax_amount = 0
    total_amount = (
        data["subtotal_amount"]
        - data["discount_amount"]
        + data["shipping_amount"]
        + tax_amount
    )

    return {
        "subtotal_amount": data["subtotal_amount"],
        "shipping_amount": data["shipping_amount"],
        "tax_amount": tax_amount,
        "discount_amount": data["discount_amount"],
        "total_amount": total_amount,
    }


class OrderCreateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField()
    email = serializers.EmailField(required=False, allow_blank=True)

    full_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=30)
    address = serializers.CharField()
    city = serializers.CharField(max_length=80)

    def validate_quantity(self, value):
        allowed_quantities = [6, 12, 18, 24, 30, 36]

        if value not in allowed_quantities:
            raise serializers.ValidationError(
                "Quantity must be one of: 6, 12, 18, 24, 30, 36."
            )

        return value

    @transaction.atomic
    def create(self, validated_data):
        quantity = validated_data["quantity"]
        amounts = calculate_order_amounts(quantity)

        order = Order.objects.create(
            email=validated_data.get("email") or None,
            quantity=quantity,
            subtotal_amount=amounts["subtotal_amount"],
            shipping_amount=amounts["shipping_amount"],
            tax_amount=amounts["tax_amount"],
            discount_amount=amounts["discount_amount"],
            total_amount=amounts["total_amount"],
        )

        Address.objects.create(
            order=order,
            full_name=validated_data["full_name"],
            phone=validated_data["phone"],
            address=validated_data["address"],
            city=validated_data["city"],
        )

        return order

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "public_id": str(instance.public_id),
            "quantity": instance.quantity,
            "subtotal_amount": instance.subtotal_amount,
            "shipping_amount": instance.shipping_amount,
            "tax_amount": instance.tax_amount,
            "discount_amount": instance.discount_amount,
            "total_amount": instance.total_amount,
            "status": instance.status,
            "created_at": instance.created_at,
            "address": {
                "full_name": instance.address.full_name,
                "phone": instance.address.phone,
                "address": instance.address.address,
                "city": instance.address.city,
            },
        }


class AddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "full_name",
            "phone",
            "address",
            "city",
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    address = AddressDetailSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "public_id",
            "email",
            "quantity",
            "subtotal_amount",
            "shipping_amount",
            "tax_amount",
            "discount_amount",
            "total_amount",
            "status",
            "customer_note",
            "created_at",
            "updated_at",
            "address",
        ]
