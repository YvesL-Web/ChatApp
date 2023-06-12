from django.urls import path
from . import views

urlpatterns = [
    path('accept_friend_request/<friend_request_id>/',
         views.accept_friend_request, name="accept-friend-request"),
    path('cancel_friend_request/', views.cancel_friend_request,
         name="cancel-friend-request"),
    path('decline_friend_request/<friend_request_id>/',
         views.decline_friend_request, name="decline-friend-request"),
    path('friend_list/<user_id>', views.friend_list_view, name="friend-list"),
    path('friend_requests/<user_id>',
         views.friend_requests_view, name="friend-requests"),
    path('remove_friend/', views.remove_friend, name="remove-friend"),
    path('send_friend_request/', views.send_friend_request_view,
         name="send-friend-request"),

]
