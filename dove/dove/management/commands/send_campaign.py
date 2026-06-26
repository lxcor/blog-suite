from django.core.management.base import BaseCommand, CommandError

from dove.models import Campaign
from dove.services import dispatch_campaign


class Command(BaseCommand):
    help = 'Send a campaign to all active subscribers'

    def add_arguments(self, parser):
        parser.add_argument('campaign_id', type=int, help='ID of the campaign to send')

    def handle(self, *args, **options):
        campaign_id = options['campaign_id']

        try:
            campaign = Campaign.objects.get(pk=campaign_id)
        except Campaign.DoesNotExist:
            raise CommandError(f'Campaign {campaign_id} does not exist.')

        if campaign.status not in ('draft', 'scheduled'):
            raise CommandError(
                f'Campaign "{campaign.subject}" is already in status "{campaign.status}".'
            )

        self.stdout.write(f'Sending campaign "{campaign.subject}" (id={campaign_id})...')

        dispatch_campaign(campaign_id)

        sent = campaign.sends.filter(status='sent').count()
        failed = campaign.sends.filter(status='failed').count()

        self.stdout.write(
            self.style.SUCCESS(f'Done. Sent: {sent}  Failed: {failed}')
        )
