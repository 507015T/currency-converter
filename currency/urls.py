from django.urls import re_path, path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter
from currency.views import CurrencyViewSet, CalcCurrencies

router = DefaultRouter()
router.register("currencies", CurrencyViewSet, basename="currency")
urlpatterns = [
    path("api/", include(router.urls)),
    re_path("calc/$", CalcCurrencies.as_view(), name="currency-calc"),
]
