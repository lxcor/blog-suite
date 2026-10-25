from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from postino.models import Category, Post

User = get_user_model()


def _days_ago(n):
    return timezone.now() - timedelta(days=n)


class NoindexTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('tester', password='x')
        cls.cat = Category.objects.create(name='Test', slug='test-cat')
        cls.cat_override = Category.objects.create(
            name='Override', slug='override-cat', noindex_after_days=1000
        )

    def _post(self, slug, days_old, category=None, keep_indexed=False, status='published'):
        p = Post.objects.create(
            title=slug, slug=slug, excerpt='e', content='c',
            author=self.user, category=category or self.cat,
            status=status, keep_indexed=keep_indexed,
        )
        # bypass save() auto-set of published_date
        Post.objects.filter(pk=p.pk).update(published_date=_days_ago(days_old))
        p.refresh_from_db()
        return p

    # ------------------------------------------------------------------ #
    # Setting unset
    # ------------------------------------------------------------------ #

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=None)
    def test_setting_unset_indexable_returns_all(self):
        p = self._post('unset-1', days_old=999)
        self.assertIn(p, Post.objects.filter(pk=p.pk).indexable())

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=None)
    def test_setting_unset_no_header(self):
        p = self._post('unset-2', days_old=999)
        response = Client().get(p.get_absolute_url())
        self.assertIsNone(response.get('X-Robots-Tag'))

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=None)
    def test_setting_unset_is_noindexed_false(self):
        p = self._post('unset-3', days_old=999)
        self.assertFalse(p.is_noindexed)

    # ------------------------------------------------------------------ #
    # N=60 basic cases
    # ------------------------------------------------------------------ #

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=60)
    def test_61_day_post_excluded_from_indexable(self):
        p = self._post('old-61', days_old=61)
        self.assertNotIn(p, Post.objects.filter(pk=p.pk).indexable())

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=60)
    def test_61_day_post_is_noindexed(self):
        p = self._post('old-61b', days_old=61)
        self.assertTrue(p.is_noindexed)

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=60)
    def test_59_day_post_in_indexable(self):
        p = self._post('young-59', days_old=59)
        self.assertIn(p, Post.objects.filter(pk=p.pk).indexable())

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=60)
    def test_59_day_post_not_noindexed(self):
        p = self._post('young-59b', days_old=59)
        self.assertFalse(p.is_noindexed)

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=60)
    def test_60_5_day_post_consistent(self):
        """is_noindexed and indexable() must agree on a fractional-day-old post."""
        p = Post.objects.create(
            title='half-day', slug='half-day', excerpt='e', content='c',
            author=self.user, category=self.cat, status='published',
        )
        Post.objects.filter(pk=p.pk).update(
            published_date=timezone.now() - timedelta(days=60, hours=12)
        )
        p.refresh_from_db()
        in_indexable = Post.objects.filter(pk=p.pk).indexable().exists()
        self.assertEqual(not in_indexable, p.is_noindexed,
                         'is_noindexed and indexable() disagree on 60.5-day post')

    # ------------------------------------------------------------------ #
    # keep_indexed escape hatch
    # ------------------------------------------------------------------ #

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=60)
    def test_keep_indexed_overrides_age(self):
        p = self._post('keep-old', days_old=365, keep_indexed=True)
        self.assertFalse(p.is_noindexed)
        self.assertIn(p, Post.objects.filter(pk=p.pk).indexable())

    # ------------------------------------------------------------------ #
    # Category override
    # ------------------------------------------------------------------ #

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=60)
    def test_category_override_wins(self):
        """Category.noindex_after_days=1000 keeps a 365-day post indexed."""
        p = self._post('cat-old', days_old=365, category=self.cat_override)
        self.assertFalse(p.is_noindexed)
        self.assertIn(p, Post.objects.filter(pk=p.pk).indexable())

    # ------------------------------------------------------------------ #
    # X-Robots-Tag response header
    # ------------------------------------------------------------------ #

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=60)
    def test_noindexed_post_has_header(self):
        p = self._post('header-old', days_old=61)
        response = Client().get(p.get_absolute_url())
        self.assertEqual(response.get('X-Robots-Tag'), 'noindex, follow')

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=60)
    def test_indexed_post_has_no_header(self):
        p = self._post('header-young', days_old=59)
        response = Client().get(p.get_absolute_url())
        self.assertIsNone(response.get('X-Robots-Tag'))

    # ------------------------------------------------------------------ #
    # Sitemap returns 200 with setting on (SQLite compatibility check)
    # ------------------------------------------------------------------ #

    @override_settings(POSTINO_NOINDEX_AFTER_DAYS=60)
    def test_sitemap_returns_200_with_setting_on(self):
        response = Client().get('/blog/sitemap.xml')
        self.assertEqual(response.status_code, 200)
