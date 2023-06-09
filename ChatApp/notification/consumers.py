from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.paginator import Paginator
from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType

from datetime import datetime
import json

from friend.models import FriendRequest, FriendList
from .utils import LazyNotificationEncoder
from .constants import *
from .models import Notification
from utils_Class_functions.ClientError import ClientError
from private_chat.models import UnreadPrivateChatRoomMessages

class NotificationConsumer(AsyncJsonWebsocketConsumer):
	"""
	Passing data to and from header.html. Notifications are displayed as "drop-downs" in the nav bar.
	There is two major categories of notifications:
			1. General Notifications
					1. FriendRequest
					2. FriendList
			1. Chat Notifications
					1. UnreadPrivateChatRoomMessages
	"""

	async def connect(self):
		"""
		Called when the websocket is handshaking as part of initial connection.
		"""
		print("NotificationConsumer: connect: " + str(self.scope["user"]))
		await self.accept()

	async def disconnect(self, code):
		"""
		Called when the WebSocket closes for any reason.
		"""
		print("NotificationConsumer: disconnect")

	async def receive_json(self, content):
		"""
		Called when we get a text frame. Channels will JSON-decode the payload
		for us and pass it as the first argument.
		"""
		command = content.get("command", None)
		print("NotificationConsumer: receive_json. Command: " + command)
		try:
			if command == "get_general_notifications":
				payload = await get_general_notifications(self.scope['user'], content['page_number'])
				if payload == None:
					await self.general_pagination_exhausted()
				else:
					payload = json.loads(payload)
					await self.send_general_notifications_payload(payload['notifications'],payload['new_page_number'])
			elif command == "accept_friend_request":
				notification_id = content['notification_id']
				payload = await accept_friend_request(self.scope['user'], notification_id)
				if payload == None:
					raise ClientError("AUTH_ERROR","Something went wrong. Try refreshing the browser.")
				else:
					payload = json.loads(payload)
					await self.send_updated_friend_request_notification(payload['notification'])
			elif command == "decline_friend_request":
				notification_id = content['notification_id']
				payload = await decline_friend_request(self.scope['user'], notification_id)
				if payload == None:
					raise ClientError("AUTH_ERROR","Something went wrong. Try refreshing the browser.")
				else:
					payload = json.loads(payload)
					await self.send_updated_friend_request_notification(payload['notification'])
			elif command =="refresh_general_notifications":
				payload = await refresh_general_notifications(self.scope['user'], content['oldest_timestamp'], content['newest_timestamp'])
				if payload == None:
					raise ClientError("AUTH_ERROR", "Something went wrong. Try refreshing the browser.")
				else:
					payload = json.loads(payload)
					await self.send_general_refreshed_notifications_payload(payload['notifications'])
			elif command == "get_new_general_notifications":
				payload = await get_new_general_notifications(self.scope['user'], content['newest_timestamp'])
				if payload != None:
					payload = json.loads(payload)
					await self.send_new_general_notifications_payload(payload['notifications'])
			elif command == "get_unread_general_notifications_count":
				payload = await get_unread_general_notifications_count(self.scope['user'])
				if payload != None:
					payload = json.loads(payload)
					await self.send_unread_general_notifications_count(payload['count'])
			elif command == "mark_notifications_read":
				await mark_notifications_read(self.scope['user'])
			elif command == "get_private_notifications":
				payload = await get_private_notifications(self.scope['user'], content['page_number'])
				if payload == None:
					await self.private_pagination_exhausted()
				else:
					payload = json.loads(payload)
					await self.send_private_notifications_payload(payload['notifications'], payload['new_page_number'])
			elif command == "get_new_private_notifications":
				payload = await get_new_private_notifications(self.scope['user'], content['newest_timestamp'])
				if payload != None:
					payload = json.loads(payload)
					await self.send_new_private_notifications_payload(payload['notifications'])
				# else:
					#send an error report later
			elif command == "get_unread_private_notifications_count":
				try:
					payload = await get_unread_private_notifications_count(self.scope["user"])
					if payload != None:
						payload = json.loads(payload)
						await self.send_unread_private_notifications_count(payload['count'])
				except Exception as e:
					print("UNREAD CHAT MESSAGE COUNT EXCEPTION: " + str(e))
					pass

				
		except ClientError as e:
			print("Exception: NotificationConsumer" + str(e))
			pass
		
	async def display_progress_bar(self, shouldDisplay):
		print("NotificationConsumer: display_progress_bar: " + str(shouldDisplay))
		await self.send_json(
			{
				"progress_bar": shouldDisplay,
			},
		)
	
	async def send_general_notifications_payload(self, notifications, new_page_number):
		# called by receive_json when ready to send a json array of the notifications
		await self.send_json({
			'general_msg_type': GENERAL_MSG_TYPE_NOTIFICATIONS_PAYLOAD,
			'notifications': notifications,
			'new_page_number': new_page_number,
		})
	
	async def send_updated_friend_request_notification(self, notification):
		# After friend request is accepted or declined,
		# send the updated notification to template
		# payload contains 'notification' and 'response'
		# 1. payload['notification]
	
		await self.send_json({
			"general_msg_type": GENERAL_MSG_TYPE_UPDATED_NOTIFICATION,
			"notification": notification
		})

	async def general_pagination_exhausted(self):
		# called by receive_json when pagination is exhausted for general notification
		await self.send_json({
			"general_msg_type" : GENERAL_MSG_TYPE_PAGINATION_EXHAUSTED,
		})

	async def send_general_refreshed_notifications_payload(self, notifications):
		await self.send_json({
			"general_msg_type": GENERAL_MSG_TYPE_NOTIFICATIONS_REFRESH_PAYLOAD,
			"notifications": notifications
		})
	async def send_new_general_notifications_payload(self, notifications):
		await self.send_json({
			"general_msg_type": GENERAL_MSG_TYPE_GET_NEW_NOTIFICATIONS,
			"notifications": notifications,
		})
	
	async def send_unread_general_notifications_count(self, count):
		await self.send_json({
			"general_msg_type": GENERAL_MSG_TYPE_GET_NOTIFICATIONS_COUNT,
			"count": count,
		})

	async def send_private_notifications_payload(self, notifications, new_page_number):
		await self.send_json({
			"private_msg_type": PRIVATE_MSG_TYPE_NOTIFICATIONS_PAYLOAD,
			"notifications": notifications,
			"new_page_number": new_page_number,
		})

	async def send_new_private_notifications_payload(self, notifications):
		await self.send_json({
			"private_msg_type": PRIVATE_MSG_TYPE_GET_NEW_NOTIFICATIONS,
			"notifications": notifications
		})

	async def private_pagination_exhausted(self):
		await self.send_json({
			"chat_msg_type": PRIVATE_MSG_TYPE_PAGINATION_EXHAUSTED,	
		})
	
	async def send_unread_private_notifications_count(self, count):
		await self.send_json({
			"private_msg_type":PRIVATE_MSG_TYPE_UNREAD_NOTIFICATIONS_COUNT,
			"count":count
		})

