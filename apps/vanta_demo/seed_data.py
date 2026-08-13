from datetime import timedelta
from uuid import NAMESPACE_DNS, uuid5

from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

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

from .services.workspaces import DEMO_ADMIN_USERNAME, seed_activity_timestamp


WORKSPACE_APP_LABELS = (
    "demo_content",
    "demo_projects",
    "demo_newsletter",
    "demo_status",
    "demo_contact",
)


def load_fictional_seed(alias, fixed_now):
    demo_admin = seed_auth(alias, fixed_now)
    blog_records = seed_blog(alias, fixed_now, demo_admin)
    projects = seed_projects(alias, fixed_now)
    newsletter_records = seed_newsletter(alias, fixed_now)
    status_records = seed_status(alias, fixed_now)
    contact_messages = seed_contact(alias, fixed_now)
    seed_admin_history(
        alias,
        fixed_now,
        demo_admin,
        blog_records["posts"][:10]
        + projects[:5]
        + newsletter_records["campaigns"][:5]
        + status_records["incidents"][:5]
        + contact_messages[:5],
    )


def seed_auth(alias, fixed_now):
    user_model = get_user_model()
    demo_admin = user_model.objects.db_manager(alias).create(
        username=DEMO_ADMIN_USERNAME,
        first_name="Demo",
        last_name="Admin",
        email="demo-admin@example.invalid",
        is_active=True,
        is_staff=True,
        is_superuser=True,
        date_joined=fixed_now - timedelta(days=90),
    )
    _set_unusable_password(demo_admin, alias)

    groups = {
        name: Group.objects.db_manager(alias).create(name=name)
        for name in (
            "Content editors",
            "Newsletter managers",
            "Status operators",
            "Support team",
        )
    }
    group_apps = {
        "Content editors": ("demo_content", "demo_projects"),
        "Newsletter managers": ("demo_newsletter",),
        "Status operators": ("demo_status",),
        "Support team": ("demo_contact",),
    }
    for name, app_labels in group_apps.items():
        permissions = Permission.objects.db_manager(alias).filter(
            content_type__app_label__in=app_labels,
            codename__startswith="change_",
        )
        groups[name].permissions.set(permissions)

    first_names = (
        "Alex",
        "Casey",
        "Devon",
        "Emery",
        "Frankie",
        "Harper",
        "Jules",
        "Kai",
        "Morgan",
        "Parker",
        "Riley",
        "Sage",
        "Taylor",
        "Avery",
        "Blair",
        "Cameron",
        "Drew",
        "Ellis",
        "Finley",
        "Gray",
        "Hayden",
        "Jordan",
        "Lane",
    )
    last_names = (
        "River",
        "Field",
        "Lane",
        "Stone",
        "Vale",
        "Wood",
        "North",
        "Winter",
        "Reed",
        "Wells",
        "Hart",
        "Brooks",
        "Quinn",
        "Shaw",
        "Rowan",
        "Lake",
        "Fox",
        "Pine",
        "Clarke",
        "Hale",
        "West",
        "Bell",
        "Grant",
    )
    group_names = tuple(groups)
    for index, (first_name, last_name) in enumerate(
        zip(first_names, last_names, strict=True), start=1
    ):
        username = f"{first_name}-{last_name}".lower()
        user = user_model.objects.db_manager(alias).create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=f"{username}@example.invalid",
            is_active=index % 11 != 0,
            is_staff=index <= 12,
            date_joined=fixed_now - timedelta(days=70 - index),
        )
        _set_unusable_password(user, alias)
        if index <= 16:
            user.groups.add(groups[group_names[(index - 1) % len(group_names)]])
    return demo_admin


def _set_unusable_password(user, alias):
    user.password = "!vanta-demo-unusable"
    user.save(using=alias, update_fields=["password"])


