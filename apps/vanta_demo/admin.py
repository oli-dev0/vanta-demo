from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from apps.demo_contact.models import ContactMessage
from apps.demo_content.models import (
    AuthorProfile,
    BlogCategory,
    BlogImage,
    BlogImageComparison,
    BlogPost,
    BlogPostPublication,
    BlogPostRelated,
    BlogPostTranslation,
    BlogTag,
)
from apps.demo_newsletter.models import (
    Campaign,
    CampaignDelivery,
    NewsletterImage,
    NewsletterSite,
    Subscription,
)
from apps.demo_projects.models import Project, ProjectTranslation
from apps.demo_status.models import (
    Incident,
    IncidentUpdate,
    KumaMonitor,
    StatusPage,
    StatusPageService,
)

from .context import get_workspace_alias
from .forms import (
    DemoBlogPostForm,
    DemoBlogPostPublicationForm,
    DemoBlogPostTranslationForm,
    DemoNewsletterImageForm,
    DemoProjectForm,
    DemoProjectTranslationForm,
    DemoUserForm,
    BoundedModelForm,
)
from .services.workspaces import DEMO_ADMIN_USERNAME


class DemoAdminSite(AdminSite):
    site_header = _("Vanta Admin Demo")
    site_title = _("Vanta Admin Demo")
    index_title = _("Demo Admin")
    site_url = "/"
    index_template = "vanta_demo/admin/index.html"

    def has_permission(self, request):
        return bool(
            get_workspace_alias() and request.user.is_active and request.user.is_staff
        )

    def login(self, request, extra_context=None):
        del extra_context
        return redirect("vanta_demo:overview")

    def logout(self, request, extra_context=None):
        del extra_context
        return redirect("vanta_demo:overview")

    def password_change(self, request, extra_context=None):
        del extra_context
        return redirect("vanta_demo:reset")

    def password_change_done(self, request, extra_context=None):
        del extra_context
        return redirect("vanta_demo:reset")


class DemoAdminMixin:
    def has_add_permission(self, request):
        if not super().has_add_permission(request):
            return False
        return self.get_queryset(request).count() < settings.VANTA_DEMO_MODEL_RECORD_CAP

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        kwargs.setdefault("using", get_workspace_alias())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        kwargs.setdefault("using", get_workspace_alias())
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def message_user(
        self, request, message, level=messages.INFO, extra_tags="", fail_silently=False
    ):
        message_text = str(message)
        if level == messages.SUCCESS:
            if "was added successfully" in message_text:
                message = _("The record was added to this demo workspace.")
            elif "was changed successfully" in message_text:
                message = _("Your changes were saved in this demo workspace.")
            elif "was deleted successfully" in message_text:
                message = _("The record was deleted from this demo workspace.")
        return super().message_user(request, message, level, extra_tags, fail_silently)


class DemoInlineMixin:
    extra = 0
    max_num = 20

    def get_formset(self, request, obj=None, **kwargs):
        kwargs.setdefault("validate_max", True)
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        kwargs.setdefault("using", get_workspace_alias())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class BlogTranslationInline(DemoInlineMixin, admin.StackedInline):
    model = BlogPostTranslation
    form = DemoBlogPostTranslationForm
    classes = ("demo-blog-translations",)


class BlogPublicationInline(DemoInlineMixin, admin.TabularInline):
    model = BlogPostPublication
    form = DemoBlogPostPublicationForm


class ProjectTranslationInline(DemoInlineMixin, admin.StackedInline):
    model = ProjectTranslation
    form = DemoProjectTranslationForm
    classes = ("demo-project-translations",)


class DemoUserAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = DemoUserForm
    fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_staff",
        "groups",
    )
    list_display = ("username", "first_name", "last_name", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "groups")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
    list_per_page = 10
    filter_horizontal = ("groups",)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.username == DEMO_ADMIN_USERNAME:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.set_unusable_password()
        super().save_model(request, obj, form, change)


class DemoGroupAdmin(DemoAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)


class DemoBlogPostAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = DemoBlogPostForm
    inlines = (BlogPublicationInline, BlogTranslationInline)
    list_display = (
        "title",
        "author",
        "category",
        "canonical_site_slug",
        "is_published",
        "published_at",
    )
    list_filter = ("is_published", "canonical_site_slug", "category", "tags")
    search_fields = ("translations__title", "translations__slug")
    ordering = ("-published_at", "-updated_at")
    list_per_page = 10
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "author",
                    "category",
                    "tags",
                    "is_published",
                    "published_at",
                    "canonical_site_slug",
                )
            },
        ),
    )

    @admin.display(description=_("Title"), ordering="translations__title")
    def title(self, obj):
        translation = obj.translations.filter(language_code="en").first()
        return translation.title if translation else _("Untitled article")


class DemoProjectAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = DemoProjectForm
    inlines = (ProjectTranslationInline,)
    list_display = ("project_name", "is_published", "is_featured", "id", "updated_at")
    list_filter = ("is_published", "is_featured")
    search_fields = ("translations__title", "translations__slug")
    ordering = ("sort_order", "-updated_at")
    list_per_page = 10
    fieldsets = (
        (None, {"fields": ("is_published", "is_featured", "sort_order")}),
        (_("Demonstration links"), {"fields": ("repo_url", "live_url")}),
    )

    @admin.display(description=_("Name"), ordering="translations__title")
    def project_name(self, obj):
        translation = obj.translations.filter(language_code="en").first()
        return translation.title if translation else _("Unnamed project")


class DemoAuthorAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = ("display_name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("display_name", "slug", "bio")
    ordering = ("display_name",)


class DemoCategoryAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    ordering = ("name",)


class DemoTagAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    ordering = ("name",)


class DemoBlogImageAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = (
        "name",
        "processing_status",
        "width",
        "height",
        "is_feature",
        "created_at",
    )
    list_filter = ("processing_status", "is_feature", "is_decorative")
    search_fields = ("name", "alt_text")
    readonly_fields = ("image_url", "created_at", "updated_at")
    list_per_page = 10


class DemoBlogImageComparisonAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = ("name", "before_image", "after_image", "position")
    search_fields = ("name",)
    ordering = ("position",)


class DemoBlogPostRelatedAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = ("post", "related_post", "position")
    ordering = ("post", "position")
    list_per_page = 10


class DemoNewsletterSiteAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = (
        "name",
        "site_slug",
        "domain",
        "sender_email",
        "is_active",
        "double_opt_in",
    )
    list_filter = ("is_active", "double_opt_in")
    search_fields = ("name", "site_slug", "domain", "sender_email")
    ordering = ("name",)


class DemoSubscriptionAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = (
        "email",
        "newsletter_site",
        "status",
        "source",
        "created_at",
        "activated_at",
    )
    list_filter = ("newsletter_site", "status", "source")
    search_fields = ("email",)
    ordering = ("-created_at", "-pk")
    list_per_page = 10


class DemoNewsletterImageAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = DemoNewsletterImageForm
    list_display = ("name", "newsletter_site", "width", "height", "created_at")
    list_filter = ("newsletter_site",)
    search_fields = ("name", "alt_text")
    readonly_fields = ("image_url", "created_at")
    list_per_page = 10


class DemoCampaignAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = (
        "subject",
        "newsletter_site",
        "status",
        "scheduled_for",
        "target_count",
        "created_at",
    )
    list_filter = ("newsletter_site", "status")
    search_fields = ("subject", "text_content")
    ordering = ("-created_at", "-pk")
    list_per_page = 10


class DemoCampaignDeliveryAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = ("campaign", "subscription", "status", "sent_at", "failed_at")
    list_filter = ("status", "campaign__newsletter_site")
    search_fields = ("campaign__subject", "subscription__email", "last_error_summary")
    ordering = ("-created_at", "-pk")
    list_per_page = 10


class StatusPageServiceInline(DemoInlineMixin, admin.TabularInline):
    model = StatusPageService
    form = BoundedModelForm


class IncidentUpdateInline(DemoInlineMixin, admin.StackedInline):
    model = IncidentUpdate
    form = BoundedModelForm


class DemoStatusPageAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    inlines = (StatusPageServiceInline,)
    list_display = ("title", "site_slug", "slug", "is_visible", "updated_at")
    list_filter = ("site_slug", "is_visible")
    search_fields = ("title", "description", "slug")


class DemoKumaMonitorAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = (
        "name",
        "monitor_key",
        "monitor_type",
        "state",
        "is_available",
        "updated_at",
    )
    list_filter = ("state", "is_available", "monitor_type")
    search_fields = ("name", "monitor_key", "monitor_type")
    list_per_page = 10


class DemoIncidentAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    inlines = (IncidentUpdateInline,)
    list_display = (
        "title",
        "status_page",
        "severity",
        "phase",
        "started_at",
        "resolved_at",
    )
    list_filter = ("severity", "phase", "status_page__site_slug")
    search_fields = ("title", "summary")
    ordering = ("-started_at",)
    list_per_page = 10
    filter_horizontal = ("affected_services",)


class DemoContactMessageAdmin(DemoAdminMixin, admin.ModelAdmin):
    form = BoundedModelForm
    list_display = ("name", "email", "subject", "created_at", "is_read")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "subject")
    ordering = ("-created_at",)
    list_per_page = 10
    actions = ("mark_as_read",)

    @admin.action(description=_("Mark selected messages as read"))
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(
            request,
            _("%(count)d message(s) marked as read.") % {"count": updated},
            messages.SUCCESS,
        )


demo_admin_site = DemoAdminSite(name="admin")
demo_admin_site.register(get_user_model(), DemoUserAdmin)
demo_admin_site.register(Group, DemoGroupAdmin)
demo_admin_site.register(AuthorProfile, DemoAuthorAdmin)
demo_admin_site.register(BlogPost, DemoBlogPostAdmin)
demo_admin_site.register(BlogCategory, DemoCategoryAdmin)
demo_admin_site.register(BlogTag, DemoTagAdmin)
demo_admin_site.register(BlogImage, DemoBlogImageAdmin)
demo_admin_site.register(BlogImageComparison, DemoBlogImageComparisonAdmin)
demo_admin_site.register(BlogPostRelated, DemoBlogPostRelatedAdmin)
demo_admin_site.register(Project, DemoProjectAdmin)
demo_admin_site.register(NewsletterSite, DemoNewsletterSiteAdmin)
demo_admin_site.register(Subscription, DemoSubscriptionAdmin)
demo_admin_site.register(NewsletterImage, DemoNewsletterImageAdmin)
demo_admin_site.register(Campaign, DemoCampaignAdmin)
demo_admin_site.register(CampaignDelivery, DemoCampaignDeliveryAdmin)
demo_admin_site.register(StatusPage, DemoStatusPageAdmin)
demo_admin_site.register(KumaMonitor, DemoKumaMonitorAdmin)
demo_admin_site.register(Incident, DemoIncidentAdmin)
demo_admin_site.register(ContactMessage, DemoContactMessageAdmin)
