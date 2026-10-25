from unittest.mock import patch

from postino.models.post import PostQuerySet

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from postino.models import Category, Post

User = get_user_model()


def _webp_bytes():
    from PIL import Image
    import io
    img = Image.new('RGB', (1200, 630), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, 'WEBP')
    return buf.getvalue()


class ImageFilenameTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('imgtest', password='x')
        cls.cat = Category.objects.create(name='ImgCat', slug='img-cat')

    def _post(self, slug):
        return Post.objects.create(
            title=slug, slug=slug, excerpt='e', content='c',
            author=self.user, category=self.cat, status='draft',
        )

    def test_long_slug_fits_within_max_length(self):
        """A 150-char slug must produce a stored filename <= max_length=255."""
        long_slug = 'a' * 75 + '-' + 'b' * 74  # 150 chars
        p = self._post(long_slug)
        p.featured_image.save('source.jpg', ContentFile(_webp_bytes()), save=True)
        p.refresh_from_db()

        max_length = Post._meta.get_field('featured_image').max_length
        self.assertLessEqual(len(p.featured_image.name), max_length)
        self.assertTrue(p.featured_image.storage.exists(p.featured_image.name))
        # original upload is gone
        self.assertFalse(p.featured_image.storage.exists('blog/featured/' + 'source.jpg'))

    def test_collision_suffix_still_fits(self):
        """Two posts with the same long slug on the same day both fit."""
        long_slug = 'c' * 75 + '-' + 'd' * 74
        p1 = self._post(long_slug + '-p1')
        p2 = self._post(long_slug + '-p2')
        for p in (p1, p2):
            p.featured_image.save('source.jpg', ContentFile(_webp_bytes()), save=True)
            p.refresh_from_db()

        max_length = Post._meta.get_field('featured_image').max_length
        for p in (p1, p2):
            self.assertLessEqual(len(p.featured_image.name), max_length)
            self.assertTrue(p.featured_image.storage.exists(p.featured_image.name))

    def test_db_failure_no_orphan_and_db_consistent(self):
        """If the post-processing DB update raises, the processed file must be
        cleaned up (no orphan) and the DB row must still reference a file that
        actually exists on disk."""
        p = self._post('db-failure-test')
        p.featured_image.save('original.jpg', ContentFile(_webp_bytes()), save=True)
        p.refresh_from_db()

        storage = p.featured_image.storage

        # Track all webp files present before the failing save
        import os
        media_dir = os.path.join(storage.location, 'blog/featured')
        def _webps():
            result = set()
            for root, _, files in os.walk(media_dir):
                for f in files:
                    if f.endswith('.webp'):
                        result.add(os.path.join(root, f))
            return result

        before = _webps()

        # Upload a new image; patch the queryset .update() to simulate a DB error
        with patch.object(
            PostQuerySet, 'update',
            side_effect=Exception('simulated DB failure'),
        ):
            p.featured_image.save('new-upload.jpg', ContentFile(_webp_bytes()), save=True)

        after = _webps()

        p.refresh_from_db()
        # No new orphaned webp was left behind
        self.assertEqual(after, before, 'Orphaned webp file(s) left after DB failure')
        # DB row still references a file that exists
        self.assertTrue(
            storage.exists(p.featured_image.name),
            f'DB points to missing file: {p.featured_image.name}',
        )


class SlugGenerationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('slugtest', password='x')
        cls.cat = Category.objects.create(name='SlugCat', slug='slug-cat')

    def _create(self, title, slug='', **extra):
        return Post.objects.create(
            title=title, slug=slug, excerpt='e', content='c',
            author=self.user, category=self.cat, status='draft', **extra
        )

    @override_settings(POSTINO_SLUG_STOPWORDS=None, POSTINO_SLUG_MAX_LENGTH=None)
    def test_default_slug_unchanged(self):
        """Without settings, slugify(title) is used as-is."""
        from django.utils.text import slugify
        p = self._create('How the Dome Works for a Platform')
        self.assertEqual(p.slug, slugify('How the Dome Works for a Platform'))

    @override_settings(
        POSTINO_SLUG_STOPWORDS={'a', 'an', 'the', 'of', 'for', 'and', 'to', 'in', 'on'},
        POSTINO_SLUG_MAX_LENGTH=None,
    )
    def test_stopwords_removed(self):
        p = self._create('How the Dome Works for a Platform')
        self.assertEqual(p.slug, 'how-dome-works-platform')

    @override_settings(
        POSTINO_SLUG_STOPWORDS=None,
        POSTINO_SLUG_MAX_LENGTH=10,
    )
    def test_max_length_cuts_at_word_boundary(self):
        p = self._create('hello world foo bar')
        # slugify -> 'hello-world-foo-bar', cut at 10 -> 'hello-worl' -> rsplit -> 'hello'
        self.assertLessEqual(len(p.slug), 10)
        self.assertFalse(p.slug.endswith('-'))

    @override_settings(
        POSTINO_SLUG_STOPWORDS={'a', 'an', 'the'},
        POSTINO_SLUG_MAX_LENGTH=None,
    )
    def test_existing_slug_not_rewritten(self):
        """Re-saving a post with an existing slug must not change it."""
        p = self._create('The Big Article', slug='my-custom-slug')
        original = p.slug
        p.title = 'The Big Article Updated'
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.slug, original)
