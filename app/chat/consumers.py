# # chat/consumers.py
from django.contrib.auth import get_user_model
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async
from channels.consumer import SyncConsumer, AsyncConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import sync_to_async
from django.db.models import Q
import json

from .api.serializers import ImageCreateSerializer
from .models import *
import base64
from accounts.models import CustomUser

from pymongo import MongoClient
from bson.json_util import dumps as bson_dump, loads as bson_loads
import  mongoengine as mongo 

mongo.connect(db='test', host="my-mongodb", port=27017, username='admin', password='admin')

# class Message(mongo.Document):
#     senderId =  mongo.StringField(required=True)
#     username =   mongo.StringField(required=True)
#     content =  mongo.StringField(required=True)
#     type = mongo.StringField(required=True)
#     avatar =  mongo.ImageField()
#     timestamp = mongo.StringField(required=True)
#     date =  mongo.StringField(required=True)
#     edited = mongo.BooleanField()
#     replyMessage = mongo.ObjectIdField()

User = get_user_model()
client = MongoClient(host="my-mongodb",
                  port=27017,
                  username='admin',
                  password='admin'
                 )
dbname = client['test']
message_collection = dbname['messages']
# chat_collection = dbname['chats']
ccolections = dbname['chats']






class ChatConsumer2(AsyncConsumer):

    async def fetch_messages(self, data):
        messages = await self.get_all_message()
        content = {
            'command': 'messages',
            'messages': await self.messages_to_json(messages)
        }
        await self.send_message(content)

    async def fetch_messages_view(self, data):
        messages = await self.get_all_message()
        content = {
            'command': 'messages',
            'messages': await self.messages_to_json(messages)
        }
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(content)
            })
    
    async def delete_two_way(self, data):
        content = {
            'command': 'delete_two_way',
            'message_id': data['message_id']
        }
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(content)
        })

    async def delete_one_way(self, data):
        content = {
            'command': 'delete_one_way',
            'message_id': data['message_id'],
            'user' : data['user']

        }
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(content)
        })
    async def change_content(self, data):
        content = {
            'command': 'change_content',
            'message_id': data['message_id'],
            'content': data['content']
        }
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(content)
        })



    
    async def new_message(self, data):
        message_ = await self.create_message(data)
        content = {
            'command': 'new_message',
            'message':  await self.message_to_json(message_)
        }
        print('new_message\n', content)
        return await self.send_chat_message(content)
    
    @sync_to_async
    def message_to_json(self, message):
        m = message.timestamp.minute
        h = message.timestamp.hour
        return {
            '_id': message.id,
            'senderId': str(message.sender.id),
            'username': message.sender.username,
            'content': message.item.content,
            'type' : 'text',
            'avatar' : "https://picsum.photos/200",
            'timestamp': f'{f"0{h}" if h < 10 else f"{h}"}:{f"0{m}" if m < 10 else f"{m}"}',
            "date": str(message.date),
            "edited": message.edited,
            'replyMessage':  self.parent_message_to_json(message.parent_message)
        }

    def parent_message_to_json(self, message):
        if message == None:
            return None
        print('6', message, 'f', message.timestamp, 'ff', message.date)
        print('ff', message.timestamp)

        m = message.timestamp.minute
        h = message.timestamp.hour
        return {
            '_id': message.id,
            'senderId': str(message.sender.id),
            'username': message.sender.username,
            'content': message.item.content,
            'type' : 'text',
            'avatar' : "https://picsum.photos/200",
            'timestamp': f'{f"0{h}" if h < 10 else f"{h}"}:{f"0{m}" if m < 10 else f"{m}"}',
            "edited": message.edited,
            "date": str(message.date)
        }

    @sync_to_async
    def messages_to_json(self, messages):
        return message_collection.find({'chat_unique_key' : self.chat_id})

    

    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_message
    }
    
    
    @sync_to_async
    def get_user1(self, username):
        return CustomUser.objects.get(username=username)

    async def websocket_connect(self, event):
        self.user = await self.get_user1(username=self.scope['url_route']['kwargs']['username'])
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat = await self.get_chat()
        self.chat_room_id = f"chat_{self.chat_id}"
        if self.chat:
            if await self.check_auth():
                await self.channel_layer.group_add(
                    self.chat_room_id,
                    self.channel_name
                )
                await self.send({'type': 'websocket.accept'})
            else:
                await self.send({'type': 'websocket.close'})
        else:
            await self.send({'type': 'websocket.close'})

    async def websocket_disconnect(self, close_code):
        await (self.channel_layer.group_discard)(
            self.chat_room_id,
            self.channel_name
        )
        raise StopConsumer()


    async def websocket_receive(self, event):
        text_data = event.get('text', None)
        data = json.loads(text_data)
        if  data['command'] == 'new_message' :
            if not data['message'] == '':
                await self.new_message(data)
        # elif data['command'] == 'delete_message':
        #     if data['type'] == 'one_way':
        #         await self.delete_one_way(data)
        #     else :
        #         pass
        else:
            await self.fetch_messages(data)

    async def send_chat_message(self, message):
        await self.channel_layer.group_send(
            self.chat_room_id,
            {
                'type': 'chat_message',
                'message': message,
                'sender_channel_name': self.channel_name
            }
        )

    async def send_message(self, message):
        await self.send({
            'type' : 'websocket.send',
            'text' : bson_dump(message)
            })

    # async def chat_message(self, event):
    #     message = event['message']
    #     if self.channel_name != event['sender_channel_name']:
    #         await self.send({
    #         'type' : 'websocket.send',
    #         'text' :json.dumps(message)
    #         })
    async def chat_message(self, event):
        message = event['message']
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(message)
            })
    @database_sync_to_async
    def get_chat(self):
        try:
            chat = ChatOneToOne.objects.get(unique_code=self.chat_id)
            self.participants = chat.participants
            return chat
        except Chat.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, data):
        message_ = None 
        print(data)
        self.sender = self.user
        if data['message_type'] == 'text':
            parent = None 
            if 'parent_message' in data:
                if data['parent_message'] != None:
                    parent_id = int(data['parent_message'])
                    parent = Message.objects.get(id=parent_id)
            text_ = Text.objects.create(owner=self.user,  content=data['message'])
            message_ = Message.objects.create(sender=self.sender,  item=text_, parent_message=parent)
            message_.recievers.add(self.participants.friend)
            message_.recievers.add(self.participants.owner)
            message_.recievers.add(self.user)
            message_.save()
            h = timezone.now().hour
            m = timezone.now().minute

            message_collection.insert_one({
                'senderId': self.sender.id,
                'username': self.sender.username,
                'chat_unique_key' : self.chat_id,
                'hide_user': [],
                'recievers': [self.user.username, self.participants.friend.username, self.participants.owner.username],
                'content': data['message'],
                'timestamp': f'{f"0{h}" if h < 10 else f"{h}"}:{f"0{m}" if m < 10 else f"{m}"}',
                "date": timezone.now(),
                'type' : 'text',
                'avatar' : "https://picsum.photos/200",
                "edited": False,
                'replyMessage': None
                }
            )
        # new 
        self.chat.messages.add(message_)
        for i in self.chat.hide_user.all():
            async_to_sync(self.channel_layer.group_send)(
                f'notification_{i.id}',
                    {
                        'type': 'fetch_one_room',
                        'chat_id': self.chat.id
                    }
            )
        self.chat.hide_user.clear()
        
        return message_
    
    @sync_to_async
    def check_auth(self):
        return self.user == self.participants.friend or self.user == self.participants.owner
        
    @sync_to_async
    def get_all_message(self):
        lst = []
        for i in  self.chat.messages.all():
            if self.user in i.recievers.all():
                lst.append(i)
        return lst


