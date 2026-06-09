from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nome da Tag")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Slug")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tag do Blog"
        verbose_name_plural = "Tags do Blog"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('postino:blog_tag', kwargs={'slug': self.slug})
