from functools import partial
from django.contrib.auth import get_user_model
from django.db.models import Q, Count

from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status, views, permissions, viewsets

from chat.models import Chat, Contact
from .serializers import *
from chat.models import UniqueGenerator
from asgiref.sync import async_to_sync
from pymongo import MongoClient

from channels.layers import get_channel_layer


User = get_user_model()

client = MongoClient(host="my-mongodb",
                  port=27017,
                  username='admin',
                  password='admin'
                 )
dbname = client['test']
ccolections = dbname['chats']

class ChatViewSet(viewsets.ModelViewSet):
    queryset = ChatOneToOne.objects.all()
    serializer_class = ChatOneToOneSerializer
    permission_classes = (permissions.IsAuthenticated, )
    contact = None 

    def get_serializer_class(self):
        if self.action == 'create':
            return ContactOneToOneSerializer
        return ChatOneToOneSerializer
    
    # def get_queryset(self):
    #     print(self.queryset.filter(self.request.user in partic))
    #     return self.queryset.filter(Q(participants__owner=self.request.user))

    def create(self, request, *args, **kwargs):
        serializer = ContactOneToOneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        friend = serializer.validated_data['friend']

        channel_layer = get_channel_layer()
        chat = ccolections.find_one({'sender': request.data['friend'], 'reciever': request.user.username, 'kind' : 0 }) 
        if chat == None:
            chat_unique_key = UniqueGenerator()

            chat = ccolections.insert_one({
                    'sender'    : request.user.username,
                    'reciever'  : request.data['friend'],
                    'kind'      : 0,
                    'contacts'  : [],
                    'sender_profile_image': "https://picsum.photos/200",
                    'reciever_profile_image': "https://picsum.photos/200",
                    'hide_user' : [],
                    'unique_code' : chat_unique_key

                })
            async_to_sync(channel_layer.group_send)(
                    f'notification_{request.user.id}',
                    {
                        'type': 'fetch_one_room',
                        'chat_id': str(chat.inserted_id)
                    }
                )
            async_to_sync(channel_layer.group_send)(
                f'notification_{friend}',
                {
                    'type': 'fetch_one_room',
                    'chat_id': str(chat.inserted_id)
                }
            )
            return Response(data = {'chat_id': chat_unique_key}, status=status.HTTP_201_CREATED)
        # remove user from hide_user
        ccolections.update_one({'_id': chat['_id']},  {'$pull' : {'hide_user':self.user.username}})

        async_to_sync(channel_layer.group_send)(
            f'notification_{request.user.id}',
                {
                    'type': 'fetch_one_room',
                    'chat_id': chat['_id']
                }
            )
        return Response(data = {'chat_id': chat['unique_code']}, status=status.HTTP_200_OK)


# update and partial update and add delete for owner and admin
# class ChatViewSet(viewsets.ModelViewSet):
#     queryset = Chat.objects.all()
#     serializer_class = ChatSerializer
#     permission_classes = (permissions.IsAuthenticated, )
#     contact = None 

#     def get_serializer_class(self):
#         if self.action == 'create':
#             return ContactSerializer
#         return ChatSerializer
    
#     # def get_queryset(self):
#     #     print(self.queryset.filter(self.request.user in partic))
#     #     return self.queryset.filter(Q(participants__owner=self.request.user))

#     def create(self, request, *args, **kwargs):
#         serializer = ContactSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         cs = serializer.validated_data['friends']
#         contact_ = Contact.objects.annotate(
#             nusers=Count('friends'),
#             nusers_match=Count('friends', filter=Q(friends__in=cs))
#         ).filter(
#             nusers=len(cs),
#             nusers_match=len(cs)
#         )
#         if contact_.count() == 0:
#             contact = serializer.save(owner=self.request.user)
#             chat_ = Chat.objects.create(participants=contact)
#             print('***unique_code=', chat_.id, chat_.unique_code)
#             channel_layer = get_channel_layer()
#             user = request.user.id
#             async_to_sync(channel_layer.group_send)(
#                     f'notification_{request.user.id}',
#                     {
#                         'type': 'fetch_one_room',
#                         'chat_id': chat_.id
#                     }
#                 )
#             for i in chat_.participants.friends.all():
#                 async_to_sync(channel_layer.group_send)(
#                     f'notification_{i.id}',
#                     {
#                         'type': 'fetch_one_room',
#                         'chat_id': chat_.id
#                     }
#                 )
#             return Response(data = {'chat_id': chat_.unique_code}, status=status.HTTP_201_CREATED)
        

