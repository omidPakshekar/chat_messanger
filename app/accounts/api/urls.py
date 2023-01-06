from django.urls import path, include

from dj_rest_auth.views import LoginView, LogoutView
from dj_rest_auth.registration.views import RegisterView, VerifyEmailView
from .views import *

from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register('', UserViewSet, basename='')

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', CustomUserLogin.as_view()),
    path('logout/', LogoutView.as_view()),
    path('search-username/', SearchUsername.as_view()),
    path('', include(router.urls)),


]    