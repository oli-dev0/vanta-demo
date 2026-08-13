from django.conf import settings


def demo_metadata(request):
    del request
    return {
        'demo_canonical_url': 'https://demo.vanta-admin.org/',
        'demo_social_image_url': (
            'https://vanta-admin.org/static/vanta_site/img/social-preview.png'
        ),
        'demo_seed_version': settings.VANTA_DEMO_SEED_VERSION,
    }
