import logging
import time
import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from apps.vanta_demo.database import workspace_path, workspace_temp_path
from apps.vanta_demo.models import DemoThrottleBucket, DemoWorkspace


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Expire and remove disposable Vanta demo workspaces and throttle buckets.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        del args
        limit = options['limit']
        if limit < 1 or limit > 1000:
            raise CommandError('--limit must be between 1 and 1000.')

        started = time.monotonic()
        now = timezone.now()
        counts = {'expired': 0, 'retired': 0, 'orphans': 0, 'throttles': 0, 'failures': 0}
        candidates = self._candidate_workspaces(now, limit)
        for workspace in candidates:
            if options['dry_run']:
                counts['retired'] += 1
                continue
            try:
                with transaction.atomic(using='default'):
                    locked = DemoWorkspace.objects.using('default').select_for_update().get(
                        pk=workspace.pk
                    )
                    if locked.status in {
                        DemoWorkspace.Status.CREATING,
                        DemoWorkspace.Status.ACTIVE,
                    }:
                        was_creating = locked.status == DemoWorkspace.Status.CREATING
                        locked.status = DemoWorkspace.Status.EXPIRED
                        locked.retired_at = now
                        locked.failure_code = (
                            'creation_timeout'
                            if was_creating
                            else locked.failure_code
                        )
                        locked.save(
                            using='default',
                            update_fields=['status', 'retired_at', 'failure_code'],
                        )
                        counts['expired'] += 1
                    workspace_path(locked.id).unlink(missing_ok=True)
                    workspace_temp_path(locked.id).unlink(missing_ok=True)
                    locked.status = DemoWorkspace.Status.RETIRED
                    locked.retired_at = now
                    locked.save(using='default', update_fields=['status', 'retired_at'])
                    counts['retired'] += 1
            except OSError:
                counts['failures'] += 1

        counts['orphans'] = self._remove_orphans(now, limit, dry_run=options['dry_run'])
        expired_throttle_ids = list(
            DemoThrottleBucket.objects.using('default')
            .filter(expires_at__lte=now)
            .order_by('expires_at', 'pk')
            .values_list('pk', flat=True)[:limit]
        )
        counts['throttles'] = len(expired_throttle_ids)
        if not options['dry_run']:
            DemoThrottleBucket.objects.using('default').filter(
                pk__in=expired_throttle_ids
            ).delete()

        duration_ms = round((time.monotonic() - started) * 1000)
        logger.info(
            'vanta_demo_cleanup expired=%s retired=%s orphans=%s throttles=%s failures=%s duration_ms=%s dry_run=%s',
            counts['expired'],
            counts['retired'],
            counts['orphans'],
            counts['throttles'],
            counts['failures'],
            duration_ms,
            options['dry_run'],
        )
        self.stdout.write(
            ' '.join(f'{key}={value}' for key, value in counts.items())
        )
        if counts['failures']:
            raise CommandError('The Vanta demo cleanup pass was incomplete.')

    def _candidate_workspaces(self, now, limit):
        creating_before = now - timedelta(seconds=settings.VANTA_DEMO_CREATING_TIMEOUT_SECONDS)
        queryset = DemoWorkspace.objects.using('default').filter(
            models_filter(now, creating_before)
        ).order_by('created_at')
        if connection.features.has_select_for_update_skip_locked:
            with transaction.atomic(using='default'):
                return list(queryset.select_for_update(skip_locked=True)[:limit])
        return list(queryset[:limit])

    def _remove_orphans(self, now, limit, *, dry_run):
        root = Path(settings.VANTA_DEMO_WORKSPACE_ROOT)
        if not root.is_dir():
            return 0
        cutoff = now.timestamp() - settings.VANTA_DEMO_ORPHAN_MIN_AGE_SECONDS
        live_ids = {
            str(value)
            for value in DemoWorkspace.objects.using('default').exclude(
                status=DemoWorkspace.Status.RETIRED
            ).values_list('id', flat=True)
        }
        removed = 0
        for path in sorted([*root.glob('*.sqlite3'), *root.glob('*.sqlite3.tmp')]):
            if removed >= limit:
                break
            identifier = path.name.removesuffix('.sqlite3.tmp').removesuffix('.sqlite3')
            try:
                identifier = str(uuid.UUID(identifier))
                old_enough = path.stat().st_mtime <= cutoff
            except (ValueError, OSError):
                continue
            if identifier in live_ids or not old_enough:
                continue
            if not dry_run:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    continue
            removed += 1
        return removed


def models_filter(now, creating_before):
    from django.db.models import Q

    return (
        Q(status=DemoWorkspace.Status.CREATING, created_at__lte=creating_before)
        | Q(status=DemoWorkspace.Status.ACTIVE, expires_at__lte=now)
        | Q(status=DemoWorkspace.Status.ACTIVE)
        & ~Q(seed_version=settings.VANTA_DEMO_SEED_VERSION)
        | Q(status__in=[DemoWorkspace.Status.EXPIRED, DemoWorkspace.Status.FAILED])
    )
