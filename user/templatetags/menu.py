from urllib.parse import parse_qs, urlparse
from django import template
from user.models import User
from django.urls import resolve
from brontur import settings
from hotel.models import Booking, Hotel, RCategory
from django.urls import reverse
import re

register = template.Library()

BREADCRUMB_TEMPLATES = [
    (r'^/register/$', 'register', [["Регистрация", None]]),
    (r'^/login/$', 'login', [["Вход", None]]),
    (r'^/logout/$', 'logout', [["Выход", None]]),
    (r'^/profile/$', 'profile', [["Профиль", None]]),
    (r'^/profile/booking/$', 'profile_booking', [["Профиль", "/profile/"], ["Брони", None]]),
    (r'^/profile/balance/$', 'profile_balance', [["Профиль", "/profile/"], ["Баланс", None]]),
    (r'^/profile/favourites/$', 'profile_favourites', [["Профиль", "/profile/"], ["Избранное", None]]),
    (r'^/profile/notifications/$', 'profile_notifications', [["Профиль", "/profile/"], ["Уведомления", None]]),
    (r'^/profile/hotel/$', 'profile_hotel', [["Профиль", "/profile/"], ["Отель", None]]),
    (r'^/profile/hotel/rooms/$', 'profile_hotel_rcs', [["Профиль", "/profile/"], ["Отель", "/profile/hotel/"], ["Номера", None]]),
    (r'^/profile/hotel/booking/$', 'profile_hotel_booking', [["Профиль", "/profile/"], ["Отель", "/profile/hotel/"], ["Брони", None]]),
    (r'^/profile/hotel/chat/$', 'profile_hotel_chat', [["Профиль", "/profile/"], ["Отель", "/profile/hotel/"], ["Чат", None]]),
    (r'^/profile/chat/$', 'profile_chat', [["Профиль", "/profile/"], ["Чат", None]]),
    (r'^/profile/hotel/price_calendar/$', 'price_calendar', [["Профиль", "/profile/"], ["Отель", "/profile/hotel/"], ["Календарь цен", None]]),

    (r'^/hotel/register/$', 'hotel_register', [["Профиль", "/profile/"], ["Отель", None], ["Регистрация", None]]),
    (r'^/hotel/[0-9]+/$', 'hotel_detailed', [["Главная", "/"], ["<Отель>", None]]),
    # (r'^/hotel/room/to_book/$', 'hotel_room_booking', [["Главная", "/"], ["<Отель>", "/hotel/<id>/"], ["Бронирование", None]]),
]


@register.inclusion_tag('template/bread_crumb.html', takes_context=True)
def bread_crumb(context):
    url: str = context.request.path



    isProfile = url.find("/profile/") > -1

    for regex, name, bc in BREADCRUMB_TEMPLATES:

        if re.match(regex, url):
            if name == "hotel_detailed":
                param = re.findall(r'^/hotel/[0-9]+/$', url)
                rc = Hotel.objects.get(id=int(url.split('/')[2]))
                sid = context.request.GET.get("sid")
                return {'breadcrumbs': [["Главная", f"/"], [f"{rc.name}", None]], "isProfile": isProfile}

            return {'breadcrumbs': bc, "isProfile": isProfile}
    return {'breadcrumbs': [], "isProfile": isProfile}