class ChatConsumer(AsyncConsumer):

    async def fetch_messages(self, data):
        messages = await self.get_all_message()
        content = {
            'command': 'messages',
            'messages': await self.messages_to_json(messages)
        }
        print('****\n', content, "\n*****")
        await self.send_message(content)

    
    async def new_message(self, data):
        message_ = await self.create_message(data)
        content = {
            'command': 'new_message',
            'message':  await self.message_to_json(message_)
        }
        print('new_message\n', content)
        return await self.send_chat_message(content)
    
    @sync_to_async
    def message_to_json(self, message):
        return {
            '_id': message.id,
            'senderId': str(message.sender.id),
            'username': message.sender.username,
            'content': message.item.content,
            'type' : 'text',
            'timestamp': str(message.timestamp),
        }

    def parent_message_to_json(self, message):
        if message == None:
            return None
        return {
            '_id': message.id,
            'senderId': str(message.sender.id),
            'username': message.sender.username,
            'content': message.item.content,
            'type' : 'text',
            'timestamp': str(message.timestamp)
        }

    @sync_to_async
    def messages_to_json(self, messages):
        result = []
        for message in messages:
            if message.item._meta.model_name == 'image':
                result.append({'_id': message.id,
                    'senderId': str(message.sender.id),
                    'username': message.sender.username,
                    'type': 'image',
                    'content': ImageCreateSerializer(instance=message.item).data['content'],
                    'timestamp': str(message.timestamp),
                    'replyMessage':  self.parent_message_to_json(message.parent_message)
                    })
            else:
                result.append({'_id': message.id,
                    'senderId': str(message.sender.id),
                    'username': message.sender.username,
                    'content': message.item.content,
                    'timestamp': str(message.timestamp),
                    'type' : 'text',
                    'replyMessage':  self.parent_message_to_json(message.parent_message)
                })

        return result

    

    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_message
    }

    async def websocket_connect(self, event):
        self.user = self.scope['user']
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat = await self.get_chat()
        self.chat_room_id = f"chat_{self.chat_id}"
        if self.chat:
            if await self.check_auth():
                await self.channel_layer.group_add(
                    self.chat_room_id,
                    self.channel_name
                )
                await self.send({'type': 'websocket.accept'})
            else:
                await self.send({'type': 'websocket.close'})
        else:
            await self.send({'type': 'websocket.close'})

    async def websocket_disconnect(self, close_code):
        await (self.channel_layer.group_discard)(
            self.chat_room_id,
            self.channel_name
        )
        raise StopConsumer()


    async def websocket_receive(self, event):
        text_data = event.get('text', None)
        data = json.loads(text_data)
        if  data['command'] == 'new_message' :
            if not data['message'] == '':
                await self.new_message(data)
        # elif data['command'] == 'delete_message':
        #     if data['type'] == 'one_way':
        #         await self.delete_one_way(data)
        #     else :
        #         pass
        else:
            await self.fetch_messages(data)

    async def send_chat_message(self, message):
        await self.channel_layer.group_send(
            self.chat_room_id,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def send_message(self, message):
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(message)
            })

    async def chat_message(self, event):
        message = event['message']
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(message)
            })
    @database_sync_to_async
    def get_chat(self):
        try:
            chat = Chat.objects.get(unique_code=self.chat_id)
            self.participants = chat.participants
            return chat
        except Chat.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, data):
        message_ = None 
        print(data)
        self.sender = CustomUser.objects.get(username=data['username'])
        reciever_ = UserMessage.objects.create()
        reciever_.users.add(*self.participants.friends.all()); reciever_.save()
        if data['message_type'] == 'text':
            parent = None 
            if 'parent_message' in data:
                parent_id = int(data['parent_message'])
                parent = Message.objects.get(id=parent_id)
            text_ = Text.objects.create(owner=self.user,  content=data['message'])
            message_ = Message.objects.create(sender=self.sender, reciever=reciever_, item=text_, parent_message=parent)

        self.chat.messages.add(message_)

        return message_
    
    @sync_to_async
    def check_auth(self):
        return self.user in self.participants.friends.all() or self.user == self.participants.owner
        
    @sync_to_async
    def get_all_message(self):
        return self.chat.messages.all()
    




