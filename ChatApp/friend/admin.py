from django.contrib import admin

from .models import FriendList, FriendRequest

# Register your models here.

@admin.register(FriendList)
class FriendListAdmin(admin.ModelAdmin):
    list_filter = ['user']
    list_display = ['user']
    search_fields = ['user']
    readonly_fields = ['user']

@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_filter = ['sender','receiver']
    list_display = ['sender','receiver']
    search_fields = ['sender__username','sender__email','receiver__username','receiver__email' ]