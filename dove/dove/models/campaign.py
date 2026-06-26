import uuid

from django.db import models


class Campaign(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Rascunho'),
        ('scheduled', 'Agendado'),
        ('sending', 'Enviando'),
        ('sent', 'Enviado'),
    )

    subject = models.CharField(max_length=200, verbose_name="Assunto")
    preview_text = models.CharField(max_length=200, blank=True, verbose_name="Texto de Preview")
    body_html = models.TextField(verbose_name="Corpo HTML")
    body_text = models.TextField(blank=True, verbose_name="Corpo Texto Simples")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Status"
    )
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name="Agendado para")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviado em")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Campanha"
        verbose_name_plural = "Campanhas"
        ordering = ['-created_at']

    def __str__(self):
        return self.subject


class CampaignSend(models.Model):
    STATUS_CHOICES = (
        ('queued', 'Na Fila'),
        ('sent', 'Enviado'),
        ('failed', 'Falhou'),
    )

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='sends')
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    sent_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Envio"
        verbose_name_plural = "Envios"
        unique_together = [('campaign', 'email')]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.campaign.subject} → {self.email}"
