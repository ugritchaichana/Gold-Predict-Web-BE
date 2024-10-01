# Backend/Gold/management/commands/show_tasks.py

from django.core.management.base import BaseCommand
from background_task.models import Task

class Command(BaseCommand):
    help = 'Show all background tasks'

    def handle(self, *args, **kwargs):
        tasks = Task.objects.all()
        if not tasks:
            self.stdout.write(self.style.SUCCESS('No background tasks found'))
            return

        for task in tasks:
            self.stdout.write(f'Task ID: {task.id}')
            self.stdout.write(f'Task Name: {task.task_name}')
            self.stdout.write(f'Parameters: {task.task_params}')
            self.stdout.write(f'Hash: {task.task_hash}')
            self.stdout.write(f'Verbose Name: {task.verbose_name}')
            self.stdout.write(f'Priority: {task.priority}')
            self.stdout.write(f'Run At: {task.run_at}')
            self.stdout.write('------')
