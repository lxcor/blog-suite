from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Comment


@receiver(post_save, sender=Comment)
def notify_admin_on_new_comment(sender, instance, created, **kwargs):
    if not created:
        return

    admin_email = getattr(settings, 'POSTINO_ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)

    subject = f'Novo comentário no post: {instance.post.title}'
    message = (
        f'Novo comentário recebido:\n\n'
        f'Post: {instance.post.title}\n'
        f'Autor: {instance.author_name}\n'
        f'E-mail: {instance.author_email}\n'
        f'Comentário: {instance.content}\n\n'
        f'Acesse o admin para aprovar ou rejeitar.'
    )

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)