def seed_blog(alias, fixed_now, demo_admin):
    authors = [
        AuthorProfile.objects.using(alias).create(
            display_name=f"Fictional Author {index:02d}",
            slug=f"fictional-author-{index:02d}",
            bio="A fictional editorial profile used only inside the isolated demo.",
            is_active=index != 12,
        )
        for index in range(1, 13)
    ]
    categories = [
        BlogCategory.objects.using(alias).create(
            name=name, slug=f"demo-category-{index:02d}"
        )
        for index, name in enumerate(
            (
                "Guides",
                "Showcases",
                "Design",
                "Development",
                "Operations",
                "Releases",
                "Workflows",
                "News",
            ),
            start=1,
        )
    ]
    tags = [
        BlogTag.objects.using(alias).create(
            name=f"Demo tag {index:02d}", slug=f"demo-tag-{index:02d}"
        )
        for index in range(1, 25)
    ]
    posts = []
    for index in range(1, 61):
        published_at = fixed_now - timedelta(days=index)
        post = BlogPost.objects.using(alias).create(
            author=authors[(index - 1) % len(authors)],
            category=categories[(index - 1) % len(categories)],
            is_published=index % 5 != 0,
            published_at=published_at,
            canonical_site_slug="vanta_admin",
        )
        post.tags.add(tags[(index - 1) % len(tags)], tags[(index + 4) % len(tags)])
        BlogPostPublication.objects.using(alias).create(
            post=post, site_slug="vanta_admin"
        )
        BlogPostTranslation.objects.using(alias).create(
            post=post,
            language_code="en",
            title=f"Fictional workflow note {index:02d}",
            slug=f"fictional-workflow-note-{index:02d}",
            excerpt="A fictional editorial summary created only for the Vanta Admin demo.",
            body="This record demonstrates Django admin editing and contains no production information.",
            seo_title=f"Fictional workflow note {index:02d}",
            seo_description="Fictional content for an isolated Vanta Admin workspace.",
        )
        BlogPost.objects.using(alias).filter(pk=post.pk).update(
            created_at=published_at - timedelta(days=2),
            updated_at=published_at + timedelta(hours=2),
        )
        posts.append(post)

    images = []
    image_statuses = tuple(BlogImage.ProcessingStatus.values)
    for index in range(1, 31):
        image = BlogImage.objects.using(alias).create(
            name=f"Fictional editorial image {index:02d}",
            image_url=f"https://assets.example.invalid/blog/image-{index:02d}.webp",
            width=(480, 800, 1200, 1600)[index % 4],
            height=(320, 533, 800, 1067)[index % 4],
            alt_text=f"Fictional demonstration image {index:02d}",
            is_decorative=index % 9 == 0,
            is_feature=index <= 6,
            processing_status=image_statuses[(index - 1) % len(image_statuses)],
            created_by=demo_admin,
        )
        images.append(image)
    BlogImage.objects.using(alias).update(
        created_at=fixed_now - timedelta(days=3),
        updated_at=fixed_now - timedelta(days=1),
    )

    for index in range(8):
        BlogImageComparison.objects.using(alias).create(
            name=f"Before and after example {index + 1:02d}",
            before_image=images[index * 2],
            after_image=images[index * 2 + 1],
            position=index + 1,
        )
    for index in range(40):
        BlogPostRelated.objects.using(alias).create(
            post=posts[index],
            related_post=posts[(index + 7) % len(posts)],
            position=1,
        )
    return {"posts": posts, "images": images}


def seed_projects(alias, fixed_now):
    names = (
        "Northstar",
        "Bluebird",
        "Cinder",
        "Daybreak",
        "Evergreen",
        "Foundry",
        "Granite",
        "Harbor",
        "Keystone",
        "Lighthouse",
        "Meadow",
        "Northwind",
        "Orbit",
        "Pioneer",
        "Summit",
        "Atlas",
        "Beacon",
        "Copper",
        "Driftwood",
        "Ember",
        "Flint",
        "Grove",
        "Horizon",
        "Juniper",
    )
    projects = []
    for index, name in enumerate(names, start=1):
        project = Project.objects.using(alias).create(
            is_published=index % 4 != 0,
            is_featured=index <= 4,
            sort_order=index,
            repo_url=f"https://example.invalid/projects/{index:02d}",
            live_url=f"https://preview.example.invalid/{index:02d}"
            if index % 3
            else "",
        )
        ProjectTranslation.objects.using(alias).create(
            project=project,
            language_code="en",
            title=name,
            slug=f"fictional-project-{index:02d}",
            summary="A fictional project used to demonstrate lists, forms, and inlines.",
            body="No external service is contacted by this demonstration record.",
            seo_title=f"Fictional project {index:02d}",
            seo_description="Fictional project content for the private Vanta Admin demo.",
        )
        Project.objects.using(alias).filter(pk=project.pk).update(
            created_at=fixed_now - timedelta(days=60 - index),
            updated_at=fixed_now - timedelta(days=index),
        )
        projects.append(project)
    return projects


