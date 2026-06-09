from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome da Categoria")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    color = models.CharField(
        max_length=20,
        default='primary',
        verbose_name="Cor do Badge",
        help_text="Cor Bootstrap (primary, secondary, success, danger, warning, info)"
    )
    description = models.TextField(blank=True, verbose_name="Descrição")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoria do Blog"
        verbose_name_plural = "Categorias do Blog"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('postino:blog_category', kwargs={'slug': self.slug})
