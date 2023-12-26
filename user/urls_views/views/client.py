import datetime
import json
import re
from django.http import HttpRequest, JsonResponse

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.contrib import messages
from chat.models import Chat
from brontur.funs import *

# from hotel.forms import HotelUpdateForm, RoomCreateForm, RoomUpdateForm

from user.models import Notification, User, Bonus_rubles as UBRuble, Companion as UCompanion, FinancialOperation
from hotel.models import Hotel, Booking, Favourite, RCategory
from utils.models import Img


@login_required
def page_profile(request):
    user : User = request.user
    ucard = UCard.objects.filter(user=user)
    cards = list(ucard.values())
    for index in range(len(cards)):
        text = cards[index]["number"]
        cards[index]["number"] = f"{text[0:3]} {text[4:7]} {text[8:11]} {text[12:15]}"

    travel_companions = UCompanion.objects.filter(user=user)

    choices = {}
    checkeds = {}

    choices["gender"] = json.dumps([
        ['Мужской', 'Мужской'],
        ['Женский', 'Женский']
    ])

    checkeds["gender"] = json.dumps([
        user.gender
    ])

    not_verification_phone_1 = not (user.active_phone and user.phone != "" and user.phone != None and len(user.phone) > 4)
    not_verification_phone_2 = not (user.active_phone_2 and user.phone_2 != "" and user.phone_2 != None and len(user.phone_2) > 4)

    not_verification_email =  not (user.active_email and user.email != "" and user.email != None and len(user.email) > 4)

    if not user.token_telegram:
        user.token_telegram = "auth_code_" + generate_password(10)
        user.save()

    token_telegram = user.token_telegram
    if re.match('auth_code', user.token_telegram):
        telegram_active = False
    else:
        telegram_active = True

    user_data = {
        "username": user.username,
        "lastname": user.lastname,
        "middlename": user.middlename,
        "email": user.email,
        "phone": user.phone,
        "phone_2": user.phone_2,
        "gender": user.gender,
        "cards": cards,
        "travel_companions": travel_companions,
        "not_verification_phone_1": not_verification_phone_1,
        "not_verification_phone_2": not_verification_phone_2,
        "not_verification_email": not_verification_email,
        "token_telegram": token_telegram,
        "telegram_active": telegram_active,
    }

    content = {"user": user_data, "choices": choices, "checkeds": checkeds}

    content = add_meta(content, title="Профиль пользователя", description="Личный кабинет пользователя", keywords=["ЛК", "Личный кабинет", "Профиль", "Учётная запись"])

    return render(request, 'user/profile.html', content)


@login_required
def page_favourites(request):
    favourites = Favourite.objects.filter(user=request.user)

    rcs_id = favourites.values_list("rc", flat=True)
    rcs = RCategory.objects.filter(id__in=rcs_id,  is_delete=False)

    d_o_1 = datetime.datetime.now()
    d_o_2 = d_o_1 + datetime.timedelta(days=1)

    s = {
        "city": "moscow",
        "a": 1,
        "c": 0,
        "age_c": [],
        "date_1": d_o_1,
        "date_2": d_o_2,
    }

    count_a = s["a"]
    count_c = s["c"]
    date_1 = s["date_1"]
    date_2 = s["date_2"]
    date_d = date_2 - date_1

    d_1 = s["date_1"].day
    m_1 = s["date_1"].month

    d_2 = s["date_2"].day
    m_2 = s["date_2"].month

    short_months = {1: 'Янв', 2: 'Фев', 3: 'Мар', 4: 'Апр', 5: 'Май',
                    6: 'Июн', 7: 'Июл', 8: 'Авг', 9: 'Сен', 10: 'Окт', 11: 'Ноя', 12: 'Дек'}

    s["date_1"] = f"{d_1} {short_months[m_1]}"
    s["date_2"] = f"{d_2} {short_months[m_2]}"

    s["count_p"] = count_a + count_c

    html_rooms = []

    for rc in rcs:
        # imgs = RImg.objects.filter(rcategory=rc)
        imgs = Img.get_url("hotel.rc", rc.id)

        services = rc.service.all()

        text_price_room = ""

        if date_d.days == 1 and count_a + count_c == 1:
            text_price_room = f"за ночь для 1 гостя"
        elif date_d.days > 1 and count_a + count_c == 1:
            text_price_room = f"за {date_d.days} ночей для 1 гостя"
        elif date_d.days == 1 and count_a + count_c > 1:
            text_price_room = f"за ночь для {count_a + count_c} гостей"
        else:
            text_price_room = f"за {date_d.days} ночей для {count_a + count_c} гостей"

        context = {
            "beds": rc.get_str_beds(),
            "breakfast": rc.hotel.breakfast,
            "count_bedrooms": rc.count_bedrooms,
            "count_images_not_shown": len(imgs) - 2,
            "count_room": rc.count_room,
            "description_of_the_room": rc.description_of_the_room,
            "dinner": rc.hotel.dinner,
            "final_price": int(Booking.calc_price(request.user, rc, (date_1, date_2))["room_full"]),
            "id": rc.id,
            "imgs": imgs,
            "lunch": rc.hotel.lunch,
            "max_adult": rc.max_adults,
            "name": rc.name,
            "offer_type": rc.get_offer_type_display(),
            "square": rc.square,
            "services": [item.name for item in services],
            "text_price_room": text_price_room,
            "favorite": True,
            "url_hotel": f"/hotel/{rc.hotel.id}/",
            "hotel": rc.hotel.name
        }

        tmpl = get_template('template/hotel_detailed_room_favourites.html')

        html_rooms.append({"html": tmpl.render(context), "data": context})

    content = {"rooms": html_rooms, "search": s}

    content = add_meta(content, title="Избраное")

    return render(request, 'user/profile_favourites.html', content)


