from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Tag Name"))
    slug = models.SlugField(max_length=50, unique=True, verbose_name=_("Slug"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Blog Tag")
        verbose_name_plural = _("Blog Tags")
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('postino:blog_tag', kwargs={'slug': self.slug})
