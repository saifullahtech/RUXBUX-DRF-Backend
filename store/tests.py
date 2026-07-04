import shutil
import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Address, CustomerReview, Order, ReviewAttachment
from .tasks import send_order_created_emails_task


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(ALLOWED_HOSTS=["testserver"])
class OrderCreateEmailTaskTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _order_payload(self, email="customer@example.com"):
        payload = {
            "quantity": 6,
            "full_name": "Ali Khan",
            "phone": "+923001234567",
            "address": "House 1, Street 2",
            "city": "Karachi",
        }

        if email is not None:
            payload["email"] = email

        return payload

    @patch("store.views.send_order_created_emails_task.delay")
    def test_order_create_queues_email_task_after_commit(self, delay_mock):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(
                reverse("order-create"),
                self._order_payload(),
                format="json",
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.get()
        self.assertEqual(order.email, "customer@example.com")
        self.assertEqual(len(callbacks), 1)
        delay_mock.assert_called_once_with(order.id)

    @patch(
        "store.views.send_order_created_emails_task.delay",
        side_effect=RuntimeError("Redis unavailable"),
    )
    def test_order_create_succeeds_when_email_task_enqueue_fails(self, delay_mock):
        with patch("store.views.logger.exception") as logger_mock:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    reverse("order-create"),
                    self._order_payload(),
                    format="json",
                )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)
        delay_mock.assert_called_once()
        logger_mock.assert_called_once()


@override_settings(
    FRONTEND_BASE_URL="http://frontend.test",
    RUXBUX_MANAGEMENT_EMAIL="staff@example.com",
)
class OrderEmailTaskTests(TestCase):
    @patch("store.tasks.send_app_email", return_value=True)
    def test_task_sends_management_email_when_customer_email_missing(self, send_mock):
        order = Order.objects.create(
            quantity=6,
            total_amount=1650,
        )
        Address.objects.create(
            order=order,
            full_name="Ali Khan",
            phone="+923001234567",
            address="House 1, Street 2",
            city="Karachi",
        )

        result = send_order_created_emails_task(order.id)

        self.assertTrue(result)
        send_mock.assert_called_once()
        call_kwargs = send_mock.call_args.kwargs
        self.assertEqual(call_kwargs["to_emails"], ["staff@example.com"])
        self.assertIn("Customer email: Not provided", call_kwargs["message"])
        self.assertIn("http://frontend.test/order-success/", call_kwargs["message"])


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, ALLOWED_HOSTS=["testserver"])
class CustomerReviewAPITests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = APIClient()

    def test_create_review_with_attachment(self):
        image = SimpleUploadedFile(
            "review.gif",
            (
                b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00"
                b"\xff\xff\xff,\x00\x00\x00\x00\x01\x00\x01\x00"
                b"\x00\x02\x02D\x01\x00;"
            ),
            content_type="image/gif",
        )

        response = self.client.post(
            reverse("review-create"),
            {
                "stars": 5,
                "name": "Ali",
                "email": "ali@example.com",
                "text": "Great product",
                "images": [image],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CustomerReview.objects.count(), 1)
        self.assertEqual(ReviewAttachment.objects.count(), 1)
        self.assertEqual(response.data["stars"], 5)
        self.assertEqual(len(response.data["attachments"]), 1)

    def test_review_summary_returns_star_counts(self):
        CustomerReview.objects.create(
            stars=5,
            name="Ali",
            email="ali@example.com",
            text="Great",
        )
        CustomerReview.objects.create(
            stars=5,
            name="Sara",
            email="sara@example.com",
            text="Excellent",
        )
        CustomerReview.objects.create(
            stars=4,
            name="Ahmed",
            email="ahmed@example.com",
            text="Good",
        )

        response = self.client.get(reverse("review-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(response.data["stars"]["5"], 2)
        self.assertEqual(response.data["stars"]["4"], 1)
        self.assertEqual(response.data["stars"]["3"], 0)
        self.assertEqual(response.data["stars"]["2"], 0)
        self.assertEqual(response.data["stars"]["1"], 0)

    def test_review_list_is_paginated_with_attachments(self):
        review = CustomerReview.objects.create(
            stars=3,
            name="Ali",
            email="ali@example.com",
            text="Nice",
        )
        ReviewAttachment.objects.create(
            review=review,
            image=SimpleUploadedFile(
                "review.gif",
                (
                    b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00"
                    b"\xff\xff\xff,\x00\x00\x00\x00\x01\x00\x01\x00"
                    b"\x00\x02\x02D\x01\x00;"
                ),
                content_type="image/gif",
            ),
        )

        response = self.client.get(reverse("review-list"), {"page": 1, "page_size": 1})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["text"], "Nice")
        self.assertEqual(len(response.data["results"][0]["attachments"]), 1)
