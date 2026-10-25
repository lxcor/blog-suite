from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Post, Tag


class ImageSitemap(Sitemap):
    changefreq = 'weekly'
    template_name = 'postino/sitemap_images.xml'

    def items(self):
        return (
            Post.objects.filter(status='published')
            .exclude(featured_image='')
            .filter(featured_image__isnull=False)
            .order_by('-published_date')
        )

    def lastmod(self, obj):
        return obj.updated_at

    def _urls(self, page, protocol, domain):
        urls = super()._urls(page, protocol, domain)
        for url_info in urls:
            post = url_info['item']
            url_info['images'] = [{
                'loc': f'{protocol}://{domain}{post.featured_image.url}',
                'title': post.title,
                'caption': post.excerpt,
            }]
        return urls


class PostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Post.objects.filter(status='published').order_by('-published_date')

    def lastmod(self, obj):
        return obj.updated_at

    def priority(self, obj):
        return 0.9 if obj.is_featured else 0.8


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('postino:blog_category', kwargs={'category_slug': obj.slug})


class TagSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.4

    def items(self):
        return Tag.objects.filter(posts__status='published').distinct()

    def location(self, obj):
        return reverse('postino:blog_tag', kwargs={'tag_slug': obj.slug})


class BlogStaticSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    def items(self):
        return ['postino:blog']

    def location(self, item):
        return reverse(item)
