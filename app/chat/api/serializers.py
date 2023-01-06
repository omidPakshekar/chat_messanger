from rest_framework import serializers

from accounts.api.serializers import UserInlineSerializer
from chat.models import *

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["friends"]

class ContactOneToOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactOneToOne
        fields = ["friend"]

class ChatContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Chat
        fields = ('id', 'contact', )
        read_only = ('id')

class MessageIdSerializer(serializers.Serializer):
    message_id = serializers.IntegerField()
    message_type = serializers.IntegerField()

class MessageContentSerializer(serializers.Serializer):
    message_id = serializers.IntegerField()
    content    = serializers.CharField()

class RoomDeleteSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    room_type = serializers.IntegerField()

class ChatSerializer(serializers.ModelSerializer):
    roomName = serializers.SerializerMethodField(read_only=True)
    users    = serializers.SerializerMethodField(read_only=True)
    roomId   = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'unique_code', 'roomId', 'roomName', 'users']
        read_only = ('id')

    def get_roomName(self, obj):
        user = self.context['request'].user
        if user == obj.participants.owner:
            return obj.participants.friends.first().username
        return obj.participants.owner.username

    def get_roomId(self, obj):
        return obj.id
   	
    def get_users(self, obj):
        lst = list(obj.participants.friends.all())
        lst.append(obj.participants.owner)
        return UserInlineSerializer(instance=lst, many=True).data

class ChatOneToOneSerializer(serializers.ModelSerializer):
    roomName = serializers.SerializerMethodField(read_only=True)
    users    = serializers.SerializerMethodField(read_only=True)
    roomId   = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChatOneToOne
        fields = ['id', 'unique_code', 'roomId', 'roomName', 'users']
        read_only = ('id')

    def get_roomName(self, obj):
        user = self.context['request'].user
        if user == obj.participants.owner:
            return obj.participants.friend.username
        return obj.participants.owner.username

    def get_roomId(self, obj):
        return obj.id
    
    def get_users(self, obj):
        lst = list()
        lst.append(obj.participants.friend)
        lst.append(obj.participants.owner)
        return UserInlineSerializer(instance=lst, many=True).data

class ImageCreateSerializer(serializers.Serializer):
    chat_unique_code = serializers.CharField()
    content = serializers.ImageField()
        
class FileCreateSerializer(serializers.Serializer):
    chat_unique_code = serializers.CharField()
    content = serializers.FileField()
