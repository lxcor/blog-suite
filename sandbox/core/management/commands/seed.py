from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates dev users and loads fixture data into the sandbox database.'

    def handle(self, *args, **options):
        User = get_user_model()

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@sandbox.local',
                password='admin',
                first_name='Admin',
                last_name='Sandbox',
            )
            self.stdout.write(self.style.SUCCESS('Created superuser admin / admin'))
        else:
            self.stdout.write('Superuser admin already exists, skipping.')

        call_command('loaddata', 'initial_data', verbosity=1)
        self.stdout.write(self.style.SUCCESS('Sandbox ready — run: python manage.py runserver'))
