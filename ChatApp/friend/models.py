from django.utils import timezone
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.conf import settings
from django.shortcuts import redirect

from private_chat.utils import find_or_creating_private_chat
from notification.models import Notification

Account = get_user_model()


# Create your models here.
class FriendList(models.Model):
    user = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="user")
    friends = models.ManyToManyField(
        Account, blank=True, related_name="friends")

    # for reverse lookups
    notifications = GenericRelation(Notification)

    def __str__(self):
        return self.user.username

    def add_friend(self, account):
        # Add a new friend
        if not account in self.friends.all():
            self.friends.add(account)
            self.save()

            content_type = ContentType.objects.get_for_model(self)
            # create notification
            # Notification(target=self.user, from_user=account, redirect_url=f"{settings.BASE_URL}/account/{account.pk}")
            # Notification(
            #     target=self.user,
            #     from_user=account,
            #     redirect_url=redirect('profile', account.pk),
            #     verb=f"You are now friend with {account.username}",
            #     content_type=content_type,
            #     object_id=self.id,
            # ).save()
            # other way
            self.notifications.create(
                target=self.user,
                from_user=account,
                redirect_url=redirect('profile', account.pk),
                verb=f"You are now friend with {account.username}",
                content_type=content_type,
            )
            self.save()

            chat = find_or_creating_private_chat(self.user, account)
            if not chat.is_active:
                chat.is_active = True
                chat.save()

    def remove_friends(self, account):
        # Remove a friend
        if account in self.friends.all():
            self.friends.remove(account)
            self.save()

            chat = find_or_creating_private_chat(self.user, account)
            if chat.is_active:
                chat.is_active = False
                chat.save()

    def unfriend(self, removee):
        # Initiate the action of unfriending someone.
        remover_friends_list = self  # person terminating the friendship

        # Remove friend from remove friend list
        remover_friends_list.remove_friends(removee)

        # remove friend from removee friendlist
        friends_list = FriendList.objects.get(user=removee)
        friends_list.remove_friends(self.user)

        content_type = ContentType.objects.get_for_model(self)

        # create notification for removee
        self.notifications.create(
            target=removee,
            from_user=self.user,
            redirect_url=redirect('profile', self.user.pk),
            verb=f"You are no longer friend with {self.user.username}",
            content_type=content_type,
        )
        # self.save()

        # create notification for remover
        self.notifications.create(
            target=self.user,
            from_user=removee,
            redirect_url=redirect('profile', removee.pk),
            verb=f"You are no longer friend with {removee.username}",
            content_type=content_type,
        )
        # self.save()

    def is_mutual_friend(self, friend):
        # are we friend?
        if friend in self.friends.all():
            return True
        return False

    @property
    def get_cname(self):
        # for determining what kind of object is associated with a Notification
        return "FriendList"


class FriendRequest(models.Model):
    sender = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="receiver")
    is_active = models.BooleanField(blank=True, null=False, default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    notifications = GenericRelation(Notification)

    def __str__(self):
        return self.sender.username

    def accept(self):
        # accept a friend request
        # Update both sender and receiver lists

        receiver_friend_list = FriendList.objects.get(user=self.receiver)
        if receiver_friend_list:
            content_type = ContentType.objects.get_for_model(self)
            # update notification for RECEIVER
            receiver_notification = Notification.objects.get(
                target=self.receiver, content_type=content_type, object_id=self.id)
            receiver_notification.is_active = False
            receiver_notification.redirect_url = redirect('profile', self.sender.pk)
            receiver_notification.verb = f"You accepted {self.sender.username}'s friend request"
            receiver_notification.timestamp = timezone.now()
            receiver_notification.save()

            receiver_friend_list.add_friend(self.sender)

            sender_friend_list = FriendList.objects.get(user=self.sender)
            if sender_friend_list:
                # create a notification for the sender
                self.notifications.create(
                    target=self.sender,
                    from_user=self.receiver,
                    redirect_url=redirect('profile', self.receiver.pk),
                    verb=f"{self.receiver.username} accepted your friend request.",
                    content_type=content_type,
                )
                sender_friend_list.add_friend(self.receiver)
                self.is_active = False
                self.save()
            return receiver_notification

    def decline(self):
        # Decline a friend request
        # It is "declined" by setting the "is_active" to False
        self.is_active = False
        self.save()

        content_type = ContentType.objects.get_for_model(self)
        # update notification for RECEIVER
        receiver_notification = Notification.objects.get(
            target=self.receiver, content_type=content_type, object_id=self.id)
        receiver_notification.is_active = False
        receiver_notification.redirect_url = redirect('profile', self.sender.pk)
        receiver_notification.verb = f"You declined {self.sender.username}'s friend request"
        receiver_notification.timestamp = timezone.now()
        receiver_notification.save()

        # create a notification for the sender
        self.notifications.create(
            target=self.sender,
            from_user=self.receiver,
            redirect_url=redirect('profile', self.receiver.pk),
            verb=f"{self.receiver.username} declined your friend request.",
            content_type=content_type,
        )
        return receiver_notification

    def cancel(self):
        # Cancel friend request
        # It is "canceled" by setting the "is_active" to False
        self.is_active = False
        self.save()

        content_type = ContentType.objects.get_for_model(self)
        # update notification for RECEIVER
        receiver_notification = Notification.objects.get(
            target=self.receiver, content_type=content_type, object_id=self.id)
        receiver_notification.is_active = False
        receiver_notification.redirect_url = redirect('profile', self.sender.pk)
        receiver_notification.verb = f"{self.sender.username} cancelled the friend request."
        receiver_notification.timestamp = timezone.now()
        receiver_notification.save()

        # create a notification for the sender
        self.notifications.create(
            target=self.sender,
            from_user=self.receiver,
            redirect_url=redirect('profile', self.receiver.pk),
            verb=f"You cancelled the friend request to {self.receiver.username}.",
            content_type=content_type,
        )

    @property
    def get_cname(self):
        # for determining what kind of object is associated with a Notification
        return "FriendRequest"


# Signal

@receiver(post_save, sender=Account)
def create_friend_list(sender, instance, created, **kwargs):
    if created:
        FriendList.objects.create(user=instance)

@receiver(post_save, sender=FriendRequest)
def create_notification(sender, instance, created, **kwargs):
    if created:
        instance.notifications.create(
            target = instance.receiver,
            from_user = instance.sender,
            redirect_url = redirect('profile', instance.sender.pk),
            verb = f"{instance.sender.username} sent you a friend request.",
            content_type = instance,
        )