@login_required
def page_booking(request):
    content = add_meta(None, title="Мои бронирования")
    return render(request, 'user/profile_booking.html', content)


@login_required
def page_balance(request):
    r_b = request.user.rbal
    bonuses_qs = UBRuble.objects.filter(user=request.user)
    FO_qs = FinancialOperation.objects.filter(user=request.user)
    result_bonus = 0
    now_date = datetime.datetime.now()
    now_date = now_date.astimezone()
    bonuses = []
    for bonus in bonuses_qs:
        result_bonus += bonus.value
        date_del = bonus.date + datetime.timedelta(days=bonus.lifespan)
        value = bonus.value
        timedelta = date_del - now_date
        days_left = timedelta.days

        bonuses.append({
            "value": bonus.value,
            "date": bonus.date,
            "del_days": days_left,
            "text": bonus.text,
        })

    FOs = []
    for fo in FO_qs:
        if fo.operation_type not in ["boost", "hotel"]:
            FOs.append({
                "price": fo.price,
                "datetime": fo.datetime,
                "comments": fo.comments,
                "isBonus": fo.isBonus,
            })

    FOs = FOs[::-1]

    balance_sum = {
        "bonus": result_bonus,
        "real": r_b,
    }
    return render(request, 'user/profile_balance.html', {"balance_sum": balance_sum, "bonuses": bonuses, "FOs": FOs})


def page_booking_full(request, id):
    bookings = Booking.objects.filter(booking_user=request.user, id=id)

    if not bookings.exists:
        return render(request, '404.html', status=404)

    booking : Booking = bookings.first()

    if booking == None:
        return redirect("profile_v2")

    if booking.children_ages != None:
        children_ages = booking.children_ages.all()
        children_ages_text = ""
        if children_ages.count() <= 0:
            children_ages_text = "Без детей"
        else:
            children_ages_list = []
            for child in children_ages:
                children_ages_list.append(str(child.age))

            children_ages_text = ', '.join(children_ages_list)
    else:
        children_ages_text = "Без детей"

    booked_room_category_name = "Нет номера"
    booked_hotel_name = "Нет номера"
    accommodation_cost = 0

    booked_room = booking.booked_room

    start_date_time = booking.start_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date_time = booking.end_date_time.replace(hour=0, minute=0, second=0, microsecond=0)

    if booked_room != None:
        booked_hotel_name = booked_room.category.hotel.name
        booked_hotel_id = booked_room.category.hotel.id
        booked_room_category_name = booked_room.category.name
        # accommodation_cost = param["prices"].get("room_full", Booking.calc_price(booking.booking_user, booked_room.category, (start_date_time, end_date_time))["room_full"])
        accommodation_cost = param["prices"].get("room_full", 0)

    chat = Chat.objects.filter(data__booking=booking.id).first()

    param = booking.param

    status_text = booking.get_status_display()
    status = booking.status

    paymant_url = None

    chat_url = None

    if booking.payment_status == "not_paid" and status == "new":
        status = "not_paid"
        status_text = "Не оплачено"

        paymant_url = booking.param.get("paymant_url")
    else:
        chat_url =  f"/profile/chats/?chat={chat.id}" if chat else ""

    booking_data = {
        'id': booking.id,
        'hotel': booked_hotel_name,
        'room_name': booked_room_category_name,
        'check_in': booking.start_date_time,
        'check_out': booking.end_date_time,
        'days_booked': (end_date_time - start_date_time).days,
        'count_a': booking.adults_count,
        'count_c': booking.children_count,
        'children_ages': children_ages_text,
        'accommodation_cost': accommodation_cost,
        'amount_paid': booking.site_price,
        'chat_url': chat_url,
        'hotel_id': booked_hotel_id,
        'status': status,
        'status_text': status_text,
        'prices': param["prices"],
        'paymant_url': paymant_url,
    }

    booking_data["cost_difference"] = booking.hotel_price

    context = {'booking_data': booking_data}
    return render(request, 'user/profile_booking_full.html', context)






def page_notifications(request: HttpRequest):


    notifications = Notification.get(request.user)

    context = {
        "notifications": notifications,
    }

    return render(request, 'user/notifications.html', context)