import json

from django.core.management.base import BaseCommand, CommandError

from postino.llm import get_llm_client
from postino.models import ContentGapOpportunity


class Command(BaseCommand):
    help = (
        'Use LLM to generate a suggested title and description for pending '
        'content gap opportunities. Pass --set-title / --set-description with '
        '--opportunity-id to manually override a record without calling the LLM.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Maximum number of opportunities to process (default: 5).',
        )
        parser.add_argument(
            '--opportunity-id',
            type=int,
            dest='opportunity_id',
            help='Process a single opportunity by ID.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without calling the LLM.',
        )
        parser.add_argument(
            '--set-title',
            dest='set_title',
            default='',
            help='Manually set the suggested_title on the opportunity (requires --opportunity-id).',
        )
        parser.add_argument(
            '--set-description',
            dest='set_description',
            default='',
            help='Manually set the suggested_description on the opportunity (requires --opportunity-id).',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        opp_id = options['opportunity_id']
        dry_run = options['dry_run']
        set_title = options['set_title'].strip()
        set_description = options['set_description'].strip()

        # Manual edit mode — no LLM call
        if set_title or set_description:
            if not opp_id:
                raise CommandError('--set-title / --set-description require --opportunity-id.')
            try:
                opp = ContentGapOpportunity.objects.get(pk=opp_id)
            except ContentGapOpportunity.DoesNotExist:
                raise CommandError(f'Opportunity #{opp_id} not found.')

            update_fields = ['status', 'updated_at']
            if set_title:
                opp.suggested_title = set_title
                update_fields.append('suggested_title')
            if set_description:
                opp.suggested_description = set_description
                update_fields.append('suggested_description')
            opp.status = 'suggested'
            opp.save(update_fields=update_fields)

            self.stdout.write(self.style.SUCCESS(f'Updated #{opp.pk}:'))
            self.stdout.write(f'  Title:       {opp.suggested_title}')
            self.stdout.write(f'  Description: {opp.suggested_description}')
            return

        if opp_id:
            qs = ContentGapOpportunity.objects.filter(pk=opp_id)
            if not qs.exists():
                raise CommandError(f'Opportunity #{opp_id} not found.')
        else:
            qs = ContentGapOpportunity.objects.filter(status='pending').order_by('-volume')[:limit]

        if not qs:
            self.stdout.write(self.style.WARNING('No pending opportunities found.'))
            return

        if dry_run:
            self.stdout.write('Dry run — would process:')
            for opp in qs:
                self.stdout.write(f'  #{opp.pk}  {opp.keyword}  ({opp.volume}/mo)')
            return

        llm = get_llm_client()
        processed = failed = 0

        for opp in qs:
            self.stdout.write(f'Processing #{opp.pk}: {opp.keyword} ...')
            try:
                result = llm.suggest_post_idea({
                    'keyword': opp.keyword,
                    'volume': opp.volume,
                    'competition': opp.competition,
                    'seed_keyword': opp.seed_keyword,
                    'content_angle': opp.content_angle,
                })
                opp.suggested_title = result.get('title', '')
                opp.suggested_description = result.get('description', '')
                opp.status = 'suggested'
                opp.save(update_fields=['suggested_title', 'suggested_description', 'status', 'updated_at'])

                self.stdout.write(f'  Title:       {opp.suggested_title}')
                self.stdout.write(f'  Description: {opp.suggested_description}')
                processed += 1

            except (json.JSONDecodeError, KeyError) as exc:
                self.stderr.write(self.style.ERROR(f'  LLM returned invalid JSON for #{opp.pk}: {exc}'))
                failed += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  Error processing #{opp.pk}: {exc}'))
                failed += 1

        self.stdout.write(
            self.style.SUCCESS(f'Done. {processed} suggested, {failed} failed.')
        )
