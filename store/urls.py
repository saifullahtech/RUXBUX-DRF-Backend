from django.urls import path

from .views import (
    CustomerReviewCreateAPIView,
    CustomerReviewListAPIView,
    CustomerReviewSummaryAPIView,
    OrderCreateAPIView,
    OrderDetailAPIView,
)

urlpatterns = [
    path("orders/create/", OrderCreateAPIView.as_view(), name="order-create"),
    path("orders/<str:public_id>/", OrderDetailAPIView.as_view(), name="order-detail"),
    path("reviews/create/", CustomerReviewCreateAPIView.as_view(), name="review-create"),
    path("reviews/summary/", CustomerReviewSummaryAPIView.as_view(), name="review-summary"),
    path("reviews/", CustomerReviewListAPIView.as_view(), name="review-list"),
]
