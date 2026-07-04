import logging

from celery import shared_task
from django.conf import settings

from mailer.email import send_app_email

from .models import Address, Order

logger = logging.getLogger(__name__)


def _order_success_url(order: Order) -> str:
    frontend_base_url = getattr(settings, "FRONTEND_BASE_URL", "http://127.0.0.1:3000")
    return f"{frontend_base_url.rstrip('/')}/order-success/{order.public_id}"


def _order_address(order: Order):
    try:
        return order.address
    except Address.DoesNotExist:
        return None


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_created_emails_task(self, order_id: int) -> bool:
    try:
        order = Order.objects.select_related("address").get(id=order_id)
    except Order.DoesNotExist:
        logger.warning("Order email task skipped because order %s does not exist.", order_id)
        return False

    address = _order_address(order)
    customer_name = address.full_name if address else "Not provided"
    phone = address.phone if address else "Not provided"
    city = address.city if address else "Not provided"
    street_address = address.address if address else "Not provided"
    customer_email = (order.email or "").strip()
    customer_email_display = customer_email or "Not provided"
    total = f"Rs. {order.total_amount:,}"
    order_url = _order_success_url(order)

    management_message = "\n".join(
        [
            f"New order received on RUXBUX.",
            "",
            f"Order ID: #{order.id}",
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
            f"Order ID: #{order.id}",
            f"Total: {total}",
            f"Order URL: {order_url}",
        ]
    )

    try:
        failures = []
        management_sent = send_app_email(
            subject=f"New Order #{order.id} - RUXBUX",
            to_emails=[settings.RUXBUX_MANAGEMENT_EMAIL],
            message=management_message,
        )

        if not management_sent:
            failures.append("management")

        if customer_email:
            customer_sent = send_app_email(
                subject=f"Order Confirmed #{order.id} - RUXBUX",
                to_emails=[customer_email],
                message=customer_message,
            )

            if not customer_sent:
                failures.append("customer")
        else:
            logger.info("Order %s has no customer email; customer email skipped.", order.id)

        if failures:
            raise RuntimeError(
                f"Order {order.id} email delivery failed for: {', '.join(failures)}"
            )

        return True
    except Exception as exc:
        logger.exception("Order %s email task failed; retrying if possible.", order.id)
        raise self.retry(exc=exc)