@database_sync_to_async
def get_general_notifications(user, page_number):
	"""
	Get General Notifications with Pagination (next page of results).
	This is for appending to the bottom of the notifications list.
	General Notifications are:
	1. FriendRequest
	2. FriendList
	"""
	if user.is_authenticated:
		friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
		friend_list_ct = ContentType.objects.get_for_model(FriendList)
		notifications = Notification.objects.filter(target=user, content_type__in=[friend_request_ct, friend_list_ct]).order_by("-timestamp")
		p = Paginator(notifications, DEFAULT_NOTIFICATION_PAGE_SIZE)
                
		payload = {}
		if len(notifications) > 0:
			if len(page_number) <= p.num_pages:
				s = LazyNotificationEncoder()
				serialized_notifications = s.serialize(p.page(page_number).object_list)
				payload['notifications'] = serialized_notifications
				new_page_number = int(page_number) + 1
				payload['new_page_number'] = new_page_number
		else:
			return None
	else:
		raise ClientError("User must be authenticated to get notifications ")
	return json.dumps(payload)


@database_sync_to_async
def accept_friend_request(user, notification_id):
	payload = {}
	if user.is_authenticated:
		try:
			notification = Notification.objects.get(pk=notification_id)
			friend_request = notification.content_object
			# confirm this is the correct user
			if friend_request.receiver == user:
				updated_notification = friend_request.accept()
				s = LazyNotificationEncoder()
				payload['notification'] = s.serialize([updated_notification])[0]
				return json.dumps(payload)
		except Notification.DoesNotExist:
			raise ClientError("AUTH_ERROR", "An error occured with that notification.Try refreshing the browser.")
		return None
	
@database_sync_to_async
def decline_friend_request(user, notification_id):
	payload = {}
	if user.is_authenticated:
		try:
			notification = Notification.objects.get(pk=notification_id)
			friend_request = notification.content_object
			# confirm this is the correct user
			if friend_request.receiver == user:
				updated_notification = friend_request.decline()
				s = LazyNotificationEncoder()
				payload['notification'] = s.serialize([updated_notification])[0]
				return json.dumps(payload)
		except Notification.DoesNotExist:
			raise ClientError("AUTH_ERROR", "An error occured with that notification.Try refreshing the browser.")
		return None
	
