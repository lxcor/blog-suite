from django.contrib import admin

from ..models import Campaign, CampaignSend
from ..services import dispatch_campaign


class CampaignSendInline(admin.TabularInline):
    model = CampaignSend
    extra = 0
    readonly_fields = ['email', 'status', 'sent_at', 'error', 'token']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['subject', 'status', 'sent_count', 'failed_count', 'sent_at', 'created_at']
    list_filter = ['status']
    search_fields = ['subject']
    readonly_fields = ['status', 'sent_at', 'created_at', 'updated_at']
    inlines = [CampaignSendInline]
    actions = ['action_send_campaign']

    def sent_count(self, obj):
        return obj.sends.filter(status='sent').count()
    sent_count.short_description = 'Sent'

    def failed_count(self, obj):
        return obj.sends.filter(status='failed').count()
    failed_count.short_description = 'Failed'

    def action_send_campaign(self, request, queryset):
        eligible = queryset.filter(status__in=['draft', 'scheduled'])
        for campaign in eligible:
            dispatch_campaign(campaign.pk)
        self.message_user(request, f'{eligible.count()} campaign(s) sent.')
    action_send_campaign.short_description = 'Send selected campaigns'