class RoomConsumer2(AsyncConsumer):

    async def fetch_room(self, data):
        rooms = await self.get_all_room()
        content = {
            'command': 'rooms',
            'rooms': await self.rooms_to_json(rooms)
        }
        await self.send_message(content)

    async def fetch_one_room(self, data):
        room = await self.get_one_chat(data['chat_id'])
        content = {
            'command': 'new_room',
            'room': await self.room_to_json(room)
        }
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(content)
            })

    async def delete_two_way(self, data):
        content = {
            'command': 'room_delete_two_way',
            'room_id': data['room_id']
        }
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(content)
        })

    async def delete_one_way(self, data):
        content = {
            'command': 'room_delete_one_way',
            'room_id': data['room_id']
        }
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(content)
        })


    @sync_to_async
    def get_one_chat(self, chat_id):
    	return ccolections.find_one({'_id' : chat_id})
        # return ChatOneToOne.objects.get(id=int(chat_id))

    async def new_room(self, data):
        message_ = await self.create_new_room(data)
        content = {
            'command': 'new_room',
            'room':  await self.room_to_json(message_)
        }
        return await self.send_room_message(content)

    @sync_to_async
    def rooms_to_json(self, rooms):
        result = []
        for room in rooms:
            # user = None
            roomName = None
            if self.user == room.participants.owner:
                roomName = room.participants.friend.username
            else:
                roomName =  room.participants.owner.username
            message = room.messages.last()
            last_message = None
            if message != None:
                last_message = {'_id' : message.id,
                                'sender' : message.sender.username,
                                'content' : message.item.content,
                                'timestamp': str(message.timestamp)}
            lst = []
            
            # for user in  room.participants.friends.all():
            lst.append({
                "_id" : room.participants.friend.id,
                "username": room.participants.friend.username,
                'avatar' : "https://picsum.photos/200"
                })
            lst.append({
            "_id" : room.participants.owner.id,
            "username": room.participants.owner.username,
            'avatar' : "https://picsum.photos/200"
            })

            result.append({'roomId': room.id,
                'roomName': roomName,
                'unique_code': room.unique_code,
                'avatar' : "https://picsum.photos/200",
                'users' : lst,
                'last_message': last_message
            })
        return result

    @sync_to_async
    def room_to_json(self, room):
        roomName = None
        if self.user == room.participants.owner:
            roomName = room.participants.friend.username
        else:
            roomName =  room.participants.owner.username

        lst = []
            
        # for user in  room.participants.friends.all():
        lst.append({
            "_id" : room.participants.friend.id,
            "username": room.participants.friend.username,
            'avatar' : "https://picsum.photos/200"
            })
        lst.append({
            "_id" : room.participants.owner.id,
            "username": room.participants.owner.username,
            'avatar' : "https://picsum.photos/200"
        })
        return {
            'roomId': room.id,
            'roomName': roomName,
            'unique_code': room.unique_code,
            'avatar' : "https://picsum.photos/200",
            'users': lst
        }

    commands = {
        'fetch_room': fetch_room,
        'new_room': new_room
    }
    
    @sync_to_async
    def get_user1(self, username):
        return CustomUser.objects.get(username=username)

    async def websocket_connect(self, event):
        self.user = await self.get_user1(username=self.scope['url_route']['kwargs']['username'])
        self.chat = await self.get_chat()
        self.chat_room_id = f"notification_{self.user.id}"
        if self.user.is_authenticated:
                await self.channel_layer.group_add(
                    self.chat_room_id,
                    self.channel_name
                )
                await self.send({'type': 'websocket.accept'})
        else:
            await self.send({'type': 'websocket.close'})

    async def websocket_disconnect(self, close_code):
        await (self.channel_layer.group_discard)(
            self.chat_room_id,
            self.channel_name
        )
        raise StopConsumer()


    async def websocket_receive(self, event):
        text_data = event.get('text', None)
        data = json.loads(text_data)
        if  data['command'] == 'new_room' :
            if not data['message'] == '':
                await self.new_room(data)
        else:
            await self.fetch_room(data)

    async def send_room_message(self, message):
        await self.channel_layer.group_send(
            self.chat_room_id,
            {
                'type': 'room_message',
                'message': message
            }
        )

    async def send_message(self, message):
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(message)
            })

    async def room_message(self, event):
        message = event['message']
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(message)
            })
            

    @database_sync_to_async
    def create_new_room(self, data):
        message_ = None 
        # print(data)
        # self.sender = CustomUser.objects.get(username=data['sender'])
        # reciever_ = UserMessage.objects.create()
        # reciever_.users.add(*self.participants.friends.all()); reciever_.save()
        # if data['message_type'] == 'text':
        #     text_ = Text.objects.create(owner=self.user,  content=data['message'])
        #     message_ = Message.objects.create(sender=self.sender, reciever=reciever_, item=text_)

        # self.chat.messages.add(message_)
        return message_
    
    @database_sync_to_async
    def get_chat(self):
        try:
            lst = []
            for i in ChatOneToOne.objects.filter(hide=False).filter(Q(participants__friend=self.user) | Q(participants__owner=self.user) ):
                if self.user not in i.hide_user.all():
                    lst.append(i)
            return lst
        except Chat.DoesNotExist:
            return None

    @sync_to_async
    def get_all_room(self):
        return self.chat