def seed_newsletter(alias, fixed_now):
    sites = [
        NewsletterSite.objects.using(alias).create(
            site_slug=slug,
            name=name,
            domain=f"{slug}.example.invalid",
            sender_name=f"{name} Editorial",
            sender_email=f"newsletter@{slug}.example.invalid",
            is_active=index != 3,
            double_opt_in=index != 2,
        )
        for index, (slug, name) in enumerate(
            (
                ("vanta-admin", "Vanta Admin"),
                ("northstar", "Northstar Studio"),
                ("field-notes", "Field Notes"),
            ),
            start=1,
        )
    ]
    subscriptions = []
    subscription_statuses = tuple(Subscription.Status.values)
    for index in range(1, 81):
        status = subscription_statuses[(index - 1) % len(subscription_statuses)]
        occurred_at = fixed_now - timedelta(days=index % 35, hours=index % 8)
        subscription = Subscription.objects.using(alias).create(
            public_id=uuid5(NAMESPACE_DNS, f"vanta-demo-subscription-{index}"),
            newsletter_site=sites[(index - 1) % len(sites)],
            email=f"subscriber-{index:03d}@example.invalid",
            status=status,
            source=Subscription.Source.ADMIN
            if index % 4 == 0
            else Subscription.Source.PUBLIC_FORM,
            confirmed_at=occurred_at if status != Subscription.Status.PENDING else None,
            activated_at=occurred_at if status == Subscription.Status.ACTIVE else None,
            unsubscribed_at=occurred_at
            if status == Subscription.Status.UNSUBSCRIBED
            else None,
        )
        subscriptions.append(subscription)
    Subscription.objects.using(alias).update(
        created_at=fixed_now - timedelta(days=20),
        updated_at=fixed_now - timedelta(days=1),
    )

    images = [
        NewsletterImage.objects.using(alias).create(
            newsletter_site=sites[(index - 1) % len(sites)],
            name=f"Campaign image {index:02d}",
            image_url=f"https://assets.example.invalid/newsletter/image-{index:02d}.webp",
            width=1200,
            height=630,
            alt_text=f"Fictional campaign artwork {index:02d}",
        )
        for index in range(1, 19)
    ]
    NewsletterImage.objects.using(alias).update(
        created_at=fixed_now - timedelta(days=10)
    )

    campaigns = []
    campaign_statuses = tuple(Campaign.Status.values)
    for index in range(1, 25):
        status = campaign_statuses[(index - 1) % len(campaign_statuses)]
        campaign = Campaign.objects.using(alias).create(
            newsletter_site=sites[(index - 1) % len(sites)],
            featured_image=images[(index - 1) % len(images)],
            subject=f"Fictional product update {index:02d}",
            html_content="<p>Fictional campaign content for the isolated demo.</p>",
            text_content="Fictional campaign content for the isolated demo.",
            status=status,
            scheduled_for=fixed_now + timedelta(days=index)
            if status == Campaign.Status.SCHEDULED
            else None,
            completed_at=fixed_now - timedelta(days=index)
            if status.startswith("completed")
            else None,
            target_count=35 + index,
            last_error="Demonstration provider error."
            if status == Campaign.Status.COMPLETED_WITH_FAILURES
            else "",
        )
        campaigns.append(campaign)
    Campaign.objects.using(alias).update(
        created_at=fixed_now - timedelta(days=12),
        updated_at=fixed_now - timedelta(hours=6),
    )

    delivery_statuses = tuple(CampaignDelivery.Status.values)
    for index in range(1, 81):
        status = delivery_statuses[(index - 1) % len(delivery_statuses)]
        event_time = fixed_now - timedelta(days=index % 10, minutes=index)
        CampaignDelivery.objects.using(alias).create(
            campaign=campaigns[(index - 1) % len(campaigns)],
            subscription=subscriptions[index - 1],
            status=status,
            queued_at=event_time if status != CampaignDelivery.Status.PENDING else None,
            sent_at=event_time if status == CampaignDelivery.Status.SENT else None,
            failed_at=event_time if status == CampaignDelivery.Status.FAILED else None,
            skipped_at=event_time
            if status == CampaignDelivery.Status.SKIPPED_UNSUBSCRIBED
            else None,
            last_error_summary="Fictional delivery failure for demonstration."
            if status == CampaignDelivery.Status.FAILED
            else "",
        )
    CampaignDelivery.objects.using(alias).update(
        created_at=fixed_now - timedelta(days=8),
        updated_at=fixed_now - timedelta(hours=2),
    )
    return {"campaigns": campaigns, "subscriptions": subscriptions}


