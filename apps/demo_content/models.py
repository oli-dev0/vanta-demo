from django.core.exceptions import ValidationError
from django.db import models
from django.forms.forms import NON_FIELD_ERRORS
from django.utils.text import slugify


class AuthorProfile(models.Model):
    display_name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name


class BlogCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogTag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = "tag"
        verbose_name_plural = "tags"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    author = models.ForeignKey(
        AuthorProfile,
        on_delete=models.PROTECT,
        related_name="posts",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.PROTECT,
        related_name="posts",
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(BlogTag, blank=True, related_name="posts")
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    canonical_site_slug = models.CharField(max_length=40, blank=True)
    cover_image = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["is_published", "published_at"])]
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        if self.pk:
            translation = (
                self.translations.filter(language_code="en").only("title").first()
            )
            if translation:
                return translation.title
        return f"Blog post #{self.pk}"

    def clean(self):
        super().clean()
        if self.canonical_site_slug and self.canonical_site_slug != "vanta_admin":
            raise ValidationError({"canonical_site_slug": "Choose Vanta Admin."})
        if not self.is_published:
            return
        errors = {}
        if not self.published_at:
            errors["published_at"] = "Published posts must have a publication date."
        if not self.canonical_site_slug:
            errors["canonical_site_slug"] = (
                "Published posts must have a canonical site."
            )
        if not self.pk:
            errors.setdefault(NON_FIELD_ERRORS, []).append(
                "Published posts must be assigned to at least one site."
            )
            errors.setdefault(NON_FIELD_ERRORS, []).append(
                "Published posts must have at least one translation."
            )
        else:
            if not self.publications.exists():
                errors.setdefault(NON_FIELD_ERRORS, []).append(
                    "Published posts must be assigned to at least one site."
                )
            elif self.canonical_site_slug not in self.publications.values_list(
                "site_slug", flat=True
            ):
                errors["canonical_site_slug"] = (
                    "Canonical site must match the publication site."
                )
            if not self.translations.exists():
                errors.setdefault(NON_FIELD_ERRORS, []).append(
                    "Published posts must have at least one translation."
                )
        if errors:
            raise ValidationError(errors)


class BlogPostPublication(models.Model):
    post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE, related_name="publications"
    )
    site_slug = models.CharField(max_length=40)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "site_slug"], name="demo_blog_one_publication_per_site"
            )
        ]
        indexes = [models.Index(fields=["site_slug"])]
        ordering = ["site_slug"]

    def __str__(self):
        return f"{self.post_id} on {self.site_slug}"

    def clean(self):
        super().clean()
        if self.site_slug != "vanta_admin":
            raise ValidationError({"site_slug": "Choose Vanta Admin."})


class BlogPostTranslation(models.Model):
    post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE, related_name="translations"
    )
    language_code = models.CharField(max_length=8)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    excerpt = models.TextField()
    body = models.TextField(blank=True)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "language_code"],
                name="demo_blog_one_translation_per_language",
            ),
            models.UniqueConstraint(
                fields=["language_code", "slug"],
                name="demo_blog_unique_slug_per_language",
            ),
        ]
        indexes = [models.Index(fields=["language_code", "slug"])]
        ordering = ["language_code", "title"]

    def __str__(self):
        return f"{self.title} ({self.language_code})"


class BlogImage(models.Model):
    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    name = models.CharField(max_length=200)
    image_url = models.URLField(blank=True, editable=False)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    alt_text = models.CharField(max_length=255, blank=True)
    is_decorative = models.BooleanField(default=False)
    is_feature = models.BooleanField(default=False)
    processing_status = models.CharField(
        max_length=12,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.READY,
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        related_name="created_demo_blog_images",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "image"
        verbose_name_plural = "images"
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.name


class BlogImageComparison(models.Model):
    name = models.CharField(max_length=160)
    before_image = models.ForeignKey(
        BlogImage,
        on_delete=models.PROTECT,
        related_name="comparison_before",
    )
    after_image = models.ForeignKey(
        BlogImage,
        on_delete=models.PROTECT,
        related_name="comparison_after",
    )
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "pk"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.before_image_id and self.before_image_id == self.after_image_id:
            raise ValidationError(
                {"after_image": "Choose a different comparison image."}
            )


class BlogPostRelated(models.Model):
    post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE, related_name="related_links"
    )
    related_post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="incoming_related_links",
    )
    position = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "related article"
        verbose_name_plural = "related articles"
        ordering = ["position", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["post", "related_post"],
                name="demo_blog_one_related_post",
            )
        ]

    def __str__(self):
        return f"{self.post} -> {self.related_post}"

    def clean(self):
        super().clean()
        if self.post_id and self.post_id == self.related_post_id:
            raise ValidationError(
                {"related_post": "An article cannot be related to itself."}
            )
