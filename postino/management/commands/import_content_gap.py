import os
import re
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from postino.models import ContentGapOpportunity


def _parse_report(path: str, min_volume: int) -> list[dict]:
    """Extract content gap opportunities from a seo-suite markdown report."""
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()

    # Locate the Content Gap Opportunities section
    gap_match = re.search(
        r'## Content Gap Opportunities(.*?)(?=^## |\Z)',
        content,
        re.DOTALL | re.MULTILINE,
    )
    if not gap_match:
        return []

    gap_section = gap_match.group(1)
    blocks = re.split(r'^#### ', gap_section, flags=re.MULTILINE)

    opportunities = []
    for block in blocks[1:]:  # blocks[0] is the intro text before first ####
        lines = block.strip().split('\n')
        keyword = lines[0].strip()

        opp = {
            'keyword': keyword,
            'volume': None,
            'competition': 'UNKNOWN',
            'cpc_low': None,
            'cpc_high': None,
            'seed_keyword': '',
            'suggested_slug': '',
            'content_angle': '',
        }

        for line in lines[1:]:
            line = line.strip().lstrip('- ')

            vol_m = re.search(r'\*\*Volume:\*\* ([\d,?]+)/mo', line)
            if vol_m:
                vol_str = vol_m.group(1).replace(',', '')
                opp['volume'] = None if vol_str == '?' else int(vol_str)

            comp_m = re.search(r'\*\*Competition:\*\* (\w+)', line)
            if comp_m:
                opp['competition'] = comp_m.group(1).upper()

            cpc_m = re.search(r'\*\*CPC:\*\* \$([\d.?]+)–\$([\d.?]+)', line)
            if cpc_m:
                low, high = cpc_m.group(1), cpc_m.group(2)
                opp['cpc_low'] = None if low == '?' else Decimal(low)
                opp['cpc_high'] = None if high == '?' else Decimal(high)

            seed_m = re.search(r'\*\*Seed keyword:\*\* (.+)', line)
            if seed_m:
                opp['seed_keyword'] = seed_m.group(1).strip()

            slug_m = re.search(r'\*\*Suggested slug:\*\* `(.+?)`', line)
            if slug_m:
                opp['suggested_slug'] = slug_m.group(1).strip()

            angle_m = re.search(r'\*\*Content angle:\*\* (.+)', line)
            if angle_m:
                opp['content_angle'] = angle_m.group(1).strip()

        vol = opp['volume']
        if vol is None or vol >= min_volume:
            opportunities.append(opp)

    return opportunities


class Command(BaseCommand):
    help = 'Import content gap opportunities from a seo-suite markdown report.'

    def add_arguments(self, parser):
        parser.add_argument('report', help='Path to the seo-suite .md report file.')
        parser.add_argument(
            '--min-volume',
            type=int,
            default=100,
            help='Skip opportunities with monthly volume below this threshold (default: 100).',
        )

    def handle(self, *args, **options):
        path = options['report']
        min_volume = options['min_volume']

        if not os.path.isfile(path):
            raise CommandError(f'File not found: {path}')

        # Store a relative-ish label — last two path components, e.g. calendula.lxcor.com/2026-07-10.md
        parts = path.replace('\\', '/').split('/')
        source_label = '/'.join(parts[-2:]) if len(parts) >= 2 else parts[-1]

        opportunities = _parse_report(path, min_volume)
        if not opportunities:
            self.stdout.write(self.style.WARNING('No content gap opportunities found in report.'))
            return

        imported = skipped = 0
        for opp_data in opportunities:
            _, created = ContentGapOpportunity.objects.get_or_create(
                keyword=opp_data['keyword'],
                source_report=source_label,
                defaults={
                    'volume': opp_data['volume'],
                    'competition': opp_data['competition'],
                    'cpc_low': opp_data['cpc_low'],
                    'cpc_high': opp_data['cpc_high'],
                    'seed_keyword': opp_data['seed_keyword'],
                    'suggested_slug': opp_data['suggested_slug'],
                    'content_angle': opp_data['content_angle'],
                },
            )
            if created:
                imported += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. {imported} imported, {skipped} skipped (already existed).'
            )
        )
