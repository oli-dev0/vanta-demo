from django.core.exceptions import ValidationError
from django.db import models


class StatusPage(models.Model):
    site_slug = models.SlugField(max_length=40)
    slug = models.SlugField(max_length=80, default="main")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_visible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["site_slug", "slug"],
                name="demo_status_one_page_slug_per_site",
            )
        ]
        ordering = ["site_slug", "slug"]

    def __str__(self):
        return f"{self.title} ({self.site_slug})"


class KumaMonitor(models.Model):
    class State(models.TextChoices):
        OPERATIONAL = "operational", "Healthy"
        DEGRADED = "degraded", "Degraded"
        DOWN = "down", "Unavailable"
        UNKNOWN = "unknown", "Unknown"

    name = models.CharField(max_length=120)
    monitor_key = models.SlugField(max_length=100, unique=True)
    monitor_type = models.CharField(max_length=40, blank=True)
    state = models.CharField(
        max_length=20, choices=State.choices, default=State.UNKNOWN
    )
    is_available = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class StatusPageService(models.Model):
    status_page = models.ForeignKey(
        StatusPage, on_delete=models.CASCADE, related_name="services"
    )
    monitor = models.ForeignKey(
        KumaMonitor, on_delete=models.PROTECT, related_name="page_services"
    )
    display_name = models.CharField(max_length=120, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["status_page", "monitor"],
                name="demo_status_one_monitor_per_page",
            )
        ]
        ordering = ["position", "monitor__name"]

    def __str__(self):
        return self.display_name or self.monitor.name


class Incident(models.Model):
    class Severity(models.TextChoices):
        MINOR = "minor", "Minor"
        MAJOR = "major", "Major"
        CRITICAL = "critical", "Critical"

    class Phase(models.TextChoices):
        INVESTIGATING = "investigating", "Investigating"
        IDENTIFIED = "identified", "Identified"
        MONITORING = "monitoring", "Monitoring"
        RESOLVED = "resolved", "Resolved"

    status_page = models.ForeignKey(
        StatusPage, on_delete=models.CASCADE, related_name="incidents"
    )
    title = models.CharField(max_length=180)
    severity = models.CharField(
        max_length=20, choices=Severity.choices, default=Severity.MINOR
    )
    phase = models.CharField(
        max_length=20, choices=Phase.choices, default=Phase.INVESTIGATING
    )
    affected_services = models.ManyToManyField(
        StatusPageService, blank=True, related_name="incidents"
    )
    started_at = models.DateTimeField()
    resolved_at = models.DateTimeField(blank=True, null=True)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-started_at", "-created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        if self.phase != self.Phase.RESOLVED and self.resolved_at:
            raise ValidationError(
                {"resolved_at": "Only resolved incidents can have a resolved time."}
            )


class IncidentUpdate(models.Model):
    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name="updates"
    )
    phase = models.CharField(max_length=20, choices=Incident.Phase.choices)
    message = models.TextField()
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["published_at", "created_at"]

    def __str__(self):
        return f"{self.incident} update at {self.published_at:%Y-%m-%d %H:%M}"
