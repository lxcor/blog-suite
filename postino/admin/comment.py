from django.contrib import admin

from ..models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'post', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('author_name', 'content', 'post__title')
    actions = ['approve_comments']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post')

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} comentários aprovados.")
    approve_comments.short_description = "Aprovar comentários selecionados"
