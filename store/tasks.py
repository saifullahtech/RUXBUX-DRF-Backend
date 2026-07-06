import logging

from celery import shared_task
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from mailer.email import send_app_email

from .models import Address, Order

logger = logging.getLogger(__name__)


def _field_exists(model, field_name: str) -> bool:
    try:
        model._meta.get_field(field_name)
    except Exception:
        return False

    return True


def _get_order_for_email_task(order_ref: str) -> Order:
    pk_field = Order._meta.pk

    try:
        prepared_pk = pk_field.get_prep_value(order_ref)
    except (TypeError, ValueError, ValidationError) as exc:
        logger.warning(
            "Order email task received invalid %s primary key %r: %s",
            pk_field.get_internal_type(),
            order_ref,
            exc,
        )
    else:
        try:
            return Order.objects.select_related("address").get(pk=prepared_pk)
        except Order.DoesNotExist:
            logger.info("No order found by primary key %r.", order_ref)

    if not _field_exists(Order, "public_id"):
        raise Order.DoesNotExist

    public_id_field = Order._meta.get_field("public_id")
    public_id_value = str(order_ref).strip()

    if isinstance(public_id_field, models.UUIDField):
        try:
            public_id_value = public_id_field.get_prep_value(public_id_value)
        except (TypeError, ValueError, ValidationError) as exc:
            logger.warning(
                "Order email task received invalid UUID public_id %r: %s",
                order_ref,
                exc,
            )
            raise Order.DoesNotExist from exc

    return Order.objects.select_related("address").get(public_id=public_id_value)


def _order_reference(order: Order) -> str:
    public_id = getattr(order, "public_id", None)
    return str(public_id or order.pk)


def _order_success_url(order: Order) -> str:
    frontend_base_url = getattr(settings, "FRONTEND_BASE_URL", "http://127.0.0.1:3000")
    return f"{frontend_base_url.rstrip('/')}/order-success/{_order_reference(order)}"


def _order_address(order: Order):
    try:
        return order.address
    except Address.DoesNotExist:
        return None


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_created_emails_task(self, order_pk) -> bool:
    logger.info("Order email task received order reference %r.", order_pk)

    try:
        order = _get_order_for_email_task(str(order_pk))
    except Order.DoesNotExist:
        logger.warning(
            "Order email task skipped because order reference %r does not exist.",
            order_pk,
        )
        return False

    logger.info(
        "Order email task found order pk=%s public_id=%s.",
        order.pk,
        getattr(order, "public_id", None),
    )

    address = _order_address(order)
    customer_name = address.full_name if address else "Not provided"
    phone = address.phone if address else "Not provided"
    city = address.city if address else "Not provided"
    street_address = address.address if address else "Not provided"
    customer_email = (order.email or "").strip()
    customer_email_display = customer_email or "Not provided"
    total = f"Rs. {order.total_amount:,}"
    order_url = _order_success_url(order)
    order_ref = _order_reference(order)

    if customer_email:
        logger.info("Customer email found for order pk=%s: %s.", order.pk, customer_email)
    else:
        logger.info("Customer email missing for order pk=%s; customer email skipped.", order.pk)

    management_message = "\n".join(
        [
            f"New order received on RUXBUX.",
            "",
            f"Order ID: #{order_ref}",
            f"Customer name: {customer_name}",
            f"Customer email: {customer_email_display}",
            f"Phone: {phone}",
            f"City: {city}",
            f"Address: {street_address}",
            f"Total: {total}",
            f"Order URL: {order_url}",
        ]
    )

    customer_message = "\n".join(
        [
            f"Thank you for your order, {customer_name}.",
            "",
            f"Your RUXBUX order has been confirmed.",
            f"Order ID: #{order_ref}",
            f"Total: {total}",
            f"Order URL: {order_url}",
        ]
    )

    try:
        failures = []
        management_sent = send_app_email(
            subject=f"New Order #{order_ref} - RUXBUX",
            to_emails=[settings.RUXBUX_MANAGEMENT_EMAIL],
            message=management_message,
        )
        logger.info(
            "Management email result for order pk=%s public_id=%s: %s.",
            order.pk,
            getattr(order, "public_id", None),
            management_sent,
        )

        if not management_sent:
            failures.append("management")

        if customer_email:
            customer_sent = send_app_email(
                subject=f"Order Confirmed #{order_ref} - RUXBUX",
                to_emails=[customer_email],
                message=customer_message,
            )
            logger.info(
                "Customer email result for order pk=%s public_id=%s: %s.",
                order.pk,
                getattr(order, "public_id", None),
                customer_sent,
            )

            if not customer_sent:
                failures.append("customer")

        if failures:
            raise RuntimeError(
                f"Order {order.pk} email delivery failed for: {', '.join(failures)}"
            )

        return True
    except Exception as exc:
        logger.exception(
            "Order email task failed for pk=%s public_id=%s; retrying if possible.",
            order.pk,
            getattr(order, "public_id", None),
        )
        raise self.retry(exc=exc)
