from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .category import Category
from .tag import Tag


class Post(models.Model):
    POST_STATUS = (
        ('draft', 'Rascunho'),
        ('published', 'Publicado'),
        ('archived', 'Arquivado'),
    )

    title = models.CharField(max_length=200, verbose_name="Título")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
    excerpt = models.TextField(max_length=300, verbose_name="Resumo")
    content = models.TextField(verbose_name="Conteúdo")

    featured_image = models.ImageField(
        upload_to='blog/featured/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Imagem Destacada"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='postino_posts',
        verbose_name="Autor"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
        verbose_name="Categoria"
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='posts',
        verbose_name="Tags"
    )

    is_featured = models.BooleanField(default=False, verbose_name="Destacado")
    status = models.CharField(
        max_length=20,
        choices=POST_STATUS,
        default='draft',
        verbose_name="Status"
    )

    views = models.PositiveIntegerField(default=0, verbose_name="Visualizações")
    reading_time = models.PositiveIntegerField(
        default=5,
        verbose_name="Tempo de Leitura (minutos)"
    )

    meta_title = models.CharField(max_length=200, blank=True, verbose_name="Meta Título")
    meta_description = models.TextField(max_length=300, blank=True, verbose_name="Meta Descrição")

    published_date = models.DateTimeField(null=True, blank=True, verbose_name="Data de Publicação")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Post do Blog"
        verbose_name_plural = "Posts do Blog"
        ordering = ['-published_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_date']),
            models.Index(fields=['slug']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()

        if not self.meta_title:
            self.meta_title = self.title

        if not self.meta_description:
            self.meta_description = self.excerpt[:200]

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('postino:blog_post_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    @property
    def is_published(self):
        return self.status == 'published' and self.published_date <= timezone.now()

    @property
    def featured_image_url(self):
        if self.featured_image and hasattr(self.featured_image, 'url'):
            return self.featured_image.url
        return "https://via.assets.so/img.jpg?w=600&h=400&bg=495057&f=png"

    @property
    def author_image_url(self):
        try:
            profile = self.author.postino_author
            if profile.avatar:
                return profile.avatar.url
        except Exception:
            pass
        return "https://via.assets.so/img.jpg?w=40&h=40&bg=d1d5db&f=png"

    @property
    def formatted_published_date(self):
        if self.published_date:
            return self.published_date.strftime("%d %b %Y")
        return ""
