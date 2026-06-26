from django.contrib import admin

from ..models import Unsubscribe


@admin.register(Unsubscribe)
class UnsubscribeAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at']
    search_fields = ['email']
    readonly_fields = ['token', 'created_at']
