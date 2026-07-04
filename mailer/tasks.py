from celery import shared_task

from .email import send_app_email


@shared_task
def send_app_email_task(
    subject: str,
    to_emails: list[str],
    message: str = "",
    html_message: str | None = None,
    from_email: str | None = None,
    reply_to: list[str] | None = None,
) -> bool:
    return send_app_email(
        subject=subject,
        to_emails=to_emails,
        message=message,
        html_message=html_message,
        from_email=from_email,
        reply_to=reply_to,
    )


@shared_task
def send_test_email(to_email: str) -> bool:
    return send_app_email(
        subject="Order Confirmed - RUXBUX",
        to_emails=[to_email],
        message="Thanks for your order! We'll ship soon.",
        html_message="<h2>Thanks for your order!</h2><p>We'll ship soon.</p>",
    )