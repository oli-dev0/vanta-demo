import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class DemoWorkspace(models.Model):
    class Status(models.TextChoices):
        CREATING = 'creating', _('Creating')
        ACTIVE = 'active', _('Active')
        EXPIRED = 'expired', _('Expired')
        FAILED = 'failed', _('Failed')
        RETIRED = 'retired', _('Retired')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    browser_id = models.UUIDField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CREATING)
    seed_version = models.CharField(max_length=32)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    last_activity_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(db_index=True)
    retired_at = models.DateTimeField(blank=True, null=True)
    failure_code = models.CharField(max_length=32, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['browser_id'],
                condition=Q(status__in=['creating', 'active']),
                name='vanta_demo_one_live_workspace_per_browser',
            ),
        ]
        indexes = [
            models.Index(fields=['status', 'expires_at'], name='vanta_demo_status_expiry_idx'),
            models.Index(fields=['browser_id', 'status'], name='vanta_demo_browser_status_idx'),
        ]

    def __str__(self):
        return f'Demo workspace ({self.status})'

    def is_active(self, *, seed_version, at=None):
        at = at or timezone.now()
        return (
            self.status == self.Status.ACTIVE
            and self.seed_version == seed_version
            and self.expires_at > at
        )


class DemoThrottleBucket(models.Model):
    class Action(models.TextChoices):
        WORKSPACE_START = 'workspace_start', _('Workspace start')

    key_hash = models.CharField(max_length=64)
    action = models.CharField(max_length=32, choices=Action.choices)
    window_started_at = models.DateTimeField()
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['key_hash', 'action'],
                name='vanta_demo_unique_throttle_bucket',
            ),
        ]

    def __str__(self):
        return f'{self.action} throttle bucket'


class DemoCapacityLock(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return 'Vanta demo capacity lock'
