from django.urls import re_path, path

from . import consumers

websocket_urlpatterns = [
    path('ws/chat2/<str:chat_id>/<str:username>/', consumers.ChatConsumer2.as_asgi()),
    path('ws/room2/<str:username>/', consumers.RoomConsumer2.as_asgi()),
    path('ws/chat/<str:chat_id>/', consumers.ChatConsumer.as_asgi()),
    path('ws/room/', consumers.RoomConsumer.as_asgi()),
]