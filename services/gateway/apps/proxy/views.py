import httpx
from django.conf import settings
from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView

# Headers that should not be forwarded upstream
HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}


class ProxyView(View):
    """
    Generic reverse proxy: forwards requests from /api/<service>/<path>
    to the corresponding downstream microservice.
    """

    def _get_upstream_url(self, service: str, path: str) -> str | None:
        base = settings.SERVICE_URLS.get(service)
        if not base:
            return None

        # Special handling for AI service - it uses /api/v1/ instead of /api/ai/
        if service == "ai":
            # e.g. GET /api/ai/v1/kb/faq-categories/ → http://ai:8010/api/v1/kb/faq-categories/
            # The path already includes "v1/" so we don't need to add it again
            return f"{base.rstrip('/')}/api/{path}"

        # Reconstruct the full path — service key == URL prefix on the upstream service.
        # e.g. GET /api/auth/register/ → http://auth:8001/api/auth/register/
        #      GET /api/products/      → http://product:8002/api/products/
        return f"{base.rstrip('/')}/api/{service}/{path}"

    def _filter_headers(self, headers: dict) -> dict:
        return {
            k: v
            for k, v in headers.items()
            if k.lower() not in HOP_BY_HOP_HEADERS
        }

    def dispatch(self, request, service: str, path: str = ""):
        upstream_url = self._get_upstream_url(service, path)
        if not upstream_url:
            return HttpResponse(
                f'{{"success":false,"message":"Service \'{service}\' not found"}}',
                status=404,
                content_type="application/json",
            )

        headers = self._filter_headers(dict(request.headers))
        params = dict(request.GET)

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.request(
                    method=request.method,
                    url=upstream_url,
                    headers=headers,
                    content=request.body,
                    params=params,
                )
        except httpx.ConnectError:
            return HttpResponse(
                f'{{"success":false,"message":"Service \'{service}\' is unavailable"}}',
                status=503,
                content_type="application/json",
            )
        except httpx.TimeoutException:
            return HttpResponse(
                '{"success":false,"message":"Upstream service timed out"}',
                status=504,
                content_type="application/json",
            )

        response = HttpResponse(
            content=resp.content,
            status=resp.status_code,
            content_type=resp.headers.get("content-type", "application/json"),
        )

        # Forward safe response headers
        for header in ("x-request-id", "x-correlation-id"):
            if header in resp.headers:
                response[header] = resp.headers[header]

        return response


class FrontendView(TemplateView):
    """Renders the SPA index.html for all non-API routes."""
    template_name = "index.html"
