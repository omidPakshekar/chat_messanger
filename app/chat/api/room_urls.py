from django.urls import path, include

from .views import *




urlpatterns = [
	path('delete/', DeleteRoomView.as_view()),

]