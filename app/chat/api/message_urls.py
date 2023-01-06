from django.urls import path, include

from .views import *




urlpatterns = [
	path('delete/', DeleteMessageView.as_view()),
	# path('delete-two-way/', DeleteMessageViewTwoWay.as_view()),
	path('change-content/', ChangeMessageContentView.as_view()),
	# path('delete-one-way/', DeleteMessageViewOneWay.as_view()),

]