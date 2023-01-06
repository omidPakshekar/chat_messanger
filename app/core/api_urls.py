from django.urls import path, include

from rest_framework.routers import DefaultRouter

from chat.api.views import ChatViewSet

router = DefaultRouter()
router.register('chat', ChatViewSet, basename='chat')

urlpatterns = [
    path('accounts/', include('accounts.api.urls')),
    path('message/', include('chat.api.message_urls')),
    path('room/', include('chat.api.room_urls')),
    path('', include(router.urls)),
]



