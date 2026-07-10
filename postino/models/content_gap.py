from django.db import models
from django.utils.translation import gettext_lazy as _


class ContentGapOpportunity(models.Model):
    COMPETITION_CHOICES = [
        ('UNKNOWN', _('Unknown')),
        ('LOW', _('Low')),
        ('MEDIUM', _('Medium')),
        ('HIGH', _('High')),
    ]
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('suggested', _('Suggested')),
        ('generated', _('Generated')),
        ('skipped', _('Skipped')),
    ]

    # From source report
    keyword = models.CharField(max_length=500)
    volume = models.IntegerField(null=True, blank=True, help_text=_('Average monthly searches'))
    competition = models.CharField(max_length=10, choices=COMPETITION_CHOICES, default='UNKNOWN')
    cpc_low = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cpc_high = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    seed_keyword = models.CharField(max_length=500, blank=True)
    suggested_slug = models.CharField(max_length=255, blank=True)
    content_angle = models.TextField(blank=True)
    source_report = models.CharField(max_length=500, blank=True, help_text=_('Report file that originated this record'))

    # Filled by suggest_post_ideas
    suggested_title = models.CharField(max_length=200, blank=True)
    suggested_description = models.TextField(blank=True)

    target_languages = models.ManyToManyField(
        'postino.Language',
        blank=True,
        related_name='opportunities',
        verbose_name=_('Target translation languages'),
        help_text=_('Languages the generated post should be translated into.'),
    )

    # Pipeline state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    post = models.ForeignKey(
        'postino.Post',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='content_gap_opportunities',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Content Gap Opportunity')
        verbose_name_plural = _('Content Gap Opportunities')
        ordering = ['-volume', 'keyword']
        unique_together = [('keyword', 'source_report')]

    def __str__(self):
        return f'{self.keyword} ({self.volume}/mo)'
