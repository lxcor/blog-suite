import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Campaign(models.Model):
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('scheduled', _('Scheduled')),
        ('sending', _('Sending')),
        ('sent', _('Sent')),
    )

    subject = models.CharField(max_length=200, verbose_name=_("Subject"))
    preview_text = models.CharField(max_length=200, blank=True, verbose_name=_("Preview Text"))
    body_html = models.TextField(verbose_name=_("HTML Body"))
    body_text = models.TextField(blank=True, verbose_name=_("Plain Text Body"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_("Status")
    )
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Scheduled for"))
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Sent at"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ['-created_at']

    def __str__(self):
        return self.subject


class CampaignSend(models.Model):
    STATUS_CHOICES = (
        ('queued', _('Queued')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
    )

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='sends')
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    sent_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Campaign Send")
        verbose_name_plural = _("Campaign Sends")
        unique_together = [('campaign', 'email')]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.campaign.subject} → {self.email}"
