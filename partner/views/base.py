import datetime
import html
import math
import os
import random
from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from partner.models import *
import datetime
from django.views.decorators.http import require_GET, require_POST
from django.template.loader import render_to_string


@require_GET
def index(request):
    return render(request, 'partner/index.html')


PAGES_DATA = {
    "dashboard": {
        "content": {
            "breadcrumbs": ["Страница", "Dashboard"],
            "title": "Dashboard",
        },
        "html_name": "dashboard.html",
    },
    "promocode": {
        "content": {
            "breadcrumbs": ["Страница", "Промокоды"],
            "title": "Промокоды",
        },
        "html_name": "promocode.html",
    },
    "channel": {
        "content": {
            "breadcrumbs": ["Страница", "Каналы"],
            "title": "Рекламные каналы",
        },
        "html_name": "channel.html",
    },
    "banner": {
        "content": {
            "breadcrumbs": ["Страница", "Баннеры"],
            "title": "Баннеры",
        },
        "html_name": "banner.html",
    },
    "widget": {
        "content": {
            "breadcrumbs": ["Страница", "Виджеты"],
            "title": "Виджеты",
        },
        "html_name": "widget.html",
    },
    "stat": {
        "content": {
            "breadcrumbs": ["Страница", "Статистика"],
            "title": "Статистика",
        },
        "html_name": "stat.html",
    },
    "dev": {
        "content": {
            "breadcrumbs": ["Страница", "DEV"],
            "title": "Страница для разработки",
        },
        "html_name": "dev.html",
    },
    "profile": {
        "content": {
            "breadcrumbs": ["Страница", "Профиль"],
            "title": "Профиль",
        },
        "html_name": "profile.html",
    },
    "partner_link": {
        "content": {
            "breadcrumbs": ["Страница", "Партнерская ссылка"],
            "title": "Партнерская ссылка",
        },
        "html_name": "partner_link.html",
    },
    "referral": {
        "content": {
            "breadcrumbs": ["Страница", "Реферальная программа"],
            "title": "Реферальная программа",
        },
        "html_name": "referral.html",
    },
    "404": {
        "content": {
            "breadcrumbs": ["Страница", "404"],
            "title": "404",
        },
        "html_name": "404.html",
    }
}

def get_channels(partner):
    return {
        channel.id: {
            "id": channel.id,
            "name": channel.name,
            "url": channel.url,
        } for channel in Channel.objects.filter(partner=partner, is_delete=False).order_by("id")
    }

def get_promocodes(partner):
    return {
        promocode.id: {
            "id": promocode.id,
            "code": promocode.code,
            "name": promocode.name,
            "description": promocode.description,
            "cashback": promocode.cashback,
            "hotel_type": promocode.hotel_type,
            "enable": promocode.enable,
            "channel": promocode.channel.id,
        } for promocode in PromoCode.objects.filter(partner=partner, is_delete=False).order_by("-enable", "id")
    }


@require_GET
def get_page(request):
    page = html.escape(request.GET.get("p", "dashboard"))
    content = {}

    page_content = PAGES_DATA.get(page)

    if not page_content:
        page_content = PAGES_DATA.get("404")

    user : User = request.user

    page_content["content"]["user"] = user
    html_name = page_content.get('html_name') if page_content else None

    content["page_id"] = page

    # Получить нужные данные
    if page in ["channel", "widget", "partner_link", "referral"]:
        page_content["content"]["channels"] = get_channels(request.user.partner)
        content["param"] = {"channels": page_content["content"]["channels"]}

    elif page == "promocode":
        page_content["content"]["promocodes"] = get_promocodes(request.user.partner)
        page_content["content"]["channels"] = get_channels(request.user.partner)
        content["param"] = {
            "channels": page_content["content"]["channels"],
            "promocodes": page_content["content"]["promocodes"]
        }

    if page_content:
        content["html"] = render_to_string(
            f"partner/base_content/{html_name}", page_content["content"])
        del page_content["content"]["user"]
        content.update(page_content)

    return JsonResponse(content)


