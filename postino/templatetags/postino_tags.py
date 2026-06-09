from datetime import timedelta

from django import template
from django.contrib.auth import get_user_model
from django.db.models import Count, Max, Q
from django.utils import timezone

from postino.models import Category, Comment, Post, Tag

register = template.Library()


# --- CATEGORY TAGS ---

@register.simple_tag
def get_categories_with_count():
    return Category.objects.filter(is_active=True).annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0).order_by('name')


@register.simple_tag
def total_posts_count():
    return Post.objects.filter(status='published').count()


@register.simple_tag
def get_recent_categories(limit=3):
    thirty_days_ago = timezone.now() - timedelta(days=30)
    return Category.objects.filter(
        is_active=True,
        posts__status='published',
        posts__published_date__gte=thirty_days_ago
    ).annotate(
        post_count=Count('posts', filter=Q(posts__status='published')),
        latest_post_date=Max('posts__published_date')
    ).filter(post_count__gt=0).order_by('-latest_post_date')[:limit]


# --- POST TAGS ---

@register.simple_tag
def get_popular_posts(count=5):
    thirty_days_ago = timezone.now() - timedelta(days=30)
    return Post.objects.filter(
        status='published',
        published_date__gte=thirty_days_ago
    ).order_by('-views')[:count]


@register.simple_tag
def get_recent_posts(count=5, exclude_post_id=None):
    queryset = Post.objects.filter(status='published').select_related('category', 'author')
    if exclude_post_id:
        queryset = queryset.exclude(id=exclude_post_id)
    return queryset.order_by('-published_date')[:count]


@register.simple_tag
def get_related_posts(post, count=3):
    if not post or not post.category:
        return Post.objects.none()

    related = Post.objects.filter(
        status='published', category=post.category
    ).exclude(id=post.id).select_related('category', 'author')

    if post.tags.exists():
        tag_ids = post.tags.values_list('id', flat=True)
        tagged_posts = Post.objects.filter(
            status='published', tags__id__in=tag_ids
        ).exclude(id=post.id).distinct()
        related = (tagged_posts | related).distinct()

    return related.order_by('-published_date')[:count]


# --- TAG TAGS ---

@register.simple_tag
def get_popular_tags(limit=10):
    return Tag.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0).order_by('-post_count')[:limit]


@register.simple_tag
def get_tag_cloud(min_font=0.8, max_font=1.5):
    tags = Tag.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0)

    if not tags:
        return []

    counts = [tag.post_count for tag in tags]
    min_count, max_count = min(counts), max(counts)

    tag_cloud = []
    for tag in tags:
        if max_count > min_count:
            size = min_font + (tag.post_count - min_count) * (max_font - min_font) / (max_count - min_count)
        else:
            size = (min_font + max_font) / 2
        tag_cloud.append({
            'tag': tag,
            'size': round(size, 2),
            'class': _tag_size_class(tag.post_count),
        })

    return tag_cloud


def _tag_size_class(count):
    if count > 10:
        return 'fs-5 fw-bold'
    elif count > 5:
        return 'fs-5'
    elif count > 2:
        return 'fs-6'
    return 'fs-7'


# --- FILTERS ---

@register.filter
def timesince_ptbr(value):
    if not value:
        return ""
    now = timezone.now()
    diff = now - value

    if diff.days == 0:
        if diff.seconds < 60:
            return "agora mesmo"
        elif diff.seconds < 3600:
            m = diff.seconds // 60
            return f"{m} minuto{'s' if m > 1 else ''} atrás"
        else:
            h = diff.seconds // 3600
            return f"{h} hora{'s' if h > 1 else ''} atrás"
    elif diff.days == 1:
        return "ontem"
    elif diff.days < 7:
        return f"{diff.days} dia{'s' if diff.days > 1 else ''} atrás"
    elif diff.days < 30:
        w = diff.days // 7
        return f"{w} semana{'s' if w > 1 else ''} atrás"
    elif diff.days < 365:
        mo = diff.days // 30
        return f"{mo} mês{'es' if mo > 1 else ''} atrás"
    else:
        y = diff.days // 365
        return f"{y} ano{'s' if y > 1 else ''} atrás"


@register.filter
def split(value, delimiter):
    if not value or not delimiter:
        return [value]
    return value.split(delimiter)


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def startswith(value, arg):
    return value.startswith(arg)


# --- STATISTICS ---

@register.simple_tag
def get_blog_stats():
    User = get_user_model()
    total_posts = Post.objects.filter(status='published').count()
    total_comments = Comment.objects.filter(is_approved=True).count()
    total_views = sum(Post.objects.filter(status='published').values_list('views', flat=True))

    active_author = User.objects.annotate(
        post_count=Count('postino_posts', filter=Q(postino_posts__status='published'))
    ).filter(post_count__gt=0).order_by('-post_count').first()

    return {
        'total_posts': total_posts,
        'total_comments': total_comments,
        'total_views': total_views,
        'active_author': active_author,
        'active_author_posts': active_author.post_count if active_author else 0,
    }


@register.simple_tag
def get_monthly_archive():
    from django.db.models.functions import TruncMonth
    return Post.objects.filter(status='published').annotate(
        month=TruncMonth('published_date')
    ).values('month').annotate(count=Count('id')).order_by('-month')[:12]


# --- UTILITY ---

@register.simple_tag(takes_context=True)
def pagination_query_string(context, **kwargs):
    request = context.get('request')
    if not request:
        return ''

    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value

    for key in list(params.keys()):
        if not params[key]:
            del params[key]

    return params.urlencode()
