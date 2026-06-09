from django.contrib import admin

from ..models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'status', 'is_featured', 'published_date', 'views', 'reading_time')
    list_filter = ('status', 'category', 'is_featured', 'published_date')
    search_fields = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    readonly_fields = ('views', 'created_at', 'updated_at')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'featured_image')
        }),
        ('Classificação', {
            'fields': ('category', 'tags', 'is_featured', 'status')
        }),
        ('Autor e Datas', {
            'fields': ('author', 'reading_time', 'published_date')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Estatísticas', {
            'fields': ('views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'author')

    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)
