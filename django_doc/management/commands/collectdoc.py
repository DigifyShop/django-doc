from django_doc import main
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Collecting Docstrings of Project'

    def handle(self, *args, **options):
        text = main.run(f"{settings.BASE_DIR}/")
        if text is None:
            text = "Documentation Collected Successfully. Run the documentation with `mkdocs serve`"
            message = self.style.SUCCESS(text)
        else:
            message = self.style.ERROR(text)
        self.stdout.write(message)
