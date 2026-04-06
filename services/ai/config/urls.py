from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/ai/', include('apps.ai_service.urls')),
    path('api/v1/kb/', include('apps.knowledge_base.urls')),
    path('api/v1/chatbot/', include('apps.chatbot.urls')),
]
