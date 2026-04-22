from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Test commands'

    def handle(self, *args, **options):
        self.stdout.write('Test commands works!')