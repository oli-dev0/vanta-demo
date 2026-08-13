from django.urls import include, path

from apps.vanta_demo.admin import demo_admin_site
from apps.vanta_demo import views


urlpatterns = [
    path('', include(('apps.vanta_demo.urls', 'vanta_demo'), namespace='vanta_demo')),
    path('admin/', demo_admin_site.urls),
]

handler400 = views.bad_request
handler403 = views.permission_denied
handler404 = views.page_not_found
handler500 = views.server_error

