from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Author(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='postino_author',
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='blog/authors/', blank=True, null=True)
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = _("Blog Author Profile")
        verbose_name_plural = _("Blog Author Profiles")

    def __str__(self):
        return f"Blog author: {self.user}"
