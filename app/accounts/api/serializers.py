from django.contrib.auth import authenticate, get_user_model
from dj_rest_auth.serializers import JWTSerializerWithExpiration
from rest_framework import exceptions, serializers
from ..models import CustomUser


class UserInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username"]

class SearchUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)


class CustomJWTSerializer(JWTSerializerWithExpiration):
    user = serializers.SerializerMethodField()
    def get_user(self, obj):
        return UserInlineSerializer(instance=obj['user'], context={'request' : self.context['request']}).data


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def authenticate(self, **kwargs):
        return authenticate(self.context['request'], **kwargs)

    def _validate_username(self, username, password):
        if username and password:
            user = self.authenticate(username=username, password=password)
        else:
            msg = 'Must include "username" and "password".'
            raise exceptions.ValidationError(msg)
        return user
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = self.authenticate(username=username, password=password)
        print(user)
        if not user:
            msg = 'Unable to log in with provided credentials.'
            raise exceptions.ValidationError(msg)
        attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', "username", "birthday_time", "date_joined", "last_login", "name", "gender"]












