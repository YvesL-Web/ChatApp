from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings

from notification.models import Notification

# Create your models here.

Account = get_user_model()

class PrivateChatRoom(models.Model):
    user1 = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='user1')
    user2 = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='user2')
    connected_users = models.ManyToManyField(Account, blank=True, related_name="connected_users")
    is_active = models.BooleanField(default=True)

    # returns true if user is added to the connected_users list
    def connect_user(self, user):
        is_user_added = False
        if not user in self.connected_users.all():
            self.connected_users.add(user)
            is_user_added = True
        return is_user_added

    def disconnect_user(self, user):
        is_user_removed = False
        if user in self.connected_users.all():
            self.connected_users.remove(user)
            is_user_removed = True
        return is_user_removed

    def __str__(self):
        return f"A Chat between {self.user1} and {self.user2}"
    
    @property
    def group_name(self):
        """
        returns the channels group name that sockets shouls subscribe to so 
        they get sent messages as they are generated
        """
        return f"privateChatRoom-{self.id}"
    

class PrivateChatRoomMessageManager(models.Manager):
    def by_room(self, room):
        qs = PrivateChatRoomMessage.objects.filter(room=room).order_by("-timestamp")
        return qs

class PrivateChatRoomMessage(models.Model):
    # Chat message created by a user inside a room

    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    room = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False, blank=False)

    objects = PrivateChatRoomMessageManager()

    def __str__(self) :
        return self.content
    

class UnreadPrivateChatRoomMessages(models.Model):
    room = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    most_recent_message = models.CharField(max_length=100, blank=True, null=True)
    reset_timestamp = models.DateTimeField()
    notifications = GenericRelation(Notification)

    def __str__(self):
        return f"Messages that {self.user.username} has not read yet."
    
    def save(self,*args, **kwargs):
        if not self.id: # if just created, add a timestamp. otherwise do not automatically change it.
            self.reset_timestamp = timezone.now()
        return super(UnreadPrivateChatRoomMessages, self).save(*args, **kwargs)
    
    # for determining what kind of object is associated with a notification
    @property
    def get_cname(self):
        return "UnreadPrivateChatRoomMessages"
    
    # Get the other user in the chatroom
    @property
    def get_other_user(self):
        if self.user == self.room.user1:
            return self.room.user2
        else:
            return self.room.user1
        
    
# signal
@receiver(post_save, sender=PrivateChatRoom)
def create_unread_private_chatroom_messages_obj(sender, instance, created, **kwargs):
    if created:
        unread_msg1 = UnreadPrivateChatRoomMessages(room=instance, user=instance.user1)
        unread_msg1.save()

        unread_msg2 = UnreadPrivateChatRoomMessages(room=instance, user=instance.user2)
        unread_msg2.save()

# when the unread message count increases, update the notification.
# if one does not exist, create one.(This should never happen)
@receiver(pre_save, sender=UnreadPrivateChatRoomMessages)
def increment_unread_msg_count(sender, instance, **kwargs):
    if instance.id is None:
        pass
    else:
        previous = UnreadPrivateChatRoomMessages.objects.get(id=instance.id)
        if previous.count < instance.count:
            content_type = ContentType.objects.get_for_model(instance)
            if instance.user == instance.room.user1:
                other_user = instance.room.user2
            else:
                other_user = instance.room.user1
            try:
                notification = Notification.objects.get(target=instance.user, content_type=content_type, object_id=instance.id)
                notification.verb = instance.most_recent_message
                notification.timestamp = timezone.now()
                notification.save()
            except Notification.DoesNotExist:
                instance.notifications.create(
                    target =instance.user,
                    from_user = other_user,
                    redirect_url = f"{settings.BASE_URL}/private-chat/?room_id={instance.room.id}",
                    verb = instance.most_recent_message,
                    content_type = content_type
                )

# if the unread message count decreases, it means the user joined the chat. so delete the notification.
@receiver(pre_save, sender=UnreadPrivateChatRoomMessages)
def remove_unread_msg_count_notification(sender, instance, **kwargs):
    if instance.id is None:
        pass
    else:
        previous = UnreadPrivateChatRoomMessages.objects.get(id=instance.id)
        if previous.count > instance.count:
            content_type = ContentType.objects.get_for_model(instance)
            try:
                notification = Notification.objects.get(target=instance.user, content_type=content_type, object_id=instance.id)
                notification.delete()
            except Notification.DoesNotExist:
                pass

