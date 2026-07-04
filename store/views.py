from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from .models import Order
from .serializers import OrderCreateSerializer, OrderDetailSerializer


class OrderCreateAPIView(CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = [AllowAny]


class OrderDetailAPIView(RetrieveAPIView):
    queryset = Order.objects.select_related("address").all()
    serializer_class = OrderDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "public_id"
