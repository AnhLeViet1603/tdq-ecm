from django.http import JsonResponse
from django.urls import path, re_path
from django.conf import settings as django_settings
from django.conf.urls.static import static
from apps.proxy.views import ProxyView, FrontendView


def health(request):
    return JsonResponse({"status": "ok", "service": "gateway"})


urlpatterns = [
    path("health/", health, name="health"),
    # Proxy all /api/<service>/... to the matching microservice
    re_path(r"^api/(?P<service>[^/]+)/(?P<path>.*)$", ProxyView.as_view(), name="proxy"),
    # Serve SPA frontend for every other route (including root /)
    path("", FrontendView.as_view(), name="frontend"),
]

# Serve local static files in development
if django_settings.DEBUG:
    urlpatterns += static(django_settings.STATIC_URL, document_root=django_settings.STATIC_ROOT)
