import logging

from django.db import transaction
from django.db.models import Avg, Count, Q
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomerReview, Order
from .serializers import (
    CustomerReviewCreateSerializer,
    CustomerReviewListSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
)
from .tasks import send_order_created_emails_task

logger = logging.getLogger(__name__)


def _enqueue_order_created_emails(order_id):
    try:
        send_order_created_emails_task.delay(order_id)
    except Exception:
        logger.exception("Failed to queue order email task for order %s.", order_id)


class OrderCreateAPIView(CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def perform_create(self, serializer):
        order = serializer.save()
        transaction.on_commit(
            lambda: _enqueue_order_created_emails(order.id)
        )


class OrderDetailAPIView(RetrieveAPIView):
    queryset = Order.objects.select_related("address").all()
    serializer_class = OrderDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "public_id"


class ReviewPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class CustomerReviewCreateAPIView(CreateAPIView):
    queryset = CustomerReview.objects.prefetch_related("attachments").all()
    serializer_class = CustomerReviewCreateSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get("data")

        if data is not None and hasattr(data, "copy"):
            data = data.copy()
            images = (
                self.request.FILES.getlist("images")
                or self.request.FILES.getlist("attachments")
                or self.request.FILES.getlist("image")
            )

            if images and hasattr(data, "setlist"):
                data.setlist("images", images)

            kwargs["data"] = data

        return super().get_serializer(*args, **kwargs)


class CustomerReviewSummaryAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        summary = CustomerReview.objects.aggregate(
            total=Count("id"),
            average_rating=Avg("stars"),
            five_star=Count("id", filter=Q(stars=5)),
            four_star=Count("id", filter=Q(stars=4)),
            three_star=Count("id", filter=Q(stars=3)),
            two_star=Count("id", filter=Q(stars=2)),
            one_star=Count("id", filter=Q(stars=1)),
        )

        return Response(
            {
                "total": summary["total"],
                "average_rating": summary["average_rating"] or 0,
                "stars": {
                    "5": summary["five_star"],
                    "4": summary["four_star"],
                    "3": summary["three_star"],
                    "2": summary["two_star"],
                    "1": summary["one_star"],
                },
            }
        )


class CustomerReviewListAPIView(ListAPIView):
    queryset = CustomerReview.objects.prefetch_related("attachments").all()
    serializer_class = CustomerReviewListSerializer
    permission_classes = [AllowAny]
    pagination_class = ReviewPagination
