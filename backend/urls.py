from django.contrib import admin
from django.urls import path, re_path
from django.urls.conf import include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from backend import settings
# from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path("", include("currency.urls")),
    # path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    re_path(
        r"^swagger/$",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
# if settings.DEBUG:
#     urlpatterns = [
#         *urlpatterns,
#     ] + debug_toolbar_urls()