class RoomConsumer(AsyncConsumer):

    async def fetch_room(self, data):
        rooms = await self.get_all_room()
        content = {
            'command': 'rooms',
            'rooms': await self.rooms_to_json(rooms)
        }
        await self.send_message(content)

    async def fetch_one_room(self, data):
        room = await self.get_one_chat(data['chat_id'])
        content = {
            'command': 'new_room',
            'room': await self.room_to_json(room)
        }
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(content)
            })


    @sync_to_async
    def get_one_chat(self, chat_id):
        return Chat.objects.get(id=int(chat_id))

    async def new_room(self, data):
        message_ = await self.create_new_room(data)
        content = {
            'command': 'new_room',
            'room':  await self.room_to_json(message_)
        }
        return await self.send_room_message(content)

    @sync_to_async
    def rooms_to_json(self, rooms):
        result = []
        for room in rooms:
            # user = None
            roomName = None
            if self.user == room.participants.owner:
                roomName = room.participants.friends.first().username
            else:
                roomName =  room.participants.owner.username
            message = room.messages.last()
            last_message = None
            if message != None:
                last_message = {'_id' : message.id,
                                'sender' : message.sender.username,
                                'content' : message.item.content,
                                'timestamp': str(message.timestamp)}
            result.append({'roomId': room.id,
                'roomName': roomName,
                'unique_code': room.unique_code,
                'last_message': last_message
            })

        return result

    @sync_to_async
    def room_to_json(self, room):
        roomName = None
        if self.user == room.participants.owner:
            roomName = room.participants.friends.first().username
        else:
            roomName =  room.participants.owner.username
        return {
            'roomId': room.id,
            'roomName': roomName,
            'unique_code': room.unique_code
        }

    commands = {
        'fetch_room': fetch_room,
        'new_room': new_room
    }

    async def websocket_connect(self, event):
        self.user = self.scope['user']
        self.chat = await self.get_chat()
        self.chat_room_id = f"notification_{self.user.id}"
        if self.user.is_authenticated:
                await self.channel_layer.group_add(
                    self.chat_room_id,
                    self.channel_name
                )
                await self.send({'type': 'websocket.accept'})
        else:
            await self.send({'type': 'websocket.close'})

    async def websocket_disconnect(self, close_code):
        await (self.channel_layer.group_discard)(
            self.chat_room_id,
            self.channel_name
        )
        raise StopConsumer()


    async def websocket_receive(self, event):
        text_data = event.get('text', None)
        data = json.loads(text_data)
        if  data['command'] == 'new_room' :
            if not data['message'] == '':
                await self.new_room(data)
        else:
            await self.fetch_room(data)

    async def send_room_message(self, message):
        await self.channel_layer.group_send(
            self.chat_room_id,
            {
                'type': 'room_message',
                'message': message
            }
        )

    async def send_message(self, message):
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(message)
            })

    async def room_message(self, event):
        message = event['message']
        await self.send({
            'type' : 'websocket.send',
            'text' :json.dumps(message)
            })
            

    @database_sync_to_async
    def create_new_room(self, data):
        message_ = None 
        # print(data)
        # self.sender = CustomUser.objects.get(username=data['sender'])
        # reciever_ = UserMessage.objects.create()
        # reciever_.users.add(*self.participants.friends.all()); reciever_.save()
        # if data['message_type'] == 'text':
        #     text_ = Text.objects.create(owner=self.user,  content=data['message'])
        #     message_ = Message.objects.create(sender=self.sender, reciever=reciever_, item=text_)

        # self.chat.messages.add(message_)
        return message_
    
    @database_sync_to_async
    def get_chat(self):
        try:
            chat = Chat.objects.all()
            return chat
        except Chat.DoesNotExist:
            return None

    @sync_to_async
    def get_all_room(self):
        return self.chat


