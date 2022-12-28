from django_doc import main
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Collecting Docstrings of Project'

    def handle(self, *args, **options):
        main.run(f'{settings.BASE_DIR}/')
        txt = 'Documentation Collected Successfully. Run the documentation with `mkdocs serve`'
        self.stdout.write(self.style.SUCCESS(txt))