@database_sync_to_async
def refresh_general_notifications(user, oldest_timestamp, newest_timestamp):
	payload = {}
	if user.is_authenticated:
		oldest_ts = oldest_timestamp[0:oldest_timestamp.find("+")]
		oldest_ts = datetime.strptime(oldest_ts, "%Y-%m-%d %H:%M:%S.%f")
		newest_ts = newest_timestamp[0:newest_timestamp.find("+")]
		newest_ts = datetime.strptime(newest_ts, "%Y-%m-%d %H:%M:%S.%f")
		friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
		friend_list_ct = ContentType.objects.get_for_model(FriendList)

		notifications = Notification.objects.filter(
			target=user, content_type__in=[friend_request_ct, friend_list_ct], 
			timestamp__gte=oldest_ts, timestamp__lte=newest_ts).order_by("-timestamp")
		
		s = LazyNotificationEncoder()
		payload['notifications'] = s.serialize(notifications)
	else:
		raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications")
	return json.dumps(payload)

@database_sync_to_async
def get_new_general_notifications(user, newest_timestamp):

	payload = {}
	if user.is_authenticated:
		timestamp = newest_timestamp[0:newest_timestamp.find("+")]
		timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
		friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
		friend_list_ct = ContentType.objects.get_for_model(FriendList)

		notifications = Notification.objects.filter(
			target=user, content_type__in=[friend_request_ct, friend_list_ct], 
			timestamp__gt=timestamp, is_read=False).order_by("-timestamp")
		
		s = LazyNotificationEncoder()
		payload['notifications'] = s.serialize(notifications)
		return json.dumps(payload)
	else:
		raise ClientError("AUTH_ERROR","User must be authenticated to get notifications.")
	
@database_sync_to_async
def get_unread_general_notifications_count(user):
	payload = {}
	if user.is_authenticated:
		friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
		friend_list_ct = ContentType.objects.get_for_model(FriendList)
		notifications = Notification.objects.filter(
			target=user, content_type__in=[friend_request_ct, friend_list_ct],
			is_read=False).order_by("-timestamp")
		unread_count = 0
		if notifications:
			for notification in notifications:
				if not notification.is_read:
					unread_count = unread_count + 1
		payload['count'] = unread_count
		print(payload)
		return json.dumps(payload)
		
	else:
		raise ClientError("AUTH_ERROR", "You must be authenticated to get notifications.")
	return None

@database_sync_to_async
def mark_notifications_read(user):
	if user.is_authenticated:
		notifications = Notification.objects.filter(target=user)
		if notifications:
			for notification in notifications:
				notification.is_read = True
				notification.save()
	return 

@database_sync_to_async
def get_private_notifications(user, page_number):
	
	if user.is_authenticated:
		chatmessage_ct = ContentType.objects.get_for_model(UnreadPrivateChatRoomMessages)
		notifications = Notification.objects.filter(target=user, content_type=chatmessage_ct).order_by("-timestamp")
		p = Paginator(notifications, DEFAULT_NOTIFICATION_PAGE_SIZE)

		payload={}
		if len(notifications) > 0:
			if int(page_number)<= p.num_pages:
				s = LazyNotificationEncoder()
				serialized_notifications = s.serialize(p.page(page_number).object_list)
				payload['notifications'] = serialized_notifications
				new_page_number = int(page_number) +1
				payload['new_page_number'] = new_page_number
				return json.dumps(payload)
		else:
			return None	
	else:
		raise ClientError("AUTH_ERROR","User must be authenticated to get notifications")
	return None

@database_sync_to_async
def get_new_private_notifications(user, newest_timestamp):
	payload = {}
	if user.is_authenticated:
		timestamp = newest_timestamp[0:newest_timestamp.find("+")]
		timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
		chatmessage_ct = ContentType.objects.get_for_model(UnreadPrivateChatRoomMessages)
		notifications = Notification.objects.filter(target=user, content_type__in=[chatmessage_ct], timestamp__gt=timestamp).order_by("-timestamp")
		s = LazyNotificationEncoder()
		payload['notifications'] = s.serialize(notifications)
		return json.dumps(payload)
	else:
		ClientError("AUTH_ERROR", "User must be authenticated to get notifications")
	return None

@database_sync_to_async
def get_unread_private_notifications_count(user):
    payload = {}
    if user.is_authenticated:
        chatmessage_ct = ContentType.objects.get_for_model(UnreadPrivateChatRoomMessages)
        notifications = Notification.objects.filter(target=user, content_type__in=[chatmessage_ct])
        
        unread_count = 0
        if notifications:
            unread_count = len(notifications.all())
        payload['count'] = unread_count
        print(payload)
        return json.dumps(payload)
    else:
        raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
    return None