@require_POST
def send_form_post(request):
    content = {}
    form_id = request.POST.get("form_id")
    content["form_id"] = form_id
    if form_id == "promocode.new":
        param = {
            "partner": request.user.partner,
            "name": request.POST.get("name"),
            "description": request.POST.get("description"),
            "cashback": request.POST.get("cashback"),
            "code": request.POST.get("code"),
            "hotel_type": request.POST.get("hotel_type"),
            "channel": Channel.objects.get(id=request.POST.get("channel_id")),
        }

        try:
            if request.POST.get("duration") == "duration_before_day":
                param["promo_code_term"] = datetime.datetime.strptime(
                    request.GET.get("duration"), "%Y-%m-%d")
        except:
            pass

        promocode = PromoCode.objects.create(**param)
        content["result"] = str(promocode)

    if form_id == "promocode.edit":
        param = {
            "name": request.POST.get("name"),
            "description": request.POST.get("description"),
            "cashback": request.POST.get("cashback"),
            "code": request.POST.get("code"),
            "hotel_type": request.POST.get("hotel_type"),
            "channel": Channel.objects.get(id=request.POST.get("channel_id")),
        }

        try:
            if request.POST.get("duration") == "duration_before_day":
                param["promo_code_term"] = datetime.datetime.strptime(
                    request.GET.get("duration"), "%Y-%m-%d")
        except:
            pass

        PromoCode.objects.filter(id=request.POST.get(
            "item_id")).update(**param)

    if form_id == "promocode.remove":
        PromoCode.objects.filter(id=request.POST.get(
            "promocode_id")).update(is_delete=True)

    if form_id == "promocode.switch_enable":
        promocode = PromoCode.objects.filter(
            id=request.POST.get("promocode_id")).first()
        promocode.enable = not promocode.enable
        promocode.save()

    if form_id == "channel.new":
        param = {
            "partner": request.user.partner,
            "name": request.POST.get("name"),
            "url": request.POST.get("url"),
        }

        Channel.objects.create(**param)

    if form_id == "channel.edit":
        param = {
            "name": request.POST.get("name"),
            "url": request.POST.get("url"),
        }

        Channel.objects.filter(id=request.POST.get("item_id")).update(**param)

    return JsonResponse(content)


def random_date(start_date, end_date):
    # Вычисляем количество дней между начальной и конечной датами
    days_between = (end_date - start_date).days

    # Выбираем случайное количество дней, прошедших с начальной даты
    random_days = random.randint(0, days_between)

    # Получаем случайную дату, добавив случайное количество дней к начальной дате
    random_date = start_date + datetime.timedelta(days=random_days)

    # Возвращаем случайную дату
    return random_date


