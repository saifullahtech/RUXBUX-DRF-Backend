from django.urls import path

from .views import OrderCreateAPIView, OrderDetailAPIView

urlpatterns = [
    path("orders/create/", OrderCreateAPIView.as_view(), name="order-create"),
    path("orders/<uuid:public_id>/", OrderDetailAPIView.as_view(), name="order-detail"),
]
