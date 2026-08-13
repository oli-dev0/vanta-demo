from django.urls import path

from . import views


urlpatterns = [
    path('', views.overview, name='overview'),
    path('start/', views.start, name='start'),
    path('reset/', views.reset, name='reset'),
    path('expired/', views.expired, name='expired'),
    path('robots.txt', views.robots_txt, name='robots'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap'),
    path('healthz/', views.healthz, name='healthz'),
    path('readyz/', views.readyz, name='readyz'),
    path('favicon.ico', views.favicon, name='favicon'),
]
