from django.contrib import admin

from ..models import Author


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('user', 'website', 'twitter')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
