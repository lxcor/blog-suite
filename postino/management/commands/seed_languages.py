from django.core.management.base import BaseCommand

from postino.models import Language

DEFAULT_LANGUAGES = [
    ('en', 'English'),
    ('pt-br', 'Portuguese (Brazil)'),
    ('fr', 'French'),
    ('es', 'Spanish'),
    ('de', 'German'),
    ('it', 'Italian'),
    ('ja', 'Japanese'),
    ('zh', 'Chinese (Simplified)'),
]


class Command(BaseCommand):
    help = 'Seed the Language table with common languages.'

    def handle(self, *args, **options):
        created = 0
        for code, name in DEFAULT_LANGUAGES:
            _, was_created = Language.objects.get_or_create(code=code, defaults={'name': name})
            if was_created:
                self.stdout.write(f'  Created: {name} ({code})')
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Done. {created} language(s) added.'))
