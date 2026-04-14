from django.urls import path, include

urlpatterns = [
    path('api/ai/v1/', include('apps.api.urls')),
]
