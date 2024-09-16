# python manage.py delete_all_tasks
from django.core.management.base import BaseCommand
from background_task.models import Task

class Command(BaseCommand):
    help = 'Delete all background tasks'

    def handle(self, *args, **kwargs):
        Task.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all background tasks'))
