from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
Account = get_user_model()


class PublicChatRoom(models.Model):
    title = models.CharField(max_length=255, unique=True, blank=True)
    users = models.ManyToManyField(Account, blank=True)

    def __str__(self):
        return self.title

    def connect_user(self, user):
        # Return True if use is added to the users list
        is_user_added = False
        if not user in self.users.all():
            self.users.add(user)
            self.save()
            is_user_added = True
        elif user in self.users.all():
            is_user_added = True
        return is_user_added

    def disconnect_user(self, user):
        # return true if user is removed from the users list
        is_user_removed = False
        if user in self.users.all():
            self.users.remove(user)
            self.save()
            is_user_removed = True

        return is_user_removed

    @property
    def group_name(self):
        # returns  the channels group name that sockets should subscribe to and get sent messages as they are generated
        return f"PublicChatRoom-{self.id}"


class PublicChatRoomMessageManager(models.Manager):
    def by_room(self, room):
        qs = PublicChatRoomMessage.objects.filter(
            room=room).order_by("-timestamp")
        return qs


class PublicChatRoomMessage(models.Model):
    # chat message created by a user inside a PublicRoom(foreign key)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    room = models.ForeignKey(PublicChatRoom, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False, blank=True)

    objects = PublicChatRoomMessageManager()

    def __str__(self):
        return self.content
