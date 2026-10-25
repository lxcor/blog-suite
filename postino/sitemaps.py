from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Post, Tag


class ImageSitemap(Sitemap):
    changefreq = 'weekly'

    def get_queryset(self):
        """Override to filter which posts appear in the image sitemap."""
        return Post.objects.filter(status='published')

    def items(self):
        return (
            self.get_queryset()
            .indexable()
            .exclude(featured_image='')
            .filter(featured_image__isnull=False)
            .order_by('-published_date')
        )

    def lastmod(self, obj):
        return obj.updated_at

    def get_urls(self, page=1, site=None, protocol=None):
        urls = super().get_urls(page=page, site=site, protocol=protocol)
        protocol_ = self.get_protocol(protocol)
        domain = self.get_domain(site)
        for url_info in urls:
            post = url_info['item']
            image_url = post.featured_image.url
            if image_url.startswith(('http://', 'https://')):
                loc = image_url
            else:
                loc = f'{protocol_}://{domain}{image_url}'
            url_info['images'] = [{'loc': loc}]
        return urls


class PostSitemap(Sitemap):
    changefreq = 'weekly'

    def items(self):
        return (
            Post.objects.filter(status='published')
            .indexable()
            .order_by('-published_date')
        )

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
