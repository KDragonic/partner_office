import datetime
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from utils.models import Place
from .models import Hotel

from django.urls.resolvers import get_resolver


class HotelSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        # hotels_url = []
        # hotels_qs = Hotel.objects.all()
        # for hotel in hotels_qs:
        #   hotels_url.append(hotel.get_absolute_url())

        return Hotel.objects.all()

    def lastmod(self, obj):
        return datetime.datetime.now()


class PlaceSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        places_qs = Place.objects.all()

        return places_qs

    def lastmod(self, obj):
        return datetime.datetime.now()


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        resolver = get_resolver()
        resolver_keys = list(resolver.reverse_dict.keys())
        urls = []
        for key in resolver_keys:
            value = resolver.reverse_dict[key]
            if isinstance(value, tuple):
                # Проверка что некакае параметры не нужно передавать
                if len(value[0][0][1]) == 0:
                    if key not in urls:
                        urls.append(key)

        return urls

    def location(self, item):
        return reverse(item)
