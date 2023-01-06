import string, random
from pyexpat import model
from django.db import models
from accounts.models import CustomUser

from django.contrib.contenttypes.fields import ContentType, GenericForeignKey, GenericRelation


def UniqueGenerator(length=35):
    letters = string.ascii_letters
    return ''.join([random.choice(letters) for i in range(length)])

def UniqueGeneratorOneToOne(length=30):
    letters = string.ascii_letters
    return ''.join([random.choice(letters) for i in range(length)])

class Contact(models.Model):
    owner       = models.ForeignKey(CustomUser, related_name='contacts', on_delete=models.CASCADE)
    friends     = models.ManyToManyField(CustomUser, blank=True)

    def __str__(self):
        return self.owner.username
    
    @property
    def list_5_first_friends(self):
        frinds =  self.friends.all()[0:5]
        return ' '.join([str(i) for i in frinds])

class UserMessage(models.Model):
    users          = models.ManyToManyField(CustomUser, blank=True)

class Message(models.Model):
    sender         = models.ForeignKey(CustomUser, related_name='messages_sender', on_delete=models.CASCADE)
    recievers      = models.ManyToManyField(CustomUser, related_name='messages_recievers')
    parent_message = models.ForeignKey('Message', related_name='child', null=True, on_delete=models.SET_NULL, blank=True)
    timestamp      = models.TimeField(auto_now_add=True)
    edited         = models.BooleanField(default=False)

    # created_time   = models.DateTimeField(auto_now_add = True)
    date           = models.DateField(auto_now_add=True)
    content_type   = models.ForeignKey(ContentType,
                                limit_choices_to = {
                                    'model__in':('text', 'video', 'image', 'file')
                                    },
                                on_delete=models.CASCADE)
    object_id   = models.PositiveIntegerField()
    item        = GenericForeignKey('content_type', 'object_id')

    
class ObjectBase(models.Model):
    owner        = models.ForeignKey(CustomUser, related_name="%(class)s_related", on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add = True)
    updated_time = models.DateTimeField(auto_now = True)
    model_content= GenericRelation(Message)
    # objects      = CustomObjectManager()
    class Meta:
        abstract = True

class Text(ObjectBase):
    content     = models.TextField(blank=True)
    
class Image(ObjectBase):
    content     = models.ImageField(upload_to= 'images')
    caption  = models.CharField(max_length = 250, blank=True)

class File(ObjectBase):
    content     = models.FileField(upload_to = 'file')
    caption  = models.CharField(max_length = 250, blank=True)

class Chat(models.Model):
    unique_code  = models.CharField(max_length=35, default=UniqueGenerator)
    participants = models.ForeignKey(Contact, related_name='chats', blank=True, on_delete=models.CASCADE)
    messages     = models.ManyToManyField(Message, blank=True)
    hide         = models.BooleanField(default=False)
    hide_user    = models.ManyToManyField(CustomUser, related_name='room_hide')

    def last_10_messages():
        return Message.objects.all().order_by('-timestamp')[:10]
    def __str__(self):
        return "{}".format(self.pk)

    @property
    def contact_owner(self):
        return self.participants
    @property
    def contact_id(self):
        return self.participants.id


class ContactOneToOne(models.Model):
    owner       = models.ForeignKey(CustomUser, related_name='contactOneToOnes', on_delete=models.CASCADE)
    friend      = models.ForeignKey(CustomUser, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.owner.username
    
class ChatOneToOne(models.Model):
    unique_code  = models.CharField(max_length=35, default=UniqueGeneratorOneToOne)
    participants = models.ForeignKey(ContactOneToOne, related_name='chatOneToOne', blank=True, on_delete=models.CASCADE)
    messages     = models.ManyToManyField(Message, related_name='chatonemessages', blank=True)
    hide         = models.BooleanField(default=False)
    hide_user    = models.ManyToManyField(CustomUser, related_name='chatOneToOne_hide')

    def last_10_messages():
        return Message.objects.all().order_by('-timestamp')[:10]
    def __str__(self):
        return "{}".format(self.pk)

    @property
    def contact_owner(self):
        return self.participants
    @property
    def contact_id(self):
        return self.participants.id












# from pyexpat import model
# from sqlite3 import Timestamp
# from django.db import models
# from django.contrib.auth import get_user_model

# User = get_user_model()

# class Contact(models.Model):
#     owner       = models.ForeignKey(User, related_name='friends',  on_delete=models.CASCADE )
#     friends     = models.ManyToManyField('Contact')

#     def __str__(self):
#         return self.owner.username
    
# class Message(models.Model):
#     contact     = models.ForeignKey(Contact, related_name="messages", on_delete=models.CASCADE)
#     content     = models.TextField()
#     Timestamp   = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.contact.user.username

# class Chat(models.Model):
#     participants= models.ManyToManyField(Contact, related_name="chats", blank=True) 
#     messages    = models.ManyToManyField(Message, blank=True)

#     def __str__(self):
#         return "{}".format(self.pk)









