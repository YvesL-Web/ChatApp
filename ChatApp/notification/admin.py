from django.contrib import admin
from .models import Notification

# Register your models here.

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['target', 'content_type','timestamp']
    list_filter = ['content_type']
    search_fields = ['target__username','target__email']
    