# import json
# from channels.generic.websocket import AsyncWebsocketConsumer

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope['url_route']['kwargs']['room_name']
#         self.room_group_name = 'chat_%s' % self.room_name

#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     # Receive message from WebSocket
#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json['message']

#         # Send message to room group
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': message
#             }
#         )

#     # Receive message from room group
#     async def chat_message(self, event):
#         message = event['message']

#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({
#             'message': message
#         }))



# class ChatConsumer2(AsyncConsumer):

#     async def fetch_messages(self, data):
#         messages = await self.get_all_message()
#         content = {
#             'command': 'messages',
#             'messages': await self.messages_to_json(messages)
#         }
#         await self.send_message(content)

#     async def fetch_messages_view(self, data):
#         messages = await self.get_all_message()
#         content = {
#             'command': 'messages',
#             'messages': await self.messages_to_json(messages)
#         }
#         await self.send({
#             'type' : 'websocket.send',
#             'text' :json.dumps(content)
#             })
    
#     async def delete_two_way(self, data):
#         content = {
#             'command': 'delete_two_way',
#             'message_id': data['message_id']
#         }
#         await self.send({
#             'type' : 'websocket.send',
#             'text' :json.dumps(content)
#         })

#     async def delete_one_way(self, data):
#         content = {
#             'command': 'delete_one_way',
#             'message_id': data['message_id']
#         }
#         await self.send({
#             'type' : 'websocket.send',
#             'text' :json.dumps(content)
#         })
#     async def change_content(self, data):
#         content = {
#             'command': 'change_content',
#             'message_id': data['message_id']
#         }
#         await self.send({
#             'type' : 'websocket.send',
#             'text' :json.dumps(content)
#         })



    
#     async def new_message(self, data):
#         message_ = await self.create_message(data)
#         content = {
#             'command': 'new_message',
#             'message':  await self.message_to_json(message_)
#         }
#         print('new_message\n', content)
#         return await self.send_chat_message(content)
    
