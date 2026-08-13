from django.db import models


class Project(models.Model):
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    repo_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    cover_image = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["is_published", "is_featured", "sort_order"])]
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        if self.pk:
            translation = (
                self.translations.filter(language_code="en").only("title").first()
            )
            if translation:
                return translation.title
        return f"Project #{self.pk}"


class ProjectTranslation(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="translations"
    )
    language_code = models.CharField(max_length=8)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    summary = models.TextField()
    body = models.TextField(blank=True)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "language_code"],
                name="demo_projects_one_translation_per_language",
            ),
            models.UniqueConstraint(
                fields=["language_code", "slug"],
                name="demo_projects_unique_slug_per_language",
            ),
        ]
        indexes = [models.Index(fields=["language_code", "slug"])]
        ordering = ["language_code", "title"]

    def __str__(self):
        return f"{self.title} ({self.language_code})"
