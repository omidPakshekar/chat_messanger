import json, jwt, os

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import  Response
from rest_framework import generics, status, views, permissions, viewsets
from rest_framework.decorators import api_view, action

from dj_rest_auth.views import LoginView as dj_Login

from accounts.models import CustomUser

from .serializers import *


class CustomUserLogin(dj_Login):
    def get_response_serializer(self):
        return CustomJWTSerializer

class SearchUsername(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()
    serializer_class = SearchUsernameSerializer
    def post(self, request, *args, **kwargs):
        return Response(UserInlineSerializer(instance=self.queryset.filter(username__contains=request.data['username']), many=True).data)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()
    
    @action(methods=["get"], detail=False, name="user Profile", url_path='profile')
    def profile(self, request):
        return Response(UserSerializer(instance=request.user, context={"request": request}).data)
