import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.serializers.python import Serializer


from .models import PublicChatRoom, PublicChatRoomMessage
from .constants import *
from utils_Class_functions.calculate_timestamp import calculate_timestamp
from utils_Class_functions.ClientError import ClientError

User = get_user_model()



class PublicChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        # Called when the websocket is handshaking as part of initial connection
        print("PublicChatConsumer: connect:" + str(self.scope['user']))
        await self.accept()

        self.room_id = None

    async def disconnect(self, code):
        print("PublicChatConsumer: disconnect")
        try:
            if self.room_id != None:
                await self.leave_room(self.room_id)
        except Exception:
            pass

    async def receive_json(self, content):
        # called when we get a text frame. Channels will JSON-decode the payload for us
        # and pass it as the first argument.

        command = content.get("command", None)
        print("PublicChatConsumer: receive_json: " + str(command))
    
        try:
            if command == "send":
                if len(content['message'].strip()) == 0:
                    raise ClientError(422,"you can't send an empty message.")
                await self.send_room(content['room_id'], content['message'])
            elif command == "join":
                await self.join_room(content['room'])
            elif command == "leave":
                await self.leave_room(content['room'])
            elif command == "get_room_chat_messages":
                await self.display_progress_bar(True)
                room = await get_room_or_error(content['room_id'])
                payload = await get_room_chat_messages(room, content['page_number'])
                if payload != None:
                    payload  = json.loads(payload)
                    await self.send_messages_payload(payload['messages'], payload['new_page_number'])
                else:
                    raise ClientError(204, "Something went wrong while retrieving chatroom messages. ")
                await self.display_progress_bar(False)

        except ClientError as e:
            await self.display_progress_bar(False)
            await self.handle_client_error(e)
    
    async def send_room(self, room_id, message):
        # Called by receive_json when someone send a message to a room
        print("PubliChatConsumer: send_room")
        if self.room_id != None:
            if str(room_id) != str(self.room_id):
                raise ClientError("ROOM_ACCESS_DENIED", "room acces denied")
            if not is_authenticated(self.scope['user']):
                raise ClientError("AUTH_ERROR","You must be authenticated to chat.")
        else:
            raise ClientError("ROOM_ACCESS_DENIED", "Room access denied.")

        room = await get_room_or_error(room_id)
        await create_public_room_chat_message(room, self.scope['user'], message)

        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",# chat_message
                "profile_image": self.scope['user'].profile_image.url,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,
                "message": message,
            }
        )

    async def chat_message(self, event):
        #  called when someone has messaged our chat
        # send a message down to the client
        print("PublicChatConsumer: chat_message from user #: " +str(event['user_id']))
        timestamp = calculate_timestamp(timezone.now())
        await self.send_json({
            "msg_type": MSG_TYPE_MESSAGE ,
            "profile_image": event['profile_image'],
            "username": event['username'],
            "user_id": event['user_id'],
            "message": event['message'],
            "natural_timestamp": timestamp
        })

    async def join_room(self, room_id):
        """
            called by receive_json when someone sent Join command
        """
        print("PublicChatConsumer: join_room")
        is_auth = is_authenticated(self.scope['user'])
        try:
            room = await get_room_or_error(room_id)
        except ClientError as e:
            await self.handle_client_error(e)
        # add user to "users" List for room
        if is_auth:
            await connect_user(room, self.scope['user'])
        
        # store that we're in the room
        self.room_id = room.id

        #  Add them to the group so they get room messages
        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name
        )

        # Tell the client to finish opening the room
        await self.send_json({
            "join": str(room.id),
            "username": self.scope['user'].username
        })

        num_connected_users = await get_num_connected_users(room_id)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "connected.user.count", # connected_user_count
                "connected_user_count": num_connected_users
            }
        )

    async def leave_room(self, room_id):
        # called by receive_json when someone sent a leave command
        print("PublicChatConsumer: leave_room")
        is_auth  = is_authenticated(self.scope['user'])
        try:
            room = await get_room_or_error(room_id)
        except ClientError as e:
            await self.handle_client_error(e)

        # remove user from "users" List 
        if is_auth:
            await disconnect_user(room, self.scope['user'])

        # remove to the room
        self.room_id = None

        #  remove them to that they no longer receive room messages
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name
        )

        num_connected_users = await get_num_connected_users(room_id)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "connected.user.count", # connected_user_count
                "connected_user_count": num_connected_users
            }
        )
        
    async def send_messages_payload(self, messages, new_page_number):
        # sends a payload of messages to the UI
        print("PublicChatConsumer: send_messages_payload.")
        await self.send_json({
            "messages_payload": "messages_payload",
            "messages": messages,
            "new_page_number": new_page_number
        })

    async def handle_client_error(self, e):
        # called when clientError is raised
        # sends error data to the UI
        errorData = {}
        errorData['error'] = e.code
        if e.message:
            errorData['message'] = e.message
            await self.send_json(errorData)
        return 

    async def display_progress_bar(self, is_displayed):
        # 1. is_displayed = True ... Display the progress bar on UI
        # 2. is_displayed = False ... Hide the progress bar on UI
        print("Display Progress bar: " + str(is_displayed))
        await self.send_json({
            "display_progress_bar": is_displayed
        })

    async def connected_user_count(self, event):
        """
        called to send the number pf connected users to the room.
        This number is displayed in the room so other users knoy how many users are connected
        to the chat.
        """
        print("PublicChatConsumer: connected_user: " + str(event['connected_user_count']))
        await self.send_json({
            "msg_type": MSG_TYPE_CONNECTED_USER_COUNT,
            "connected_user_count": event["connected_user_count"]
        },)