def seed_status(alias, fixed_now):
    pages = [
        StatusPage.objects.using(alias).create(
            site_slug=slug,
            slug="main",
            title=f"{name} service status",
            description="Fictional service availability for the isolated demo.",
            is_visible=index != 3,
        )
        for index, (slug, name) in enumerate(
            (
                ("vanta-admin", "Vanta Admin"),
                ("northstar", "Northstar"),
                ("field-notes", "Field Notes"),
            ),
            start=1,
        )
    ]
    monitors = [
        KumaMonitor.objects.using(alias).create(
            name=f"Demo service {index:02d}",
            monitor_key=f"demo-service-{index:02d}",
            monitor_type=("HTTP", "Ping", "Keyword")[index % 3],
            state=tuple(KumaMonitor.State.values)[
                (index - 1) % len(KumaMonitor.State.values)
            ],
            is_available=index != 12,
        )
        for index in range(1, 13)
    ]
    KumaMonitor.objects.using(alias).update(
        updated_at=fixed_now - timedelta(minutes=15)
    )
    services = []
    for index in range(18):
        page = pages[index % len(pages)]
        monitor = monitors[
            (index // len(pages) + (index % len(pages) * 4)) % len(monitors)
        ]
        service = StatusPageService.objects.using(alias).create(
            status_page=page,
            monitor=monitor,
            display_name=f"{monitor.name} on {page.site_slug}",
            position=index // len(pages),
            is_visible=index % 7 != 0,
        )
        services.append(service)

    incidents = []
    phases = tuple(Incident.Phase.values)
    severities = tuple(Incident.Severity.values)
    for index in range(1, 25):
        phase = phases[(index - 1) % len(phases)]
        started_at = fixed_now - timedelta(days=index, hours=index % 6)
        incident = Incident.objects.using(alias).create(
            status_page=pages[(index - 1) % len(pages)],
            title=f"Fictional service incident {index:02d}",
            severity=severities[(index - 1) % len(severities)],
            phase=phase,
            started_at=started_at,
            resolved_at=started_at + timedelta(hours=2)
            if phase == Incident.Phase.RESOLVED
            else None,
            summary="A fictional incident created to demonstrate status administration.",
        )
        incident.affected_services.add(services[(index - 1) % len(services)])
        incidents.append(incident)
        for update_index in range(2):
            IncidentUpdate.objects.using(alias).create(
                incident=incident,
                phase=phase if update_index else Incident.Phase.INVESTIGATING,
                message=f"Fictional incident update {update_index + 1}.",
                published_at=started_at + timedelta(minutes=30 * update_index),
            )
    Incident.objects.using(alias).update(
        created_at=fixed_now - timedelta(days=30),
        updated_at=fixed_now - timedelta(hours=1),
    )
    IncidentUpdate.objects.using(alias).update(
        created_at=fixed_now - timedelta(days=20)
    )
    StatusPage.objects.using(alias).update(
        created_at=fixed_now - timedelta(days=60),
        updated_at=fixed_now - timedelta(days=2),
    )
    return {"incidents": incidents, "monitors": monitors}


def seed_contact(alias, fixed_now):
    messages = []
    for index in range(1, 61):
        message = ContactMessage.objects.using(alias).create(
            name=f"Fictional Visitor {index:02d}",
            email=f"visitor-{index:03d}@example.invalid",
            subject=f"Demonstration enquiry {index:02d}",
            message="This fictional contact message contains no customer or production information.",
            is_read=index % 3 != 0,
        )
        ContactMessage.objects.using(alias).filter(pk=message.pk).update(
            created_at=fixed_now - timedelta(days=index % 30, minutes=index),
        )
        messages.append(message)
    return messages


def seed_admin_history(alias, fixed_now, demo_admin, objects):
    for index, obj in enumerate(objects[:30]):
        content_type = ContentType.objects.db_manager(alias).get_for_model(obj)
        LogEntry.objects.using(alias).create(
            action_time=seed_activity_timestamp(fixed_now, index),
            user_id=demo_admin.pk,
            content_type_id=content_type.pk,
            object_id=str(obj.pk),
            object_repr=str(obj)[:200],
            action_flag=ADDITION,
            change_message="Seeded fictional demo record.",
        )
