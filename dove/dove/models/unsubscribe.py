import uuid

from django.db import models


class Unsubscribe(models.Model):
    email = models.EmailField(unique=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Descadastro"
        verbose_name_plural = "Descadastros"
        ordering = ['-created_at']

    def __str__(self):
        return self.email
