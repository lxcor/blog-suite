from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import BlogStaticSitemap, CategorySitemap, PostSitemap, TagSitemap

app_name = 'postino'

_sitemaps = {
    'posts': PostSitemap,
    'categories': CategorySitemap,
    'tags': TagSitemap,
    'static': BlogStaticSitemap,
}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': _sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('', views.BlogListView.as_view(), name='blog'),
    path('categoria/<slug:category_slug>/', views.BlogListView.as_view(), name='blog_category'),
    path('author/<slug:author_slug>/', views.BlogListView.as_view(), name='blog_author'),
    path('tag/<slug:tag_slug>/', views.BlogListView.as_view(), name='blog_tag'),
    path('buscar/', views.blog_search, name='blog_search'),
    path('assinar/', views.blog_subscribe, name='subscribe'),
    path('comentar/<int:post_id>/', views.blog_comment, name='comment'),
    path('<slug:slug>/', views.BlogPostDetailView.as_view(), name='blog_post_detail'),
]
