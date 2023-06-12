from friend.models import FriendList
from private_chat.utils import find_or_creating_private_chat
friend_list = FriendList.objects.all()
for f in friend_list:
    for friend in f.friends.all():
        chat = find_or_creating_private_chat(f.user, friend)
        chat.is_active = True
        chat.save()