#     @sync_to_async
#     def message_to_json(self, message):
#         m = message.timestamp.minute
#         h = message.timestamp.hour
#         return {
#             '_id': message.id,
#             'senderId': str(message.sender.id),
#             'username': message.sender.username,
#             'content': message.item.content,
#             'type' : 'text',
#             'avatar' : "https://picsum.photos/200",
#             'timestamp': f'{f"0{h}" if h < 10 else f"{h}"}:{f"0{m}" if m < 10 else f"{m}"}',
#             "date": str(message.date),
#             'replyMessage':  self.parent_message_to_json(message.parent_message)
#         }

#     def parent_message_to_json(self, message):
#         if message == None:
#             return None
#         print('6', message, 'f', message.timestamp, 'ff', message.date)
#         print('ff', message.timestamp)

#         m = message.timestamp.minute
#         h = message.timestamp.hour
#         return {
#             '_id': message.id,
#             'senderId': str(message.sender.id),
#             'username': message.sender.username,
#             'content': message.item.content,
#             'type' : 'text',
#             'avatar' : "https://picsum.photos/200",
#             'timestamp': f'{f"0{h}" if h < 10 else f"{h}"}:{f"0{m}" if m < 10 else f"{m}"}',
#             "date": str(message.date)
#         }

#     @sync_to_async
#     def messages_to_json(self, messages):
#         result = []
#         for message in messages:
#             if message.item._meta.model_name == 'image':
#                 result.append({'_id': message.id,
#                     'senderId': str(message.sender.id),
#                     'username': message.sender.username,
#                     'type': 'image',
#                     'content': ImageCreateSerializer(instance=message.item).data['content'],
#                     'timestamp': str(message.timestamp),
#                     "date": str(message.date),
#                     'avatar' : "https://picsum.photos/200",
#                     'replyMessage':  self.parent_message_to_json(message.parent_message)
#                     })
#             else:
#                 m = message.timestamp.minute
#                 h = message.timestamp.hour
#                 print(message.timestamp)
#                 result.append({'_id': message.id,
#                     'senderId': str(message.sender.id),
#                     'username': message.sender.username,
#                     'content': message.item.content,
#                     'timestamp': f'{f"0{h}" if h < 10 else f"{h}"}:{f"0{m}" if m < 10 else f"{m}"}',
#                     "date": str(message.date),
#                     'type' : 'text',
#                     'avatar' : "https://picsum.photos/200",
#                     'replyMessage':  self.parent_message_to_json(message.parent_message)
#                 })
#         print(result)
#         return result

    