#         return Response(data = {'chat_id': contact_[0].chats.all()[0].unique_code}, status=status.HTTP_200_OK)
        

class ImageCreateView(generics.GenericAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, *args, **kwargs):
        chat_ = Chat.objects.get(unique_code=self.request.data['chat_unique_code'])
        image_ = Image.objects.create(owner=self.request.user, content=self.request.data['content'])
        reciever_ = UserMessage.objects.create()
        reciever_.users.add(*chat_.participants.friends.all())
        reciever_.save()
        Message.objects.create(item=image_, sender=self.request.user, reciever=reciever_)
        return Response({'detail' : "it's created"}, status=status.HTTP_201_CREATED)

class FileCreateView(generics.CreateAPIView):
    serializer_class = FileCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, *args, **kwargs):
        chat_ = Chat.objects.get(unique_code=self.request.data['chat_unique_code'])
        image_ = File.objects.create(owner=self.request.user, content=self.request.data['content'])
        reciever_ = UserMessage.objects.create()
        reciever_.users.add(*chat_.participants.friends.all())
        reciever_.save()
        Message.objects.create(item=image_, sender=self.request.user, reciever=reciever_)
        return Response({'detail' : "it's created"}, status=status.HTTP_201_CREATED)




class DeleteRoomView(generics.GenericAPIView):
    queryset = Message.objects.all()
    serializer_class = RoomDeleteSerializer


    def post(self, *args, **kwargs):
        obj = ChatOneToOne.objects.get(id=int(self.request.data['room_id']))
        channel_layer = get_channel_layer()
        delete_type = self.request.data['room_type']
        if delete_type == '1':

            async_to_sync(channel_layer.group_send)(
                f'notification_{self.request.user.id}',
                {
                'type': 'delete_one_way',
                 "command": "room_delete_one_way",
                 "room_id": str(obj.id),

                }
            )
            for i in obj.messages.all():
                i.recievers.remove(self.request.user)
                i.save()

            obj.hide_user.add(self.request.user)
            obj.save()
            return Response({'detail': 'room one way delete succsessfully'}, status=status.HTTP_200_OK)
        else:

            async_to_sync(channel_layer.group_send)(
            f'notification_{obj.participants.owner.id}',
                {
                'type': 'delete_two_way',
                 "command": "room_delete_two_way",
                 "room_id": str(obj.id),

                }
            )
            async_to_sync(channel_layer.group_send)(
            f'notification_{obj.participants.friend.id}',
                {
                'type': 'delete_two_way',
                 "command": "room_delete_two_way",
                 "room_id": str(obj.id),

                }
            )
            
            obj.participants.delete()
            obj.delete()
            return Response({'detail': 'room two way delete succsessfully'}, status=status.HTTP_200_OK)






