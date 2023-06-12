from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core import files
from django.core.files.storage import default_storage, FileSystemStorage
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

import os
import cv2
import json
import base64
import requests

from friend.friend_request_status import FriendRequestStatus
from friend.utils import get_friend_request_or_false

from .models import Account
from .forms import RegistrationForm, LoginRegistrationForm, AccountUpdateForm
from friend.models import FriendList, FriendRequest

TEMP_PROFILE_IMAGE_NAME = "temp_profile_image.png"
# Create your views here.


def register_view(request, *args, **kwargs):
    user = request.user
    if user.is_authenticated:
        return redirect("home")

    context = {}

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Account Successfully created')
            form.save()
            return redirect('login')
        else:
            context["registration_form"] = form

    return render(request, "account/register.html", context)


def login_view(request, *args, **kwargs):
    context = {}
    user = request.user
    if user.is_authenticated:
        return redirect("home")

    if request.POST:
        form = LoginRegistrationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email, password=password)
            if user:
                login(request, user)
                return redirect("home")
            else:
                messages.warning(request, "email or password is incorrect")
                return redirect("users:login")
        else:
            context["login_form"] = form

    return render(request, "account/login.html", context)


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required(login_url='login')
def profile_view(request, user_id):

    context = {}
    try:
        account = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        return HttpResponse("That user doesn't exist.")
    if account:
        context['id'] = account.id
        context['username'] = account.username
        context['email'] = account.email
        context['profile_image'] = account.profile_image.url
        context['hide_email'] = account.hide_email

        try:
            friend_list = FriendList.objects.get(user=account)
        except FriendList.DoesNotExist:
            friend_list = FriendList(user=account)
            friend_list.save()
        friends = friend_list.friends.all()
        context["friends"] = friends

        # Define state template variables
        is_self = True
        is_friend = False
        request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
        friend_requests = None
        user = request.user
        if user.is_authenticated and user != account:
            is_self = False
            if friends.filter(pk=user.id):
                is_friend = True
            else:
                is_friend = False
                # Case1: request has been sent from them to you
                if get_friend_request_or_false(sender=account, receiver=user) != False:
                    request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
                    context['pending_friend_request_id'] = get_friend_request_or_false(
                        sender=account, receiver=user).id
                # Case2: request has been sent by you to them
                elif get_friend_request_or_false(sender=user, receiver=account) != False:
                    request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value
                else:
                    # Case3: No request has been sent
                    request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
        elif not user.is_authenticated:
            is_self = False
        else:
            try:
                friend_requests = FriendRequest.objects.filter(
                    receiver=user, is_active=True)
            except:
                pass

        context['is_self'] = is_self
        context['is_friend'] = is_friend
        context['request_sent'] = request_sent
        context['friend_requests'] = friend_requests

        return render(request, "account/profile.html", context)


def search_result(request, *args, **kwargs):
    context = {}
    if request.method == "GET":
        search_query = request.GET["q"]
        if len(search_query) > 0:
            # search_results = Account.objects.filter( username__icontains=search_query)
            search_results = Account.objects.filter(
                Q(email__icontains=search_query) | Q(username__icontains=search_query))
            user = request.user
            accounts = [] # [(account, True),(account2, False)....] the boolean help to know if you're friend
            if user.is_authenticated:
                #get the authenticated users friend list
                auth_user_friend_list = FriendList.objects.get(user=user)
                for account in search_results:
                    accounts.append((account, auth_user_friend_list.is_mutual_friend(account)))
                context['accounts'] = accounts
            else:
                for account in search_results:
                    accounts.append((account, False))
                context['accounts'] = accounts

            

    return render(request, "account/search_result.html", context)


@login_required(login_url='login')
def edit_profile_view(request, user_id):
    try:
        account = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        return HttpResponse("Something went wrong.")
    if account.pk != request.user.pk:
        return HttpResponse("You cannot edit someone else profile.")
    context = {}
    if request.method == 'POST':
        form = AccountUpdateForm(request.POST, request.FILES, instance=account)
        if form.is_valid():
            form.save()
            return redirect("profile", account.pk)
        else:
            form = AccountUpdateForm(
                request.POST,
                initial={
                    'id': account.pk,
                    "email": account.email,
                    "username": account.username,
                    "profile_image": account.profile_image,
                    "hide_email": account.hide_email
                }
            )
            context["form"] = form
    else:
        form = AccountUpdateForm(
            initial={
                'id': account.pk,
                "email": account.email,
                "username": account.username,
                "profile_image": account.profile_image,
                "hide_email": account.hide_email
            }
        )
        context["form"] = form

    context['DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    return render(request, "account/profile_update.html", context)


def save_temp_profile_image_from_base64String(imageString, user):
    INCORRECT_PADDING_EXCEPTION = "Incorrect padding"
    try:
        if not os.path.exists(settings.TEMP):
            os.mkdir(settings.TEMP)
        if not os.path.exists(f"{settings.TEMP}/{user.username}"):
            os.mkdir(f"{settings.TEMP}/{user.username}")
        url = os.path.join(
            f"{settings.TEMP}/{user.username}", TEMP_PROFILE_IMAGE_NAME)
        storage = FileSystemStorage(location=url)
        image = base64.b64decode(imageString)
        with storage.open('', 'wb+') as destination:
            destination.write(image)
            destination.close()
        return url
    except Exception as e:
        if str(e) == INCORRECT_PADDING_EXCEPTION:
            imageString += "=" * ((4 - len(imageString) % 4) % 4)
            return save_temp_profile_image_from_base64String(imageString, user)
    return None


@login_required(login_url='login')
def crop_image(request, *args, **kwargs):
    payload = {}
    user = request.user
    if request.method == "POST":
        try:
            imageString = request.POST["image"]
            url = save_temp_profile_image_from_base64String(imageString, user)
            img = cv2.imread(url)

            cropX = int(float(str(request.POST["cropX"])))
            cropY = int(float(str(request.POST["cropY"])))
            cropWidth = int(float(str(request.POST["cropWidth"])))
            cropHeight = int(float(str(request.POST["cropHeight"])))

            if cropX < 0:
                cropX = 0
            if cropY < 0:
                cropY = 0

            crop_img = img[cropY:cropY+cropHeight, cropX:cropX+cropWidth]
            cv2.imwrite(url, crop_img)
            user.profile_image.delete()
            user.profile_image.save(
                "profile_image.png", files.File(open(url, "rb")))
            user.save()

            payload['result'] = "success"
            payload["cropped_profile_image"] = user.profile_image.url

            os.remove(url)

        except Exception as e:
            payload['result'] = 'error'
            payload['exception'] = str(e)

    return JsonResponse(payload)
