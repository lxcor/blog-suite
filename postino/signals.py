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

    subject = f'New comment on post: {instance.post.title}'
    message = (
        f'New comment received:\n\n'
        f'Post: {instance.post.title}\n'
        f'Author: {instance.author_name}\n'
        f'Email: {instance.author_email}\n'
        f'Comment: {instance.content}\n\n'
        f'Visit the admin to approve or reject it.'
    )

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)
