from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from itertools import chain

from .models import PrivateChatRoom, PrivateChatRoomMessage
from .utils import find_or_creating_private_chat


Account = get_user_model()
DEBUG = False

# Create your views here.

@login_required(login_url='login')
def private_chat_room_view(request):
    user = request.user
    room_id = request.GET.get("room_id")

    context = {}
    if room_id:
        try:
            room = PrivateChatRoom.objects.get(pk=room_id) 
            context['room'] = room
        except PrivateChatRoom.DoesNotExist:
            pass
        
    # 1. Find all the rooms this user is a part of
    # rooms1 = PrivateChatRoom.objects.filter(user1=user, is_active = True )
    # rooms2 = PrivateChatRoom.objects.filter(user2=user, is_active = True)
    rooms = PrivateChatRoom.objects.filter(Q(user1=user)|Q(user2=user), is_active=True)
  
    # 2. Merge the lists
    # rooms = list(chain(rooms1, rooms2))

    # m_and_f: messages and friends
    # format: [{"message":"yo", "friend":"Yves"},{"message":"on dit quoi?", "friend":"Henri"}]
    m_and_f = []
    for room in rooms:
        # Figure out which user is the "friend"
        if room.user1 == user:
            friend = room.user2
        else:
            friend = room.user1
        m_and_f.append({
            "message":"",
            "friend":friend
        })
    print(rooms)
    print(m_and_f)
    context['m_and_f'] = m_and_f
    context['debug'] = DEBUG
    context['debug_mode'] = settings.DEBUG

    return render(request,'private_chat/room.html', context)

@login_required(login_url='login')
def create_or_return_private_chat(request):
    user1 = request.user
    payload = {}
    if request.method == "POST":
        user2_id = request.POST["user2_id"]
        try :
            user2 = Account.objects.get(pk = user2_id)
            chat = find_or_creating_private_chat(user1, user2)
            payload['response'] = "Successfully got the chat."
            payload['chatroom_id'] = chat.id  
        except Account.DoesNotExist:
            payload['response'] = "Unable to start a chat with that user."
    
    return JsonResponse(payload)