from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.Model):
    code = models.CharField(max_length=10, unique=True, help_text=_('BCP 47 tag, e.g. en, pt-br, fr'))
    name = models.CharField(max_length=100, help_text=_('Display name, e.g. English'))

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'
