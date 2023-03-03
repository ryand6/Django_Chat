import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from .models import PublicChat, PublicMessages


class PublicChatRoomConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_group_name = 'public_chat'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()


    async def receive(self, text_data):
        # receives JSON data from javascript function when user sends message - converts
        # data into python dictionary to then broadcast to the room group 
        # all users inside the room group will receive this, and from there the chat_message
        # function will be called in each instance of PublicChatRoomConsumer
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        if not message:
            return
        current_user = self.scope['user']
        if current_user.is_authenticated:
            username = current_user.username
            profile_pic = current_user.profile_image.url

            try:
                # access the user model associated with the last posted message in the chat
                last_message = await database_sync_to_async(PublicMessages.objects.select_related('user').last)()
            except PublicMessages.DoesNotExist:
                last_message = None
            
            # if current user sent the last message that was posted in the chatroom, don't continue to display
            # their username and profile pic until someone else sends a new message
            if last_message:
                if last_message.user == current_user:
                    username = ""
                    profile_pic = ""

            try:
                self.chatroom = await database_sync_to_async(PublicChat.objects.get)(title=self.room_group_name)
            except PublicChat.DoesNotExist:
                self.chatroom = await database_sync_to_async(PublicChat.objects.create)(title=self.room_group_name)

            await self.save_message(current_user, message)

            await self.channel_layer.group_send(
                self.room_group_name,
                # event
                {
                    'type': 'chat.message',
                    'message': message,
                    'username': username,
                    'profile_pic': profile_pic,
                }
            )

    
    async def chat_message(self, event):
        # stores the "message" data from the receive functions event and stores in variable
        message = event['message']
        username = event['username']
        profile_pic = event['profile_pic']

        # sends message to WebSocket where javascript function then appends it to the chat log, thus
        # message is shown on all users inside the room group's browsers
        await self.send(text_data=json.dumps({
                'message': message,
                'username': username,
                'profile_pic': profile_pic
            }))


    async def save_message(self, user, message):
            await database_sync_to_async(PublicMessages.objects.create)(
                room=self.chatroom,
                user=user,
                message=message,
            )


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)