class DeleteRoomViewOneWay(generics.GenericAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageIdSerializer

    def post(self, *args, **kwargs):
        obj = Message.objects.get(id=int(self.request.data['message_id']))
        channel_layer = get_channel_layer()
        chat_ = obj.chat_set.last()
        obj.recievers.remove(self.request.user)
        async_to_sync(channel_layer.group_send)(
            f'chat_{chat_.unique_code}',
            {
            'type': 'delete_one_way',
             "command": "delete_one_way",
             "message_id": str(obj.id),

            }
        )
        return Response({'detail': 'message delete succsessfully'}, status=status.HTTP_200_OK)



class DeleteMessageViewTwoWay(generics.GenericAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageIdSerializer

    def post(self, *args, **kwargs):
        obj = Message.objects.get(id=int(self.request.data['message_id']))
        channel_layer = get_channel_layer()
        if self.request.user == obj.sender:
            chat_ = obj.chat_set.last()
            async_to_sync(channel_layer.group_send)(
                f'chat_{chat_.unique_code}',
                {
                'type': 'delete_two_way',
                 "command": "delete_two_way",
                 "message_id": str(obj.id),

                }
            )
            obj.delete()
            return Response({'detail': 'message delete succsessfully'}, status=status.HTTP_200_OK)

        return Response({'detail': 'you are not owner'}, status=status.HTTP_400_BAD_REQUEST)



class DeleteMessageViewOneWay(generics.GenericAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageIdSerializer

    def post(self, *args, **kwargs):
        pass
        


# class DeleteMessageViewTwoWay(generics.GenericAPIView):
#     queryset = Message.objects.all()
#     serializer_class = MessageIdSerializer

#     def post(self, *args, **kwargs):
#         obj = Message.objects.get(id=int(self.request.data['message_id']))
#         channel_layer = get_channel_layer()
#         if self.request.user == obj.sender:
#             chat_ = obj.chat_set.last()
#             obj.delete()
#             async_to_sync(channel_layer.group_send)(
#                 f'chat_{chat_.id}',
#                 {
#                 'type': 'fetch_messages_view',
#                  "command": "messages",
#                 }
#             )
#             return Response({'detail': 'message delete succsessfully'}, status=status.HTTP_200_OK)

#         return Response({'detail': 'you are not owner'}, status=status.HTTP_400_BAD_REQUEST)





class ChangeMessageContentView(generics.GenericAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageContentSerializer


    def post(self, *args, **kwargs):
        obj = Message.objects.get(id=int(self.request.data['message_id']))
        channel_layer = get_channel_layer()
        content = self.request.data['content']
        obj.edited = True
        chat_ = obj.chatonemessages.last()
        item_ = obj.item
        item_.content = content
        item_.save()
        obj.save()
        async_to_sync(channel_layer.group_send)(
                f'chat_{chat_.unique_code}',
                {
                'type': 'change_content',
                 "command": "change_content",
                 "message_id": str(obj.id),
                 "content": content
                }
            )
        return Response({'detail': 'message changed'}, status=status.HTTP_200_OK)


class DeleteMessageView(generics.GenericAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageIdSerializer


    def post(self, *args, **kwargs):
        obj = Message.objects.get(id=int(self.request.data['message_id']))
        channel_layer = get_channel_layer()
        delete_type = self.request.data['message_type']
        print('dddd', delete_type)
        chat_ = obj.chatonemessages.last()
        if delete_type == '1':
            obj.recievers.remove(self.request.user)
            async_to_sync(channel_layer.group_send)(
                f'chat_{chat_.unique_code}',
                {
                'type': 'delete_one_way',
                 "command": "delete_one_way",
                 "message_id": str(obj.id),
                 "user": str(self.request.user.id)

                }
            )
            obj
            obj.save()
            return Response({'detail': 'message delete one way succsessfully'}, status=status.HTTP_200_OK)
        else:
            # if self.request.user == obj.sender:
            async_to_sync(channel_layer.group_send)(
                f'chat_{chat_.unique_code}',
                {
                'type': 'delete_two_way',
                 "command": "delete_two_way",
                 "message_id": str(obj.id),

                }
            )
            obj.delete()
            return Response({'detail': 'message delete two way succsessfully'}, status=status.HTTP_200_OK)

            # return Response({'detail': 'you are not owner'}, status=status.HTTP_400_BAD_REQUEST)





   
# class AddUserContact(views.APIView):
#     queryset = Contact.objects.all()
#     serializer_class = ContactSerializer
#     # authentication_classes = 
#     def post(self, request, format=None):





