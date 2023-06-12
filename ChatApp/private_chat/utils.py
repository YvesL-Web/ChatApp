from django.utils import timezone
from django.core.paginator import Paginator
from django.core.serializers.python import Serializer

from private_chat.constants import MSG_TYPE_MESSAGE
from .models import PrivateChatRoom
from utils_Class_functions.calculate_timestamp import calculate_timestamp

def find_or_creating_private_chat(user1, user2):
    try:
        chat = PrivateChatRoom.objects.get(user1 =user1, user2=user2)
    except PrivateChatRoom.DoesNotExist:
        try:
            chat = PrivateChatRoom.objects.get(user1=user2, user2=user1)
        except Exception as e:
            chat = PrivateChatRoom(user1=user1, user2=user2)
            chat.save()
    return chat


class LazyRoomChatMessageEncode(Serializer):
    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'msg_type': MSG_TYPE_MESSAGE})
        dump_object.update({'user_id': obj.user.id})
        dump_object.update({'msg_id': obj.id})
        dump_object.update({'username': obj.user.username})
        dump_object.update({'message': obj.content})
        dump_object.update({'profile_image': obj.user.profile_image.url})
        dump_object.update({'natural_timestamp': calculate_timestamp(obj.timestamp)})
       
        return dump_object