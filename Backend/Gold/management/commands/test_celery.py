from django.core.management.base import BaseCommand
from Gold.tasks import test_task

class Command(BaseCommand):
    help = 'Test Celery task'

    def handle(self, *args, **kwargs):
        from django.conf import settings
        settings.configure()
        import django
        django.setup()

        result = test_task.delay()
        self.stdout.write(self.style.SUCCESS(f'Task ID: {result.id}'))
