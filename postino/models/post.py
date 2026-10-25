import io
import logging
import os
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .category import Category
from .tag import Tag

logger = logging.getLogger(__name__)


class PostQuerySet(models.QuerySet):
    def indexable(self):
        """Return only posts that should be indexed by search engines.

        Respects POSTINO_NOINDEX_AFTER_DAYS (global) and
        Category.noindex_after_days (per-category override).
        When the setting is unset, all published posts are returned unchanged.
        Cutoffs are computed in Python to stay compatible with SQLite.
        """
        days = getattr(settings, 'POSTINO_NOINDEX_AFTER_DAYS', None)
        if days is None:
            return self

        from django.db.models import Q

        now = timezone.now()
        # Posts with no category override use the global cutoff.
        fresh = Q(
            category__noindex_after_days__isnull=True,
            published_date__gte=now - timedelta(days=days),
        )
        # Per-category overrides: one Q per distinct override value.
        overrides = (
            Category.objects
            .exclude(noindex_after_days__isnull=True)
            .values_list('noindex_after_days', flat=True)
            .distinct()
        )
        for d in overrides:
            fresh |= Q(
                category__noindex_after_days=d,
                published_date__gte=now - timedelta(days=d),
            )
        return self.filter(Q(keep_indexed=True) | fresh)


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
        max_length=255,
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
    keep_indexed = models.BooleanField(
        default=False,
        verbose_name=_("Keep indexed"),
        help_text=_("Always keep this post indexed, even if it exceeds the noindex age threshold."),
    )
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

    objects = PostQuerySet.as_manager()

    class Meta:
        verbose_name = _("Blog Post")
        verbose_name_plural = _("Blog Posts")
        ordering = ['-published_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_date']),
            models.Index(fields=['slug']),
            models.Index(fields=['category']),
        ]

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._original_image = (
            instance.featured_image.name
            if 'featured_image' in field_names and instance.featured_image
            else None
        )
        return instance

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_slug()

        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()

        if not self.meta_title:
            self.meta_title = self.title

        if not self.meta_description:
            self.meta_description = self.excerpt[:200]

        super().save(*args, **kwargs)

        result = self._process_featured_image()
        if result:
            old_name, new_name = result
            field = self._meta.get_field('featured_image')
            try:
                type(self).objects.filter(pk=self.pk).update(featured_image=new_name)
            except Exception:
                logger.exception(
                    'postino: DB update for featured_image failed for post %s', self.pk
                )
                try:
                    field.storage.delete(new_name)
                except Exception:
                    pass
                self.featured_image.name = old_name
            else:
                if old_name != new_name:
                    try:
                        field.storage.delete(old_name)
                    except Exception:
                        logger.exception(
                            'postino: could not delete original image %s', old_name
                        )

        self._original_image = self.featured_image.name if self.featured_image else None

    def _generate_slug(self):
        """Build an auto-slug from the title, respecting POSTINO_SLUG_* settings."""
        base = slugify(self.title)

        stopwords = getattr(settings, 'POSTINO_SLUG_STOPWORDS', None)
        if stopwords and base:
            parts = [w for w in base.split('-') if w not in stopwords]
            if parts:
                base = '-'.join(parts)

        slug = base or slugify(self.title)

        max_len = getattr(settings, 'POSTINO_SLUG_MAX_LENGTH', None)
        if max_len is None:
            max_len = self._meta.get_field('slug').max_length
        if len(slug) > max_len:
            # Only split on a word boundary if the cut doesn't already land on one.
            if slug[max_len] == '-':
                slug = slug[:max_len]
            else:
                slug = slug[:max_len].rsplit('-', 1)[0]

        return slug or slugify(self.title)

    def _process_featured_image(self):
        """Crop and convert featured_image on upload. Controlled by POSTINO_FEATURED_IMAGE_* settings.

        Returns (old_name, new_name) on success so the caller can update the DB
        row first, then delete old_name only after the update commits.
        Returns False when no processing is needed or on error.
        """
        size = getattr(settings, 'POSTINO_FEATURED_IMAGE_SIZE', (1200, 630))
        if size is None:
            return False

        if not self.featured_image:
            return False
        original_image = getattr(self, '_original_image', None)
        if self.featured_image.name == original_image:
            return False

        fmt = getattr(settings, 'POSTINO_FEATURED_IMAGE_FORMAT', 'WEBP').upper()
        quality = getattr(settings, 'POSTINO_FEATURED_IMAGE_QUALITY', 85)
        ext = '.jpg' if fmt == 'JPEG' else f'.{fmt.lower()}'

        from PIL import Image
        from django.core.files.base import ContentFile

        target_w, target_h = size

        try:
            self.featured_image.open('rb')
            with Image.open(self.featured_image) as img:
                img = img.convert('RGB')
                src_w, src_h = img.size
                target_ratio = target_w / target_h
                src_ratio = src_w / src_h

                if src_ratio > target_ratio:
                    new_w = int(src_h * target_ratio)
                    left = (src_w - new_w) // 2
                    img = img.crop((left, 0, left + new_w, src_h))
                else:
                    new_h = int(src_w / target_ratio)
                    top = (src_h - new_h) // 2
                    img = img.crop((0, top, src_w, top + new_h))

                img = img.resize((target_w, target_h), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format=fmt, quality=quality)
                buf.seek(0)
        except Exception:
            logger.exception('postino: featured image processing failed for post %s', self.pk)
            return False
        finally:
            self.featured_image.close()

        old_name = self.featured_image.name
        directory = os.path.dirname(old_name)
        stem = f"{directory}/{self.slug}" if directory else self.slug
        field = self._meta.get_field('featured_image')
        try:
            new_name = field.storage.save(
                f"{stem}{ext}", ContentFile(buf.read()), max_length=field.max_length
            )
        except Exception:
            logger.exception('postino: could not save processed image for post %s', self.pk)
            return False

        self.featured_image.name = new_name
        return old_name, new_name

    def get_absolute_url(self):
        return reverse('postino:blog_post_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    @property
    def is_published(self):
        return self.status == 'published' and self.published_date <= timezone.now()

    @property
    def is_noindexed(self):
        """True when the post should carry a noindex directive.

        Checks POSTINO_NOINDEX_AFTER_DAYS (global) and the category's own
        noindex_after_days override. keep_indexed=True always wins.
        """
        if self.keep_indexed:
            return False
        days = getattr(settings, 'POSTINO_NOINDEX_AFTER_DAYS', None)
        if days is None:
            return False
        if self.category_id:
            cat_days = getattr(self.category, 'noindex_after_days', None)
            if cat_days is not None:
                days = cat_days
        if not self.published_date:
            return False
        return timezone.now() - self.published_date > timedelta(days=days)

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
