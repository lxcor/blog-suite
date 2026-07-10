from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import ListView

from ..models import Category, Post, Tag


class BlogListView(ListView):
    model = Post
    template_name = 'postino/blog.html'
    context_object_name = 'posts'
    paginate_by = 6

    def _active_language(self):
        return getattr(self.request, 'LANGUAGE_CODE', 'en')

    def get_queryset(self):
        lang = self._active_language()
        queryset = Post.objects.filter(
            status='published', language=lang,
        ).select_related('category', 'author').prefetch_related('tags').order_by('-published_date')

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

        context.update({
            'featured_post': featured_post,
            'categories': categories,
            'popular_posts': popular_posts,
            'tags': tags,
            'recent_posts': recent_posts,
            'total_posts': Post.objects.filter(status='published', language=lang).count(),
            'current_category': self.kwargs.get('category_slug'),
            'current_tag': self.kwargs.get('tag_slug'),
            'per_page_options': [6, 12, 24, 48],
            'default_per_page': 12,
        })

        return context
