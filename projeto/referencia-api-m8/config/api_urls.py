from django.urls import include, path
from apps.accounts.throttles import ThrottledTokenView
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView
from rest_framework.routers import DefaultRouter

from apps.accounts.api import MeView
from apps.cart.api import CartItemViewSet, CartView
from apps.catalog.api import CategoryViewSet, ProductViewSet
from apps.orders.api import OrderViewSet
from apps.payments.api import PagarPedidoView

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("categories", CategoryViewSet, basename="category")
router.register("cart/items", CartItemViewSet, basename="cart-item")
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("auth/token/", ThrottledTokenView.as_view(), name="token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/logout/", TokenBlacklistView.as_view(), name="logout"),
    path("cart/", CartView.as_view(), name="cart"),
    path("orders/<int:pk>/pay/", PagarPedidoView.as_view(), name="order-pay"),
    path("", include(router.urls)),
]
