import json
import datetime

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import PermissionDenied
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from account.models import Account
from .models import PrivateMessages, PrivateChat
from home.views import sanitise_text


class PrivateChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'private_chat_{self.room_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        user_id = user.id
        await self.channel_layer.group_send(
            self.room_group_name,
            # event
            {
                'type': 'send.userid',
                'user_id': user_id,
                'status': 'connected',
            }
        )

    async def receive(self, text_data):
        # receives JSON data from javascript function when user sends message - converts
        # data into python dictionary to then broadcast to the room group 
        # all users inside the room group will receive this, and from there the chat_message
        # function will be called in each instance of PublicChatRoomConsumer
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        codeFlag = text_data_json["code"]
        language = text_data_json["language"]
        message = sanitise_text(message)
        if not message:
            return
        current_user = self.scope['user']
        if current_user.is_authenticated:
            username = current_user.username
            username_hidden = username
            profile_pic = current_user.profile_image.url
            try:
                # access the user model associated with the last posted message in the chat
                last_message = await database_sync_to_async(PrivateMessages.objects.select_related('user').last)()
            except PrivateMessages.DoesNotExist:
                last_message = None
            # if current user sent the last message that was posted in the chatroom, don't continue to display
            # their username and profile pic until someone else sends a new message - unless the message is sent
            # on a new day, in which case display profile pic and username regardless
            if last_message:
                last_message_date = str(last_message.created_at)[:10]
                current_message_date = str(datetime.date.today())
                if last_message.user == current_user and last_message_date == current_message_date:
                    username = ""
                    profile_pic = ""
            try:
                self.chatroom = await database_sync_to_async(PrivateChat.objects.get)(pk=self.room_id)
            except PrivateChat.DoesNotExist:
                raise PermissionDenied
            await self.save_message(current_user, message, codeFlag, language)
            try:
                # access the user model associated with the last posted message in the chat
                last_message = await database_sync_to_async(PrivateMessages.objects.select_related('user').last)()
                # convert timestamp to iso format so that it can be serialized
                timestamp = last_message.created_at.isoformat()
            except:
                timestamp = ""
            await self.channel_layer.group_send(
                self.room_group_name,
                # event
                {
                    'type': 'chat.message',
                    'message': message,
                    'code': codeFlag,
                    'language': language,
                    'username': username,
                    'profile_pic': profile_pic,
                    'timestamp': timestamp,
                    'username_hidden': username_hidden,
                    'room_id': self.room_id
                }
            )
    
    async def chat_message(self, event):
        # stores the "message" data from the receive functions event and stores in variable
        message = event['message']
        username = event['username']
        code = event['code']
        language = event['language']
        profile_pic = event['profile_pic']
        timestamp = event['timestamp']
        username_hidden = event['username_hidden']
        room_id = event['room_id']
        # sends message to WebSocket where javascript function then appends it to the chat log, thus
        # message is shown on all users inside the room group's browsers
        await self.send(text_data=json.dumps({
                'message': message,
                'username': username,
                'code': code,
                'language': language,
                'profile_pic': profile_pic,
                'timestamp': timestamp,
                'username_hidden': username_hidden,
                'room_id': room_id
            })) 

    async def send_userid(self, event):
        user_id = event['user_id']
        status = event['status']
        online = False
        if status == "connected":
            online = True
        await self.set_user_status(user_id, online)
        await self.send(text_data=json.dumps({'user_id': user_id, 'status': status}))

    @database_sync_to_async
    def set_user_status(self, user_id, online):
        user = Account.objects.get(pk=user_id)
        user.online = online
        user.save()

    async def save_message(self, user, message, codeFlag, language):
        await database_sync_to_async(PrivateMessages.objects.create)(
            room=self.chatroom,
            user=user,
            message=message,
            code=codeFlag,
            language=language
        )

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


class AllPrivateChatRoomsConsumer(AsyncWebsocketConsumer):
    consumers = {}

    async def connect(self):
        self.user = self.scope['user']
        self.user_id = self.user.id
        self.add_consumer_instance()
        if self.user.is_anonymous:
            await self.close()
        self.chatrooms = await database_sync_to_async(list)(self.user.chatrooms.all())
        self.group_name_all_chats = f'all_chats_{self.user.id}'
        # add room_group_name of each private chat user is a part of to the channel layer
        for chatroom in self.chatrooms:
            room_group_name = f'private_chat_{chatroom.pk}'
            await self.channel_layer.group_add(
                room_group_name,
                self.channel_name
            )
        # add a group that can interact with all of the users private chats
        await self.channel_layer.group_add(
            self.group_name_all_chats,
            self.channel_name
        )
        await self.accept()

    def add_consumer_instance(self):
        AllPrivateChatRoomsConsumer.consumers[self.user_id] = self

    def remove_consumer_instance(self):
        del AllPrivateChatRoomsConsumer.consumers[self.user_id]

    async def disconnect(self, close_code):
        # Unsubscribe the user from all chatrooms they're a part of
        for chatroom in self.chatrooms:
            room_group_name = f'private_chat_{chatroom.pk}'
            await self.channel_layer.group_discard(
                room_group_name,
                self.channel_name
            )

    # receives event from PrivateChatRoomConsumer when message is sent in private chat
    async def chat_message(self, event):    
        room_id = event['room_id']
        # Send the chatroom ID to the WebSocket
        await self.send(text_data=json.dumps({
            'room_id': room_id,
        }))

    async def send_userid(self, event):
        user_id = event['user_id']
        status = event['status']
        online = False
        if status == "connected":
            online = True
        await self.set_user_status(user_id, online)
        await self.send(text_data=json.dumps({'user_id': user_id, 'status': status}))

    @database_sync_to_async
    def set_user_status(self, user_id, online):
        user = Account.objects.get(pk=user_id)
        user.online = online
        user.save()

    
    # has to be synchronous the create_chat function in the privatechat views.py
    # adds the users properly 
    def add_user_to_chat_groups(self, id):
        room_group_name = f'private_chat_{id}'
        self.channel_layer.group_add(room_group_name, self.channel_name)


# when users are added to an instance of PrivateChat, call the add_user_to_chat_groups method
# of the instance of AllPrivateChatRoomsConsumer that matches that new users id in order for their
# room group name to be added to AllPrivateChatRoomsConsumer's channel_layer
@receiver(m2m_changed, sender=PrivateChat.users.through)
def update_private_chat(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add' or action == 'pre_add':
        for user in instance.users.all():
            consumer = AllPrivateChatRoomsConsumer.consumers.get(user.id)
            if consumer:
                consumer.add_user_to_chat_groups(instance.id)