@register.inclusion_tag('template/tabs_menu.html', takes_context=True)
def tabs(context):
    user : User = context.request.user.normal()
    path = context.request.path
    hotels = Hotel.objects.filter(owner=user, is_delete=False)
    user_owner_hotel = hotels.exists()
    name = user.email

    list_url_1 = ["/profile/hotel/", "/profile/hotel/rcs/",
                  "/profile/hotel/rooms/", "/profile/hotel/price_calendar/"]
    list_url_2 = ['/profile/hotel/booking/',
                  '/profile/hotel/booking/chess/', '/profile/hotel/chat/']
    list_url_3 = ['/profile/hotel/balance/', '/profile/hotel/boost/']

    if hotels.exists():
        if not context.request.session.get('hotel'):
            context.request.session["hotel"] = hotels.first().id
            context.request.session.modified = True

    count_new_booking = 0

    hotels_result = []
    if len(hotels) != 0:
        select_hotel = context.request.session.get('hotel')
        if select_hotel:
            if hotels.exists():
                for hotel in hotels:

                    hotels_result.append({
                        "id": hotel.id,
                        "name": hotel.name,
                        "select": hotel.id == select_hotel,
                    })

        count_new_booking = len(Booking.objects.filter(booked_room__category__hotel__id=select_hotel, status="new"))

    content = {
        "name": name,
        "count_new_booking": count_new_booking,
        "user_owner_hotel": user_owner_hotel,
        "is_admin": user.is_superuser or user.user_type in ["moder", "admin", "owner"],
        "user_type": user.user_type,
        "supermoderator": "supermoderator" in user.additional_info["permission"] if user.additional_info.get("permission") else False,
        "path": path,
        # Строка ` "view_name":solve(path).view_name` использует функцию `resolve()` Django для
        # получения имени представления, связанного с текущим URL-путем. Функция resolve() принимает
        # URL-путь в качестве входных данных и возвращает объект ResolverMatch, который содержит
        # информацию о разрешенном представлении. Атрибут view_name объекта ResolverMatch представляет
        # имя разрешенного представления. Эта информация затем включается в словарь `content`,
        # возвращаемый тегом шаблона `tabs()`.
        "view_name": resolve(path).view_name,
        "list_url_1": list_url_1,
        "list_url_2": list_url_2,
        "list_url_3": list_url_3,
        "hotels": hotels_result,
    }

    return content


staff_post_list = {
    "owner": "Разработчик",
    "admin": "Администратор",
    "moder": "Модератор",
    "hotel": "Отель",
    "client": "Клиент",
}

@register.inclusion_tag('template/amenu_sidebar.html', takes_context=True)
def amenu_sidebar(context):
    user : User = context.request.user.normal()
    path = context.request.path
    name = user.get_FIO()
    staff_post = {
        "code": user.user_type,
        "label": staff_post_list[user.user_type]
    }

    content = {
        "name": name,
        "staff_post": staff_post,
        "is_admin": user.is_superuser or user.user_type in ["moder", "admin", "owner"],
        "user_type": user.user_type,
        "supermoderator": "supermoderator" in user.additional_info["permission"] if user.additional_info.get("permission") else False,
        "path": path,
        "view_name": resolve(path).view_name,
    }

    return content

@register.inclusion_tag('template/hotel_shift_tab.html', takes_context=True)
def hotel_shift_tab(context):
    user : User = context.request.user.normal()
    path = context.request.path
    hotels = Hotel.objects.filter(owner=user)
    user_owner_hotel = hotels.exists()

    if hotels.exists():
        if not context.request.session.get('hotel'):
            context.request.session["hotel"] = hotels.first().id
            context.request.session.modified = True

    hotels_result = []
    if len(hotels) != 0:
        select_hotel = context.request.session.get('hotel')
        if select_hotel:
            if hotels.exists():
                for hotel in hotels:

                    hotels_result.append({
                        "id": hotel.id,
                        "name": hotel.name,
                        "select": hotel.id == select_hotel,
                    })

    content = {
        "user_owner_hotel": user_owner_hotel,
        "is_admin": user.is_superuser or user.user_type in ["moder", "admin", "owner"],
        "path": path,
        "hotels": hotels_result,
    }

    return content



@register.inclusion_tag('user/v2/menu-lk.html', takes_context=True)
def meny_lk(context):
    user : User = context.request.user.normal()

    url_name = resolve(context.request.path).url_name

    if user.hotels.all().first():
        if user.user_type != "hotel":
            user.user_type = "hotel"
            user.save()
    else:
        if user.user_type == "hotel":
            user.user_type = "client"
            user.save()


    content = {
        "user": {
            "user_type": user.user_type,
        },
        "menu_lk_active": url_name,
    }

    return content

