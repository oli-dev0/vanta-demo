import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("demo_content", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthorProfile",
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
                ("display_name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=140, unique=True)),
                ("bio", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["display_name"],
            },
        ),
        migrations.CreateModel(
            name="BlogCategory",
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
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=140, unique=True)),
            ],
            options={
                "verbose_name": "category",
                "verbose_name_plural": "categories",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="BlogImage",
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
                ("name", models.CharField(max_length=200)),
                ("image_url", models.URLField(blank=True, editable=False)),
                ("width", models.PositiveIntegerField(default=0)),
                ("height", models.PositiveIntegerField(default=0)),
                ("alt_text", models.CharField(blank=True, max_length=255)),
                ("is_decorative", models.BooleanField(default=False)),
                ("is_feature", models.BooleanField(default=False)),
                (
                    "processing_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("ready", "Ready"),
                            ("failed", "Failed"),
                        ],
                        default="ready",
                        max_length=12,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "image",
                "verbose_name_plural": "images",
                "ordering": ["-created_at", "-pk"],
            },
        ),
        migrations.CreateModel(
            name="BlogImageComparison",
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
                ("name", models.CharField(max_length=160)),
                ("position", models.PositiveIntegerField(default=0)),
            ],
            options={
                "ordering": ["position", "pk"],
            },
        ),
        migrations.CreateModel(
            name="BlogPostRelated",
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
                ("position", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "related article",
                "verbose_name_plural": "related articles",
                "ordering": ["position", "pk"],
            },
        ),
        migrations.CreateModel(
            name="BlogTag",
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
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=100, unique=True)),
            ],
            options={
                "verbose_name": "tag",
                "verbose_name_plural": "tags",
                "ordering": ["name"],
            },
        ),
        migrations.RemoveIndex(
            model_name="project",
            name="demo_conten_is_publ_0dc71a_idx",
        ),
        migrations.RemoveIndex(
            model_name="projecttranslation",
            name="demo_conten_languag_24b806_idx",
        ),
        migrations.RemoveConstraint(
            model_name="projecttranslation",
            name="demo_projects_one_translation_per_language",
        ),
        migrations.RemoveConstraint(
            model_name="projecttranslation",
            name="demo_projects_unique_slug_per_language",
        ),
        migrations.AddField(
            model_name="blogpost",
            name="author",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="posts",
                to="demo_content.authorprofile",
            ),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="posts",
                to="demo_content.blogcategory",
            ),
        ),
        migrations.AddField(
            model_name="blogimage",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_demo_blog_images",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="blogimagecomparison",
            name="after_image",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="comparison_after",
                to="demo_content.blogimage",
            ),
        ),
        migrations.AddField(
            model_name="blogimagecomparison",
            name="before_image",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="comparison_before",
                to="demo_content.blogimage",
            ),
        ),
        migrations.AddField(
            model_name="blogpostrelated",
            name="post",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="related_links",
                to="demo_content.blogpost",
            ),
        ),
        migrations.AddField(
            model_name="blogpostrelated",
            name="related_post",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="incoming_related_links",
                to="demo_content.blogpost",
            ),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="tags",
            field=models.ManyToManyField(
                blank=True, related_name="posts", to="demo_content.blogtag"
            ),
        ),
        migrations.RemoveField(
            model_name="projecttranslation",
            name="project",
        ),
        migrations.AddConstraint(
            model_name="blogpostrelated",
            constraint=models.UniqueConstraint(
                fields=("post", "related_post"), name="demo_blog_one_related_post"
            ),
        ),
        migrations.DeleteModel(
            name="Project",
        ),
        migrations.DeleteModel(
            name="ProjectTranslation",
        ),
    ]
