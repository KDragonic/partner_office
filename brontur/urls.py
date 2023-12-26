from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from hotel.sitemaps import *


sitemaps = {
    'hotels': HotelSitemap,
    'place': PlaceSitemap,
    "static": StaticViewSitemap,
}


urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # path("__debug__/", include("debug_toolbar.urls")),
    path('tinymce/', include('tinymce.urls')),
    path('', include('main.urls')),
    path('', include('hotel.urls')),
    path('', include('user.urls')),
    path('partner/', include('partner.urls')),
    path('', include('chat.urls')),
    path('', include('utils.urls')),
    path('', include('bot.urls')),
    path('techsupport/', include('technical_support.urls')),
    path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = 'main.views.handler404'
handler403 = 'main.views.handler403'
