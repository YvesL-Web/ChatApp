DEFAULT_NOTIFICATION_PAGE_SIZE = 10

# General notification include:
# 1. FriendRequest
# 2. FriendList

GENERAL_MSG_TYPE_NOTIFICATIONS_PAYLOAD = 0 # New 'general' notifications data payload incoming
GENERAL_MSG_TYPE_PAGINATION_EXHAUSTED = 1
GENERAL_MSG_TYPE_NOTIFICATIONS_REFRESH_PAYLOAD = 2
GENERAL_MSG_TYPE_GET_NEW_NOTIFICATIONS = 3
GENERAL_MSG_TYPE_GET_NOTIFICATIONS_COUNT = 4
GENERAL_MSG_TYPE_UPDATED_NOTIFICATION = 5 # Update a notification that has been altered(ex:accpet/decline friend request)


PRIVATE_MSG_TYPE_NOTIFICATIONS_PAYLOAD = 10
PRIVATE_MSG_TYPE_PAGINATION_EXHAUSTED = 11
PRIVATE_MSG_TYPE_GET_NEW_NOTIFICATIONS = 13
PRIVATE_MSG_TYPE_UNREAD_NOTIFICATIONS_COUNT = 14