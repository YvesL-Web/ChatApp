from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import FriendRequest, FriendList

from django.contrib.auth import get_user_model
Account = get_user_model()

# Create your views here.


@login_required(login_url='login')
def friend_list_view(request, user_id):
    context = {}
    user = request.user
    try:
        this_user = Account.objects.get(pk=user_id)
        context['this_user'] = this_user
    except Account.DoesNotExist as e:
        return HttpResponse("That user does not exist.")
    try:
        friend_list = FriendList.objects.get(user=this_user)
    except FriendList.DoesNotExist:
        return HttpResponse(f"YCould not fin a friend list for {this_user}")

    # Must be friends to view a friend list
    if user != this_user:
        if not user in friend_list.friends.all():
            messages.info(request,"You must be friend to view this friend list.")
            return redirect('profile', user_id)

    friends = []  # [(Account1, True).....]
    auth_user_friend_list = FriendList.objects.get(user=user)
    for friend in friend_list.friends.all():
        friends.append(
            (friend, auth_user_friend_list.is_mutual_friend(friend)))
    context['friends'] = friends

    return render(request, "friend/friend_list.html", context)


@login_required(login_url='login')
def friend_requests_view(request, user_id):
    context = {}
    user = request.user
    account = Account.objects.get(pk=user_id)
    if account == user:
        friend_requests = FriendRequest.objects.filter(
            receiver=account, is_active=True)
        context['friend_requests'] = friend_requests
    else:
        return HttpResponse("You can't view another users friend requests.")
    return render(request, "friend/friend_requests.html", context)


@login_required(login_url='users:login')
def send_friend_request_view(request):
    user = request.user
    payload = {}
    if request.method == "POST":
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
                # Get any friend requests(active and not-active)
                friend_requests = FriendRequest.objects.filter(
                    sender=user, receiver=receiver)
                # find if any of them are active
                try:
                    for request in friend_requests:
                        if request.is_active:
                            raise Exception(
                                "You have already sent them a friend request.")
                    # if none are active, then create a new friend request
                    friend_request = FriendRequest(
                        sender=user, receiver=receiver)
                    friend_request.save()
                    # payload['result'] = "success"
                    payload['response'] = "Friend request sent."
                except Exception as e:
                    # payload['result'] = 'error'
                    payload['response'] = str(e)
            # if the FriendRequest object doesn't exist.
            except FriendRequest.DoesNotExist:
                # There are no friend requests create one
                friend_request = FriendRequest(sender=user, receiver=receiver)
                friend_request.save()
                payload['response'] = "Friend request sent."

            if payload['response'] == None:
                payload['response'] = "Something went wrong."
        else:
            payload['response'] = "Unable to send a friend request"
    else:
        payload['response'] = " You must be authenticated to send a friend request.!"
    # return HttpResponse(json.dumps(payload), content_type="application/json")
    return JsonResponse(payload)


@login_required(login_url='users:login')
def accept_friend_request(request, friend_request_id):
    user = request.user
    payload = {}
    if request.method == "GET":
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            # Confirm that is the correct request
            if friend_request.receiver == user:
                if friend_request:
                    # found the request.now accept it
                    friend_request.accept()
                    payload['response'] = "Friend request accepted."
            else:
                payload['response'] = "Something went wrong."
        else:
            payload['response'] = "That is not your request to accept."
    else:
        payload['response'] = "Unable to accept that friend request."
    return JsonResponse(payload)


@login_required(login_url='users:login')
def remove_friend(request):
    user = request.user
    payload = {}
    if request.method == "POST":
        user_id = request.POST["receiver_user_id"]
        if user_id:
            try:
                removee = Account.objects.get(pk=user_id)
                friend_list = FriendList.objects.get(user=user)
                friend_list.unfriend(removee)
                payload['response'] = "Successfully removed that friend."
            except Exception as e:
                payload["response"] = f"Something went wrong: {str(e)}"
        else:
            payload["response"] = "There was an error. Unable to remove that friend."

    return JsonResponse(payload)


@login_required(login_url='users:login')
def decline_friend_request(request, friend_request_id):
    user = request.user
    payload = {}
    if request.method == "GET":
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            # Confirm that it is the correct request
            if friend_request.receiver == user:
                if friend_request:
                    friend_request.decline()
                    payload['response'] = "Friend request decline."
                else:
                    payload["response"] = "Something went wrong"
            else:
                payload['response'] = "That is not your friend request to decline."
        else:
            payload['response'] = "Unable to decline that friend request."
    return JsonResponse(payload)


@login_required(login_url='users:login')
def cancel_friend_request(request):
    user = request.user
    payload = {}

    if request.method == "POST":
        user_id = request.POST["receiver_user_id"]
        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
                friend_requests = FriendRequest.objects.filter(
                    sender=user, receiver=receiver, is_active=True)
            except Exception as e:
                payload['response'] = "Nothing to cancel. Friend request does not exist."

            # There should only ever be a single active friend request at any given time. Cancel them all just in case
            if len(friend_requests) > 1:
                for request in friend_requests:
                    request.cancel()
                payload["response"] = "Friend request cancelled."
            else:
                # Found the request. Now cancel it.
                friend_requests.first().cancel()
                payload["response"] = "Friend request cancelled."
        else:
            payload["response"] = "Unable to cancel that friend request."
    return JsonResponse(payload)
