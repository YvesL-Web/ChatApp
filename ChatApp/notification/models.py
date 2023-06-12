from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
# Create your models here.


Account = get_user_model()
class Notification(models.Model):

    # who the notifications is sent to.
    target = models.ForeignKey(Account, on_delete= models.CASCADE)

    # the user that the creation of the notification was triggered by
    from_user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name="from_user")

    # statement describing the notification (ex:Chris sent you a friend request.)
    verb = models.CharField(max_length=255, unique=False, blank=True, null=True)

    redirect_url = models.URLField(max_length=500, null=True, unique=False, blank=True, help_text="The URL to redirect to when clicked.")
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False) 

    # Below the mandatory fields for generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return self.verb
    
    def get_content_object_type(self):
        return str(self.content_object.get_cname)