from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .category import Category
from .tag import Tag


class Post(models.Model):
    POST_STATUS = (
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('archived', _('Archived')),
    )

    title = models.CharField(max_length=200, verbose_name=_("Title"))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_("Slug"))
    excerpt = models.TextField(max_length=300, verbose_name=_("Summary"))
    content = models.TextField(verbose_name=_("Content"))

    featured_image = models.ImageField(
        upload_to='blog/featured/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name=_("Featured Image")
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='postino_posts',
        verbose_name=_("Author")
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
        verbose_name=_("Category")
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='posts',
        verbose_name=_("Tags")
    )

    is_featured = models.BooleanField(default=False, verbose_name=_("Featured"))
    status = models.CharField(
        max_length=20,
        choices=POST_STATUS,
        default='draft',
        verbose_name=_("Status")
    )

    views = models.PositiveIntegerField(default=0, verbose_name=_("Views"))
    reading_time = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Reading Time (minutes)")
    )

    meta_title = models.CharField(max_length=200, blank=True, verbose_name=_("Meta Title"))
    meta_description = models.TextField(max_length=300, blank=True, verbose_name=_("Meta Description"))

    language = models.CharField(
        max_length=10,
        default='en',
        verbose_name=_("Language"),
        help_text=_("BCP 47 language code of this post's content, e.g. en, pt-br, fr"),
    )
    translated_from = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='translations',
        verbose_name=_("Translated from"),
    )

    published_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Publication Date"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Blog Post")
        verbose_name_plural = _("Blog Posts")
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
