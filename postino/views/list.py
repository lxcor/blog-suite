from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import ListView

from ..models import Category, Post, Tag


def _has_digest_relation():
    """True only for host projects that also install a `digest` app whose
    DigestArticle model points a FK at Post with related_name='digest_articles'
    (e.g. agrogato-web's news bulletin). Most postino consumers don't have
    this app at all, so every usage below must be optional, not assumed."""
    try:
        Post._meta.get_field('digest_articles')
        return True
    except FieldDoesNotExist:
        return False


class BlogListView(ListView):
    model = Post
    template_name = 'postino/blog.html'
    context_object_name = 'posts'
    paginate_by = 6

    def _active_language(self):
        return getattr(self.request, 'LANGUAGE_CODE', 'en')

    def get_queryset(self):
        lang = self._active_language()
        has_digest = _has_digest_relation()
        prefetch = ('tags', 'digest_articles') if has_digest else ('tags',)
        queryset = Post.objects.filter(
            status='published', language=lang,
        ).select_related('category', 'author').prefetch_related(*prefetch).order_by('-published_date')

        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)

        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags=tag)

        author_slug = self.kwargs.get('author_slug')
        if author_slug:
            user = get_object_or_404(get_user_model(), username=author_slug)
            queryset = queryset.filter(author=user)

        feed = self.request.GET.get('feed', '').strip()
        if feed and has_digest:
            queryset = queryset.filter(digest_articles__source_feed=feed).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self._active_language()
        lang_filter = Q(posts__status='published', posts__language=lang)

        featured_post = Post.objects.filter(
            status='published', is_featured=True, language=lang,
        ).select_related('category', 'author').first()

        categories = Category.objects.filter(is_active=True).annotate(
            post_count=Count('posts', filter=lang_filter)
        ).filter(post_count__gt=0).order_by('name')

        thirty_days_ago = timezone.now() - timedelta(days=30)

        popular_posts = Post.objects.filter(
            status='published', language=lang, published_date__gte=thirty_days_ago
        ).order_by('-views')[:5]

        tags = Tag.objects.annotate(
            post_count=Count('posts', filter=lang_filter)
        ).filter(post_count__gt=0).order_by('name')

        recent_posts = Post.objects.filter(
            status='published', language=lang,
        ).select_related('category', 'author').order_by('-published_date')[:5]

        feed_pills = []
        if _has_digest_relation():
            _FEED_DISPLAY = [
                ('soja', 'Soja'), ('milho', 'Milho'), ('cafe', 'Café'),
                ('boi', 'Boi Gordo'), ('graos', 'Grãos'), ('leite', 'Leite'),
                ('algodao', 'Algodão'), ('trigo', 'Trigo'),
                ('hortifruti', 'Hortifruti'), ('agronegocio', 'Agronegócio'),
                ('meio-ambiente', 'Meio Ambiente'), ('outros', 'Outros'),
            ]
            feed_counts_qs = (
                Post.objects.filter(status='published', language=lang)
                .values('digest_articles__source_feed')
                .annotate(n=Count('id', distinct=True))
                .filter(digest_articles__source_feed__isnull=False)
                .exclude(digest_articles__source_feed='')
            )
            feed_counts = {
                row['digest_articles__source_feed']: row['n']
                for row in feed_counts_qs
            }
            feed_pills = [
                (key, label, feed_counts[key])
                for key, label in _FEED_DISPLAY
                if key in feed_counts
            ]

        context.update({
            'featured_post': featured_post,
            'categories': categories,
            'popular_posts': popular_posts,
            'tags': tags,
            'recent_posts': recent_posts,
            'total_posts': Post.objects.filter(status='published', language=lang).count(),
            'current_category': self.kwargs.get('category_slug'),
            'current_tag': self.kwargs.get('tag_slug'),
            'current_feed': self.request.GET.get('feed', '').strip(),
            'feed_pills': feed_pills,
            'per_page_options': [6, 12, 24, 48],
            'default_per_page': 12,
        })

        return context
