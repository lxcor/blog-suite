from django.contrib import admin

from ..models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color', 'is_active', 'post_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Número de Posts'
