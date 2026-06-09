from django.urls import path

from . import views

app_name = 'postino'

urlpatterns = [
    path('', views.BlogListView.as_view(), name='blog'),
    path('categoria/<slug:category_slug>/', views.BlogListView.as_view(), name='blog_category'),
    path('author/<slug:author_slug>/', views.BlogListView.as_view(), name='blog_author'),
    path('tag/<slug:tag_slug>/', views.BlogListView.as_view(), name='blog_tag'),
    path('buscar/', views.blog_search, name='blog_search'),
    path('assinar/', views.blog_subscribe, name='subscribe'),
    path('comentar/<int:post_id>/', views.blog_comment, name='comment'),
    path('<slug:slug>/', views.BlogPostDetailView.as_view(), name='blog_post_detail'),
]
