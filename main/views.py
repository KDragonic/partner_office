import datetime
import math
import os
import random
from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from utils.models import Place
from utils.models import Mailing
from hotel.models import Address, Hotel, RCategory, RService
import datetime
import urllib.parse

from brontur.funs import add_meta, generate_password


def home(request):
    from utils.models import Constant
    data = []
    сities = [
        {
            "name": "Москва",
            "slug": "russia/moscow",
            "img": static('img/city/moscow.jpg')
        },
        {
            "name": "Санкт-Петербург",
            "slug": "russia/saint-petersburg",
            "img":  static('img/city/saint_petersburg.jpg')
        },
        {
            "name": "Казань",
            "slug": "russia/kazan",
            "img":  static('img/city/kazan.jpg')
        },
        {
            "name": "Сочи",
            "slug": "russia/sochi",
            "img":  static('img/city/sochi.jpg')
        }
    ]

    for index, city in enumerate(сities):
        address = Address.objects.filter(city=city["name"], hotel__enable=True)
        result = {}
        result["name"] = city["name"]
        result["img"] = city["img"]
        result["slug"] = city["slug"]

        place = Place.objects.filter(slug=city["slug"]).first()
        if place:
            result["count"] = Address.objects.filter(city=place.name).count()
        else:
            result["count"] = 0
        # result["count"] = len(address)
        data.append(result)

    date_1 = datetime.datetime.now() + datetime.timedelta(days=1)
    date_2 = datetime.datetime.now() + datetime.timedelta(days=2)

    search = {
        "date_1": date_1.strftime("%d.%m.%Y"),
        "date_2": date_2.strftime("%d.%m.%Y"),
    }

    settings_options_obj : dict = Constant.get("settings_options", "json")

    content =  {
        "data": data,
        "search": search,
        "heading": settings_options_obj["pages"]["main"]["heading"],
        "subtitle": settings_options_obj["pages"]["main"]["subtitle"],
    }

    content = add_meta(content, title=f"сервис поиска и бронирования отелей по всей России", description=f"Бронирование более 1 340 000 вариантов жилья с кешбэком. Отели, базы отдыха, квартиры, дома в более 315 городах России, Абхазии, Белоруссии. Удобный поиск. Быстрое бронирование. Гарантия заселения. Более 500 тысяч отзывов.")

    if len(request.GET.get("dev_version", "")) > 2:
        return render(request, 'main/home_dev.html', content)

    return render(request, 'main/home.html', content)


def about(request):
    return render(request, 'main/about.html')


def faq(request):
    return render(request, 'main/faq.html')


def privacy_policy(request):
    return render(request, 'main/privacy_policy.html')


def payment_methods(request):
    return render(request, 'main/payment_methods.html')


def contract_offer(request):
    return render(request, 'main/contract_offer.html')


def handler404(request, exception):
    if isinstance(exception, str):
        return render(request, 'error_page.html', {'message': exception, "status": 404}, status=404)

    return render(request, 'error_page.html', {'message': None, "status": 404}, status=404)

def handler403(request, exception):
    if isinstance(exception, str):
        return render(request, 'error_page.html', {'message': exception, "status": 403}, status=403)

    return render(request, 'error_page.html', {'message': None, "status": 403}, status=403)

def ajax_mailing_add(request):
    email = request.POST.get("email")
    if email == "" or len(email) <= 5:
        raise Http404("Invalid request")

    Mailing.add_email(email)
    return JsonResponse({"success": True})



def testing_page(request):
    content = {}
    return JsonResponse(content)