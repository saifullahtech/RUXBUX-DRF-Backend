import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_app_email(
    subject: str,
    to_emails: list[str],
    message: str = "",
    html_message: str | None = None,
    from_email: str | None = None,
    reply_to: list[str] | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> bool:
    """
    Send email directly using Django SMTP.

    attachments format:
    [
        ("invoice.pdf", pdf_bytes, "application/pdf"),
        ("image.png", png_bytes, "image/png"),
    ]
    """

    if not subject:
        logger.error("Email subject is required.")
        return False

    if not to_emails:
        logger.error("At least one recipient email is required.")
        return False

    if not from_email:
        from_email = getattr(
            settings,
            "DEFAULT_FROM_EMAIL",
            getattr(settings, "EMAIL_HOST_USER", None),
        )

    text_content = message or (strip_tags(html_message) if html_message else "")

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_emails,
            reply_to=reply_to or None,
        )

        if html_message:
            email.attach_alternative(html_message, "text/html")

        if attachments:
            for filename, file_bytes, mime_type in attachments:
                email.attach(filename, file_bytes, mime_type)

        email.send(fail_silently=False)
        return True

    except Exception as e:
        logger.exception("Email sending failed: %s", e)
        return False


def queue_app_email(
    subject: str,
    to_emails: list[str],
    message: str = "",
    html_message: str | None = None,
    from_email: str | None = None,
    reply_to: list[str] | None = None,
) -> str:
    """
    Queue email through Celery.

    Note:
    Attachments are not included here because your Celery serializer is JSON.
    Bytes/PDF/image attachments should not be sent directly through JSON Celery tasks.
    """

    from .tasks import send_app_email_task

    result = send_app_email_task.delay(
        subject=subject,
        to_emails=to_emails,
        message=message,
        html_message=html_message,
        from_email=from_email,
        reply_to=reply_to,
    )

    return result.id