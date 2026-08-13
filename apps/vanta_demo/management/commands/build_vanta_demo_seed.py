import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command
from django.db import connections

from apps.vanta_demo.context import workspace_database
from apps.vanta_demo.database import register_seed_database
from apps.vanta_demo.seed_data import load_fictional_seed
from apps.vanta_demo.services.workspaces import validate_workspace_file


FIXED_NOW = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


class Command(BaseCommand):
    help = 'Build the deterministic fictional SQLite seed for the Vanta Admin demo.'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('--destination', type=Path, default=settings.VANTA_DEMO_SEED_PATH)
        parser.add_argument('--force', action='store_true', help='Replace an existing build artifact.')

    def handle(self, *args, **options):
        del args
        destination = options['destination'].expanduser().resolve()
        if destination.exists() and not options['force']:
            raise CommandError('The seed destination already exists; pass --force only in the image build.')
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o755)

        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix='.vanta-demo-seed-',
            suffix='.sqlite3',
            dir=destination.parent,
        )
        os.close(file_descriptor)
        temporary_path = Path(temporary_name)
        temporary_path.unlink()
        alias = register_seed_database(temporary_path)
        try:
            with workspace_database(alias):
                call_command(
                    'migrate',
                    database=alias,
                    interactive=False,
                    verbosity=0,
                    skip_checks=True,
                )
                self._load_fixtures(alias)
            connections[alias].close()
            if not validate_workspace_file(temporary_path):
                raise CommandError('The generated Vanta demo seed failed validation.')
            temporary_path.chmod(0o444)
            os.replace(temporary_path, destination)
            destination.chmod(0o444)
        finally:
            connections[alias].close()
            temporary_path.unlink(missing_ok=True)

        self.stdout.write(self.style.SUCCESS(f'Built Vanta demo seed at {destination}'))

    def _load_fixtures(self, alias):
        load_fictional_seed(alias, FIXED_NOW)
