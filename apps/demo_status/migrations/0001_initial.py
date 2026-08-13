import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Incident",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=180)),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("minor", "Minor"),
                            ("major", "Major"),
                            ("critical", "Critical"),
                        ],
                        default="minor",
                        max_length=20,
                    ),
                ),
                (
                    "phase",
                    models.CharField(
                        choices=[
                            ("investigating", "Investigating"),
                            ("identified", "Identified"),
                            ("monitoring", "Monitoring"),
                            ("resolved", "Resolved"),
                        ],
                        default="investigating",
                        max_length=20,
                    ),
                ),
                ("started_at", models.DateTimeField()),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("summary", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-started_at", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="KumaMonitor",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("monitor_key", models.SlugField(max_length=100, unique=True)),
                ("monitor_type", models.CharField(blank=True, max_length=40)),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("operational", "Healthy"),
                            ("degraded", "Degraded"),
                            ("down", "Unavailable"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=20,
                    ),
                ),
                ("is_available", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="IncidentUpdate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "phase",
                    models.CharField(
                        choices=[
                            ("investigating", "Investigating"),
                            ("identified", "Identified"),
                            ("monitoring", "Monitoring"),
                            ("resolved", "Resolved"),
                        ],
                        max_length=20,
                    ),
                ),
                ("message", models.TextField()),
                ("published_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "incident",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="updates",
                        to="demo_status.incident",
                    ),
                ),
            ],
            options={
                "ordering": ["published_at", "created_at"],
            },
        ),
        migrations.CreateModel(
            name="StatusPage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("site_slug", models.SlugField(max_length=40)),
                ("slug", models.SlugField(default="main", max_length=80)),
                ("title", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("is_visible", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["site_slug", "slug"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("site_slug", "slug"),
                        name="demo_status_one_page_slug_per_site",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="incident",
            name="status_page",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="incidents",
                to="demo_status.statuspage",
            ),
        ),
        migrations.CreateModel(
            name="StatusPageService",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("display_name", models.CharField(blank=True, max_length=120)),
                ("position", models.PositiveIntegerField(default=0)),
                ("is_visible", models.BooleanField(default=True)),
                (
                    "monitor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="page_services",
                        to="demo_status.kumamonitor",
                    ),
                ),
                (
                    "status_page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="services",
                        to="demo_status.statuspage",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "monitor__name"],
            },
        ),
        migrations.AddField(
            model_name="incident",
            name="affected_services",
            field=models.ManyToManyField(
                blank=True, related_name="incidents", to="demo_status.statuspageservice"
            ),
        ),
        migrations.AddConstraint(
            model_name="statuspageservice",
            constraint=models.UniqueConstraint(
                fields=("status_page", "monitor"),
                name="demo_status_one_monitor_per_page",
            ),
        ),
    ]