#     commands = {
#         'fetch_messages': fetch_messages,
#         'new_message': new_message
#     }
    
    
#     @sync_to_async
#     def get_user1(self, username):
#         return CustomUser.objects.get(username=username)

#     async def websocket_connect(self, event):
#         self.user = await self.get_user1(username=self.scope['url_route']['kwargs']['username'])
#         self.chat_id = self.scope['url_route']['kwargs']['chat_id']
#         self.chat = await self.get_chat()
#         self.chat_room_id = f"chat_{self.chat_id}"
#         if self.chat:
#             if await self.check_auth():
#                 await self.channel_layer.group_add(
#                     self.chat_room_id,
#                     self.channel_name
#                 )
#                 await self.send({'type': 'websocket.accept'})
#             else:
#                 await self.send({'type': 'websocket.close'})
#         else:
#             await self.send({'type': 'websocket.close'})

#     async def websocket_disconnect(self, close_code):
#         await (self.channel_layer.group_discard)(
#             self.chat_room_id,
#             self.channel_name
#         )
#         raise StopConsumer()


#     async def websocket_receive(self, event):
#         text_data = event.get('text', None)
#         data = json.loads(text_data)
#         if  data['command'] == 'new_message' :
#             if not data['message'] == '':
#                 await self.new_message(data)
#         # elif data['command'] == 'delete_message':
#         #     if data['type'] == 'one_way':
#         #         await self.delete_one_way(data)
#         #     else :
#         #         pass
#         else:
#             await self.fetch_messages(data)

#     async def send_chat_message(self, message):
#         await self.channel_layer.group_send(
#             self.chat_room_id,
#             {
#                 'type': 'chat_message',
#                 'message': message,
#                 'sender_channel_name': self.channel_name
#             }
#         )

#     async def send_message(self, message):
#         await self.send({
#             'type' : 'websocket.send',
#             'text' :json.dumps(message)
#             })

#     # async def chat_message(self, event):
#     #     message = event['message']
#     #     if self.channel_name != event['sender_channel_name']:
#     #         await self.send({
#     #         'type' : 'websocket.send',
#     #         'text' :json.dumps(message)
#     #         })
#     async def chat_message(self, event):
#         message = event['message']
#         await self.send({
#             'type' : 'websocket.send',
#             'text' :json.dumps(message)
#             })
#     @database_sync_to_async
#     def get_chat(self):
#         try:
#             chat = Chat.objects.get(unique_code=self.chat_id)
#             self.participants = chat.participants
#             return chat
#         except Chat.DoesNotExist:
#             return None

#     @database_sync_to_async
#     def create_message(self, data):
#         message_ = None 
#         print(data)
#         self.sender = self.user
#         if data['message_type'] == 'text':
#             parent = None 
#             if 'parent_message' in data:
#                 if data['parent_message'] != None:
#                     parent_id = int(data['parent_message'])
#                     parent = Message.objects.get(id=parent_id)
#             text_ = Text.objects.create(owner=self.user,  content=data['message'])
#             message_ = Message.objects.create(sender=self.sender,  item=text_, parent_message=parent)
#             message_.recievers.add(*self.participants.friends.all())
#             message_.recievers.add(self.participants.owner)
#             message_.recievers.add(self.user)
#             message_.save()
#         self.chat.messages.add(message_)
#         return message_
    
#     @sync_to_async
#     def check_auth(self):
#         return self.user in self.participants.friends.all() or self.user == self.participants.owner
        
#     @sync_to_async
#     def get_all_message(self):
#         lst = []
#         for i in  self.chat.messages.all():
#             if self.user in i.recievers.all():
#                 lst.append(i)
#         return lst