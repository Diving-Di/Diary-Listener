from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a default dev user (admin/admin123)'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'admin'
        password = 'password'
        email = 'admin@example.com'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created user: {username} / {password}'))
        else:
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists'))
