from django.db import models


class Subscription(models.Model):
    email = models.EmailField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
