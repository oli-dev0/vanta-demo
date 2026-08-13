import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NewsletterSite",
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
                ("site_slug", models.SlugField(unique=True)),
                ("name", models.CharField(max_length=120)),
                ("domain", models.CharField(max_length=255)),
                ("sender_name", models.CharField(max_length=120)),
                ("sender_email", models.EmailField(max_length=254)),
                ("is_active", models.BooleanField(default=False)),
                ("double_opt_in", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name", "pk"],
            },
        ),
        migrations.CreateModel(
            name="NewsletterImage",
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
                ("image_url", models.URLField(blank=True, editable=False)),
                ("width", models.PositiveIntegerField(default=0)),
                ("height", models.PositiveIntegerField(default=0)),
                ("alt_text", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "newsletter_site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="images",
                        to="demo_newsletter.newslettersite",
                    ),
                ),
            ],
            options={
                "verbose_name": "image",
                "verbose_name_plural": "images",
                "ordering": ["-created_at", "-pk"],
            },
        ),
        migrations.CreateModel(
            name="Campaign",
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
                ("subject", models.CharField(max_length=255)),
                ("html_content", models.TextField()),
                ("text_content", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("scheduled", "Scheduled"),
                            ("queued", "Queued"),
                            ("sending", "Sending"),
                            ("completed", "Completed"),
                            ("completed_with_failures", "Completed with failures"),
                        ],
                        default="draft",
                        max_length=30,
                    ),
                ),
                ("scheduled_for", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("target_count", models.PositiveIntegerField(blank=True, null=True)),
                ("last_error", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "featured_image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="campaigns",
                        to="demo_newsletter.newsletterimage",
                    ),
                ),
                (
                    "newsletter_site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="campaigns",
                        to="demo_newsletter.newslettersite",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-pk"],
            },
        ),
        migrations.CreateModel(
            name="Subscription",
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
                    "public_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("email", models.EmailField(max_length=254)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending confirmation"),
                            ("active", "Active"),
                            ("unsubscribed", "Unsubscribed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[("public_form", "Public form"), ("admin", "Admin")],
                        default="public_form",
                        max_length=20,
                    ),
                ),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("activated_at", models.DateTimeField(blank=True, null=True)),
                ("unsubscribed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "newsletter_site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="subscriptions",
                        to="demo_newsletter.newslettersite",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-pk"],
            },
        ),
        migrations.CreateModel(
            name="CampaignDelivery",
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
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("queued", "Queued"),
                            ("sent", "Sent"),
                            ("failed", "Failed"),
                            ("skipped_unsubscribed", "Skipped - unsubscribed"),
                        ],
                        default="pending",
                        max_length=30,
                    ),
                ),
                ("queued_at", models.DateTimeField(blank=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("failed_at", models.DateTimeField(blank=True, null=True)),
                ("skipped_at", models.DateTimeField(blank=True, null=True)),
                ("last_error_summary", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "campaign",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deliveries",
                        to="demo_newsletter.campaign",
                    ),
                ),
                (
                    "subscription",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="campaign_deliveries",
                        to="demo_newsletter.subscription",
                    ),
                ),
            ],
            options={
                "verbose_name": "campaign delivery",
                "verbose_name_plural": "campaign deliveries",
                "ordering": ["pk"],
            },
        ),
        migrations.AddIndex(
            model_name="campaign",
            index=models.Index(
                fields=["newsletter_site", "status", "created_at"],
                name="demo_newsle_newslet_77542b_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(
                fields=["newsletter_site", "status", "created_at"],
                name="demo_newsle_newslet_619ac1_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="subscription",
            constraint=models.UniqueConstraint(
                fields=("newsletter_site", "email"),
                name="demo_newsletter_site_email_unique",
            ),
        ),
        migrations.AddIndex(
            model_name="campaigndelivery",
            index=models.Index(
                fields=["campaign", "status", "id"],
                name="demo_newsle_campaig_b89104_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="campaigndelivery",
            constraint=models.UniqueConstraint(
                fields=("campaign", "subscription"),
                name="demo_newsletter_campaign_subscription_unique",
            ),
        ),
    ]
