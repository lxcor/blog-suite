from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.utils.html import strip_tags

from postino.models import Subscription

from .models import Campaign, CampaignSend, Unsubscribe


def dispatch_campaign(campaign_id):
    campaign = Campaign.objects.get(pk=campaign_id)

    if campaign.status not in ('draft', 'scheduled'):
        raise ValueError(
            f"Cannot send campaign '{campaign.subject}': status is '{campaign.status}'."
        )

    campaign.status = 'sending'
    campaign.save(update_fields=['status', 'updated_at'])

    from_email = getattr(settings, 'DOVE_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
    site_url = getattr(settings, 'DOVE_SITE_URL', '').rstrip('/')

    unsubscribed = set(
        Unsubscribe.objects.values_list('email', flat=True)
    )

    subscribers = (
        Subscription.objects
        .exclude(email__isnull=True)
        .exclude(email='')
        .values_list('email', flat=True)
        .distinct()
    )

    for email in subscribers:
        if email.lower() in {e.lower() for e in unsubscribed}:
            continue

        send_obj, created = CampaignSend.objects.get_or_create(
            campaign=campaign,
            email=email,
            defaults={'status': 'queued'},
        )

        if not created and send_obj.status == 'sent':
            continue

        unsubscribe_url = f"{site_url}/dove/unsubscribe/{send_obj.token}/"

        body_html = campaign.body_html.replace('{{unsubscribe_url}}', unsubscribe_url)
        body_text = (campaign.body_text or strip_tags(body_html)).replace(
            '{{unsubscribe_url}}', unsubscribe_url
        )

        try:
            msg = EmailMultiAlternatives(
                subject=campaign.subject,
                body=body_text,
                from_email=from_email,
                to=[email],
            )
            msg.attach_alternative(body_html, 'text/html')
            msg.send()

            send_obj.status = 'sent'
            send_obj.sent_at = timezone.now()
            send_obj.save(update_fields=['status', 'sent_at'])
        except Exception as exc:
            send_obj.status = 'failed'
            send_obj.error = str(exc)
            send_obj.save(update_fields=['status', 'error'])

    campaign.status = 'sent'
    campaign.sent_at = timezone.now()
    campaign.save(update_fields=['status', 'sent_at', 'updated_at'])
