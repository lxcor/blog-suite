from django.contrib import admin

from postino.models import ContentGapOpportunity


@admin.register(ContentGapOpportunity)
class ContentGapOpportunityAdmin(admin.ModelAdmin):
    list_display = [
        'keyword', 'volume', 'competition', 'status',
        'suggested_title', 'source_report', 'created_at',
    ]
    list_filter = ['status', 'competition', 'source_report']
    search_fields = ['keyword', 'suggested_title', 'seed_keyword']
    readonly_fields = ['created_at', 'updated_at', 'post']
    ordering = ['-volume']
    list_per_page = 50

    fieldsets = [
        ('Keyword Data', {
            'fields': ['keyword', 'volume', 'competition', 'cpc_low', 'cpc_high',
                       'seed_keyword', 'suggested_slug', 'content_angle', 'source_report'],
        }),
        ('LLM Suggestions', {
            'fields': ['suggested_title', 'suggested_description'],
        }),
        ('Pipeline State', {
            'fields': ['status', 'post', 'target_languages', 'created_at', 'updated_at'],
        }),
    ]

    actions = ['mark_skipped', 'reset_to_pending']

    @admin.action(description='Mark selected as skipped')
    def mark_skipped(self, request, queryset):
        queryset.update(status='skipped')

    @admin.action(description='Reset selected to pending')
    def reset_to_pending(self, request, queryset):
        queryset.update(status='pending', suggested_title='', suggested_description='')