@require_GET
def api_get(request):
    content = {}
    type = request.GET.get("type")
    if type == "kdjq.option":
        kdjq_id = request.GET.get("kdjq_id")
        if kdjq_id == "stat.promocode":
            # if PromoCode.objects.count() <= 1000:
            #     for i in range(0, 1000 - PromoCode.objects.count()):
            #         PromoCode.generate_promo_code_object()


            if False: # reset_booking
                partner = request.user.partner

                status_list : dict = {}

                for booking in Booking.objects.all():
                    booking : Booking

                    booking.param["partner"] = {
                        "promocode": partner.id,
                        "type": random.choice(["promocode", "widget", "partner_link"])
                    }

                    check_in_time : datetime.time = booking.booked_room.category.hotel.check_in_time
                    departure_time : datetime.time = booking.booked_room.category.hotel.departure_time

                    created_at = random_date(datetime.datetime(2023, 11, 1, check_in_time.hour, check_in_time.minute), datetime.datetime(2023, 12, 25, departure_time.hour, departure_time.minute))
                    start_date_time = created_at + datetime.timedelta(days=random.randint(2, 5))
                    end_date_time = start_date_time + datetime.timedelta(days=random.randint(4, 11))

                    booking.created_at = created_at
                    booking.start_date_time = start_date_time
                    booking.end_date_time = end_date_time

                    passed_time_start = start_date_time.replace(tzinfo=datetime.timezone.utc) <= datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
                    passed_time_end = end_date_time.replace(tzinfo=datetime.timezone.utc) <= datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)

                    status = None

                    # Если время бронирования прошло
                    if passed_time_start and passed_time_end:
                        status = random.choice(["left"])

                    # Если время бронирования прошло
                    elif passed_time_start:
                        status = random.choice(["verified", "settled"])

                    else:
                        status = random.choice(["cancelled", "new", "new"])

                    status_list[status] = status_list.get(status, 0) + 1

                    booking.status = status

                    booking.save()



            content["kdjq_option"] = {
                "source": {
                    "table": {
                        "fields": [
                            {
                                "id": "promo_code",
                                "name": "Промокод",
                                "type": "string",
                                "format": "",
                                "starts_with": "",
                                "ends_with": ""
                            },
                            {
                                "id": "channel",
                                "name": "Канал",
                                "type": "string",
                                "format": "",
                                "starts_with": "",
                                "ends_with": ""
                            },
                            {
                                "id": "use",
                                "name": "Использованиия",
                                "type": "int",
                                "format": "number",
                                "starts_with": "",
                                "ends_with": "раз"
                            },
                            {
                                "id": "good_luck",
                                "name": "Успехов",
                                "type": "int",
                                "format": "number",
                                "starts_with": "",
                                "ends_with": ""
                            },
                            {
                                "id": "failure",
                                "name": "Неудач",
                                "type": "int",
                                "format": "number",
                                "starts_with": "",
                                "ends_with": "раз"
                            },
                            {
                                "id": "cancellations",
                                "name": "Отмены брони",
                                "type": "int",
                                "format": "number",
                                "starts_with": "",
                                "ends_with": ""
                            },
                            {
                                "id": "booking_confirmed",
                                "name": "Подтверждено брони",
                                "type": "int",
                                "format": "",
                                "starts_with": "",
                                "ends_with": ""
                            },
                            {
                                "id": "average_income",
                                "name": "Средний доход",
                                "type": "int",
                                "format": "number",
                                "starts_with": "",
                                "ends_with": "₽"
                            },
                            {
                                "id": "total_income",
                                "name": "Общий доход",
                                "type": "int",
                                "format": "number",
                                "starts_with": "",
                                "ends_with": "₽"
                            },
                            {
                                "id": "possible_income",
                                "name": "Возможный доход",
                                "type": "int",
                                "format": "number",
                                "starts_with": "+",
                                "ends_with": "₽"
                            }
                        ],
                        "grouping": {},
                    },
                    "form": {
                        "inputs": {
                            "period": {
                                "label": "Период",
                                "type": "date-range",
                                "placeholder": "",
                                "name": "period"
                            },
                            "grouping": {
                                "label": "Группировка",
                                "type": "select",
                                "name": "grouping",
                                "options": [
                                    {"value": "", "label": "Нет"},
                                    {"value": "channels", "label": "По каналам"},
                                ]
                            },
                            "device_type": {
                                "label": "Тип устройства",
                                "type": "select",
                                "name": "device_type",
                                "options": [
                                    {"value": "", "label": "Все"},
                                    {"value": "phone", "label": "Телефон"},
                                    {"value": "pc", "label": "Компьютер"},
                                    {"value": "tablet", "label": "Планшет"},
                                    {"value": "laptop", "label": "Ноутбук"},
                                    {"value": "smartwatch", "label": "Смарт-часы"},
                                    {"value": "tv", "label": "Телевизор"},
                                    {"value": "game_console",
                                        "label": "Игровая приставка"},
                                    {"value": "camera", "label": "Камера"},
                                    {"value": "audio_player",
                                        "label": "Аудиоплеер"},
                                    {"value": "other", "label": "Другое"}
                                ]
                            },
                            "channel": {
                                "label": "Канал",
                                "type": "select",
                                "name": "channel",
                                "options": [
                                    {"value": "", "label": "Все"},
                                ]
                            },
                            "record_type": {
                                "label": "Тип записи",
                                "type": "select",
                                "name": "record_type",
                                "options": [
                                    {"value": "full", "label": "Полностью"},
                                    {"value": "compact", "label": "Компактная"},
                                    {"value": "exponential",
                                        "label": "Экспоненциальная"}
                                ]
                            },
                            "record_count": {
                                "label": "Количество записей",
                                "type": "select",
                                "name": "record_count",
                                "options": [
                                    {"value": "10", "label": "10"},
                                    {"value": "25", "label": "25"},
                                    {"value": "50", "label": "50"},
                                    {"value": "75", "label": "75"},
                                    {"value": "100", "label": "100"},
                                    {"value": "200", "label": "200"},
                                    {"value": "500", "label": "500"}
                                ]
                            }
                        },
                    },
                    "list": [],
                    "links": {}
                }
            }

            partner = request.user.partner

            links = {}
            grouping = []

            for channel in Channel.objects.filter(partner=partner):
                channel: Channel
                channel_name = channel.name
                channel_url = channel.url
                links[f"channel.{channel.id}"] = {
                    "list": [
                        {"name": "Название", "value": channel_name},
                        {"name": "Ссылка", "value": channel.url},
                        {"name": "Дата создания", "value": channel.created_at},
                        {"name": "Дата изменения", "value": channel.updated_at},
                    ]
                }

                content["kdjq_option"]["source"]["form"]["inputs"]["channel"]["options"].append(
                    {"value": channel.id, "label": channel.name})

                colors = {
                    "vk": {"bg": "#45668e", "color": "#ffffff", "cell": "#c8d7e5"},
                    "google": {"bg": "#4285F4", "color": "#ffffff", "cell": "#c1d5f7"},
                    "yandex": {"bg": "#e32636", "color": "#ffffff", "cell": "#de9ba1"},
                    "facebook": {"bg": "#3b5998", "color": "#ffffff", "cell": "#a1b1d0"},
                    "instagram": {"bg": "#e4405f", "color": "#ffffff", "cell": "#f7b3c5"},
                    "youtube": {"bg": "#ff0000", "color": "#ffffff", "cell": "#f3abab"},
                    "snapchat": {"bg": "#fffc00", "color": "#000000", "cell": "#ffffcc"}
                }

                channel_param = next(
                    (colors[key] for key in colors if key in channel_url), None)

                if channel_param is None:
                    channel_param = {"bg": "#d3d3d3",
                                     "color": "#000000", "cell": "#F2F2F2"}

                grouping.append({"label": channel_name, **channel_param})

            content["kdjq_option"]["source"]["table"]["grouping"]["channels"] = {
                "field": "channel",
                "list": grouping,
            }

            list_data = []

            for promocode in PromoCode.objects.filter(partner=partner):
                links[f"promocode.{promocode.id}"] = {
                    "list": [
                        {"name": "Название", "value": promocode.name, },
                        {"name": "Промокод", "value": promocode.code, },
                        {"name": "Описание", "value": promocode.description, },
                        {"name": "Дата создания", "value": promocode.created_at, },
                        {"name": "Дата изменения", "value": promocode.updated_at, },
                    ]
                }

                promo_code = {"value": promocode.name, "expanded": {
                    "link": f"promocode.{promocode.id}"}}

                channel = {"value": promocode.channel.name, "expanded": {
                    "link": f"channel.{promocode.channel.id}"}}
                use = {"value": random.randint(99, 99999)}
                good_luck = {"value": random.randint(0, use["value"])}

                failure_procent = random.random()

                failure = {
                    "value": use["value"] - good_luck["value"],
                    "expanded": {
                        "list": [
                            {
                                "name": "Не верные условия",
                                "value": "{} раз".format(round((use["value"] - good_luck["value"]) * failure_procent))
                            },
                            {
                                "name": "Срок действия истёк",
                                "value": "{} раз".format((use["value"] - good_luck["value"]) - (round((use["value"] - good_luck["value"]) * failure_procent)))
                            }
                        ]
                    }
                }

                cancellations = {"value": random.randint(0, use["value"])}
                booking_confirmed = {"value": random.randint(0, use["value"])}
                average_income = {"value": random.randint(0, 99999)}
                total_income = {
                    "value": average_income["value"] * booking_confirmed["value"]}
                possible_income = {"value": round(total_income["value"] * 0.3)}

                list_data.append({
                    "promo_code": promo_code, "channel": channel, "use": use, "good_luck": good_luck,
                    "failure": failure, "cancellations": cancellations, "booking_confirmed": booking_confirmed,
                    "average_income": average_income, "total_income": total_income, "possible_income": possible_income,
                })

            content["kdjq_option"]["source"]["list"] = list_data
            content["kdjq_option"]["source"]["links"] = links

    return JsonResponse(content)


@require_GET
def widget_get_code(request):
    type = request.GET.get("type")

    if (type == "directions_for_hotels"):

        context = {}
        context["html"] = render_to_string(
            'partner/widget/directions_for_hotels.html', context)
        return JsonResponse(context)
