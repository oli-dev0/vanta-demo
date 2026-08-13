from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models


class NewsletterSite(models.Model):
    site_slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    domain = models.CharField(max_length=255)
    sender_name = models.CharField(max_length=120)
    sender_email = models.EmailField(max_length=254)
    is_active = models.BooleanField(default=False)
    double_opt_in = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending confirmation"
        ACTIVE = "active", "Active"
        UNSUBSCRIBED = "unsubscribed", "Unsubscribed"

    class Source(models.TextChoices):
        PUBLIC_FORM = "public_form", "Public form"
        ADMIN = "admin", "Admin"

    public_id = models.UUIDField(default=uuid4, unique=True, editable=False)
    newsletter_site = models.ForeignKey(
        NewsletterSite,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    email = models.EmailField(max_length=254)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.PUBLIC_FORM
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["newsletter_site", "email"],
                name="demo_newsletter_site_email_unique",
            )
        ]
        indexes = [models.Index(fields=["newsletter_site", "status", "created_at"])]
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.email} ({self.newsletter_site})"

    def clean(self):
        self.email = self.email.strip().casefold()
        if self.status == self.Status.ACTIVE and not self.activated_at:
            raise ValidationError(
                {"activated_at": "Active subscriptions require an activation time."}
            )
        if self.status == self.Status.UNSUBSCRIBED and not self.unsubscribed_at:
            raise ValidationError(
                {"unsubscribed_at": "Unsubscribed records require an unsubscribe time."}
            )

    def save(self, *args, **kwargs):
        self.email = self.email.strip().casefold()
        super().save(*args, **kwargs)


class NewsletterImage(models.Model):
    newsletter_site = models.ForeignKey(
        NewsletterSite,
        on_delete=models.PROTECT,
        related_name="images",
    )
    name = models.CharField(max_length=120)
    image_url = models.URLField(blank=True, editable=False)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    alt_text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "image"
        verbose_name_plural = "images"
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.name


class Campaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        QUEUED = "queued", "Queued"
        SENDING = "sending", "Sending"
        COMPLETED = "completed", "Completed"
        COMPLETED_WITH_FAILURES = "completed_with_failures", "Completed with failures"

    newsletter_site = models.ForeignKey(
        NewsletterSite,
        on_delete=models.PROTECT,
        related_name="campaigns",
    )
    featured_image = models.ForeignKey(
        NewsletterImage,
        on_delete=models.PROTECT,
        related_name="campaigns",
        null=True,
        blank=True,
    )
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    text_content = models.TextField()
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.DRAFT
    )
    scheduled_for = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    target_count = models.PositiveIntegerField(null=True, blank=True)
    last_error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["newsletter_site", "status", "created_at"])]
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.subject

    def clean(self):
        if (
            self.featured_image_id
            and self.featured_image.newsletter_site_id != self.newsletter_site_id
        ):
            raise ValidationError(
                {"featured_image": "Choose an image from the same newsletter site."}
            )
        if self.status == self.Status.SCHEDULED and not self.scheduled_for:
            raise ValidationError(
                {"scheduled_for": "Scheduled campaigns require a date and time."}
            )


class CampaignDelivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        SKIPPED_UNSUBSCRIBED = "skipped_unsubscribed", "Skipped - unsubscribed"

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="deliveries"
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        related_name="campaign_deliveries",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.PENDING
    )
    queued_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    skipped_at = models.DateTimeField(null=True, blank=True)
    last_error_summary = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "subscription"],
                name="demo_newsletter_campaign_subscription_unique",
            )
        ]
        indexes = [models.Index(fields=["campaign", "status", "id"])]
        ordering = ["pk"]
        verbose_name = "campaign delivery"
        verbose_name_plural = "campaign deliveries"

    def __str__(self):
        return f"{self.campaign} / {self.status}"
