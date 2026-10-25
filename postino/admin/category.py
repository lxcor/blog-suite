from django.contrib import admin

from ..models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color', 'is_active', 'noindex_after_days', 'post_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fields = ('name', 'slug', 'color', 'description', 'is_active', 'noindex_after_days')

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Post Count'