@database_sync_to_async
def get_num_connected_users(room_id):
    users = PublicChatRoom.objects.get(pk=room_id).users
    if users:
        return len(users.all())
    return 0

def is_authenticated(user):
    if user.is_authenticated:
        return True
    return False

@database_sync_to_async
def create_public_room_chat_message(room, user, message):
    return PublicChatRoomMessage.objects.create(user=user, room=room, content=message)

@database_sync_to_async
def connect_user(room, user):
    return room.connect_user(user)

@database_sync_to_async
def disconnect_user(room, user):
    return room.disconnect_user(user)

@database_sync_to_async
def get_room_or_error(room_id):
    # Tries to fetch a room for the user
    try:
        room = PublicChatRoom.objects.get(pk = room_id)
    except PublicChatRoom.DoesNotExist:
        raise ClientError("ROOM_INVALID","Invalid room")
    return room


@database_sync_to_async
def get_room_chat_messages(room, page_number):
    try:
        qs = PublicChatRoomMessage.objects.by_room(room) # queryset
        p = Paginator(qs, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE) # Paginator

        payload = {}
        new_page_number = int(page_number)
        if new_page_number <= p.num_pages:
            new_page_number += 1
            s = LazyRoomChatMessageEncoder()
            payload['messages'] = s.serialize(p.page(page_number).object_list)
        else:
            payload['messages'] = "None"
        payload['new_page_number'] = new_page_number
        return json.dumps(payload)
    
    except Exception as e:
        print("Exception: " + str(e))
        return None

            

class LazyRoomChatMessageEncoder(Serializer):
    def get_dump_object(self, obj) :
        dump_object = {}
        dump_object.update({'msg_type': MSG_TYPE_MESSAGE})
        dump_object.update({'user_id': obj.user.id})
        dump_object.update({'msg_id': obj.id})
        dump_object.update({'username': obj.user.username})
        dump_object.update({'message': obj.content})
        dump_object.update({'profile_image': obj.user.profile_image.url})
        dump_object.update({'natural_timestamp': calculate_timestamp(obj.timestamp)})
       
        return dump_object