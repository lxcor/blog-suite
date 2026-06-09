from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render

from ..models import Post


def blog_search(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        search_vector = (
            SearchVector('title', weight='A') +
            SearchVector('excerpt', weight='B') +
            SearchVector('content', weight='C')
        )
        search_query = SearchQuery(query)

        results = Post.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(
            status='published', search=search_query
        ).order_by('-rank', '-published_date')

    paginator = Paginator(results, 6)
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, 'postino/blog_search.html', {
        'posts': posts,
        'query': query,
        'total_results': len(results),
        'pagination_options': [6, 12, 24],
        'default_per_page': 6,
    })
