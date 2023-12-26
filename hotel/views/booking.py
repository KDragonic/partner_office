import copy
import datetime
import json
import locale
import math
from geopy.distance import geodesic
from time import strptime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.urls import reverse
import requests
from brontur.funs import gen_chat_create_booking
from brontur.funs import add_meta, generate_password
from chat.models import Chat
# from hotel.models import Address, HImg, Hotel, RCategory, Room, Comment, RImg, RService, HService, Booking

from hotel.models import Address
from hotel.models import Hotel
from hotel.models import RCategory
from hotel.models import Room
from hotel.models import Comment
from hotel.models import RService
from hotel.models import HService
from hotel.models import Booking
from hotel.models import GroupBooking
from hotel.models import Favourite
from django.forms.models import model_to_dict

from django.db.models import Q

from user.models import User, Notification, Companion, Bonus_rubles, FinancialOperation
from user.mail import send as send_mail
from django.db.models import Count

from django.http import HttpResponse, JsonResponse

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.core.management import call_command

from django.http import Http404

from utils.models import Img, Place


def hotel_room_to_book(request):
    get_param = {obj[0]: obj[1][0]
                 for obj in dict(request.GET.lists()).items()}

    age_c_original: str = get_param["age_c"] if get_param.get("age_c") else ""
    age_c = age_c_original.split("-")

    if age_c == [""]:
        age_c = []

    age_c = [int(obj) for obj in age_c]

    c_count = len(age_c)

    f_age_c = list(filter(lambda x: x >= 3, age_c))
    f_c_count = len(f_age_c)

    a_count = int(get_param["adults"] if get_param.get("adults") else 0)
    date_1 = get_param.get("date_1")
    date_2 = get_param.get("date_2")

    if not date_1 or not date_2:
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        next_week = datetime.datetime.now() + datetime.timedelta(weeks=1)
        date_1 = tomorrow
        date_2 = next_week
    else:
        date_1 = datetime.datetime.strptime(date_1, "%d.%m.%Y")
        date_2 = datetime.datetime.strptime(date_2, "%d.%m.%Y")

    date_d = date_2 - date_1
    rcs_list = [obj.split(".") for obj in get_param["rcs"].split("-")]
    map(int, rcs_list)

    rc_first = RCategory.objects.get(id=rcs_list[0][0])
    hotel = rc_first.hotel
    address = Address.objects.get(hotel=hotel)
    user: User = request.user

    place_id = Place.objects.filter(name=address.city).first().id

    authenticated = user.is_authenticated

    rc_list_result = []

    user_data = {}

    other_data = {}

    for obj in rcs_list:
        rc_id, count, food_rate = obj
        count = int(count)
        rc = RCategory.objects.get(id=rc_id)


        food_rate_price = 0
        if food_rate != "nf":
            food_rate_price = int(rc.additional_info.get("food_rate")[food_rate])

        for index in range(count):
            prices = Booking.calc_price(user, rc, (date_1, date_2), (date_2.date() - date_1.date()).days * food_rate_price)

            if not other_data.get("prices"):
                other_data["prices"] = prices
            else:
                other_data["prices"]["site"] += prices["site"]
                other_data["prices"]["hotel"] += prices["hotel"]
                other_data["prices"]["room_full"] += prices["room_full"]

                other_data["prices"]["prepayment_for_the_room_before_checkin"] += prices["prepayment_for_the_room_before_checkin"]

        if other_data["prices"]["site"] == 0:
            other_data["prices"]["hotel"] = 0

        data = {
            "hotel": {
                "name": hotel.name,
                "time": {
                    "in": hotel.check_in_time.strftime("%H:%M"),
                    "out": hotel.departure_time.strftime("%H:%M"),
                },
                "local": address.short(),
                "city": address.city,
                "stars": hotel.stars,
            },
            "room": {
                "count": count,
                "id": rc.id,
                "name": rc.name,
                "text": "",
                "img": [],
            },
            "date_1": date_1,
            "date_2": date_2,
            "debug": {
                "date_1": date_1.strftime("%d.%m.%Y"),
                "date_2": date_2.strftime("%d.%m.%Y"),
                "d_date_1": date_d.days,
                "d_date_2": ((date_2 - datetime.timedelta(days=1)) - date_1).days,
            }
        }

        beds = rc.get_str_beds()
        data["room"]["text"] += beds


        imgs = Img.get_url("hotel.rc", rc.id, 0)
        if len(imgs) > 0:
            data["room"]["img"] = imgs[0]["url"]

        data["room"]["counts"] = range(count)

        rc_list_result.append(data)

    if user.is_authenticated:
        other_data["prices"]["bonus"]["discount"] = min(Bonus_rubles.get(
            user)["sum"], round(other_data["prices"]["site"] * 0.5))
    else:
        other_data["prices"]["bonus"]["discount"] = 0

    if authenticated:
        user_data["user"] = {
            "username": user.username,
            "lastname": user.lastname,
            "middlename": user.middlename,
            "email": user.email,
            "phone": user.phone,
            "citizenship": user.nationality,
            "travel_companions": Companion.objects.filter(user=user),
            "balance": user.rbal,
        }

    if authenticated:
        return render(request, 'hotel/hotel_room_booking.html', {"list": rc_list_result, "user_data": user_data, "other_data": other_data, "get_param": get_param})
    else:
        return render(request, 'hotel/hotel_room_booking_not_authenticated.html', {"list": rc_list_result, "other_data": other_data, "get_param": get_param})


def format_percent(value):
    return '{:.1%}'.format(value)


def hotel_room_booking_add(request):
    from utils.models import Constant
    username = request.POST.get('name')
    lastname = request.POST.get('lastname')
    middlename = request.POST.get('middlename')
    email = request.POST.get('email')
    phone = request.POST.get('phone')

    if not request.user.is_authenticated:
        users = User.objects.filter(Q(email=email) | Q(phone=phone))
        user = users.first()
        if user:
            content = {
                "error": "the_user_already_exists",
                "status": "error",
            }
            return JsonResponse(content)
        else:

            if user:
                content = {
                    "error": "the_user_already_exists",
                    "status": "error",
                }
                return JsonResponse(content)

            password = generate_password(15)
            active_code_email = generate_password(30)
            user = User.objects.create_user(
                username=username,
                lastname=lastname,
                middlename=middlename,
                email=email,
                login=email,
                password=password,
                gender="Мужской",
                phone=phone,
                active_code_email=active_code_email,
            )

            user.additional_info["password"] = password
            user.save()

            Notification.new(user, "Личный кабинет зарегистрирован", "Продолжите бронирование", "", True, True)

            mail_content = {
                "password": password,
                "login": email,
            }

            send_mail(
                "new_user", "Добро пожаловать на сайт turgorodok.ru", email, mail_content)

            confirmation_email_address_url = request.build_absolute_uri(
                reverse("confirmation_email_address")) + f"?code={active_code_email}"

            send_mail("confirmation_email_address", "Подтвердите свою почту на сайте", email, {
                "confirmation_email_address_url": confirmation_email_address_url})

            settings_options_obj : dict = Constant.get("settings_options", "json")
            bonus_lifetime = int(settings_options_obj["registration_bonuses"]["lifetime"])
            bonus_value = int(settings_options_obj["registration_bonuses"]["value"])


            Bonus_rubles.objects.create(
                user=user,
                value=bonus_value,
                lifespan=bonus_lifetime,
                text="Получено за регистрацию"
            )

            FinancialOperation.new(
                user, bonus_value, True, "user", "Получено за регистрацию")

            login(request, user)
            content = {
                "status": "reload",
            }
            return JsonResponse(content)
    else:
        user = request.user.normal()


    user.save()

    get_param = {obj[0]: obj[1][0]
                 for obj in dict(request.POST.lists()).items()}


    date_1 = get_param.get("date_1")
    date_2 = get_param.get("date_2")

    if not date_1 or not date_2:
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        next_week = datetime.datetime.now() + datetime.timedelta(weeks=1)
        date_1 = tomorrow
        date_2 = next_week
    else:
        date_1 = datetime.datetime.strptime(date_1, "%d.%m.%Y")
        date_2 = datetime.datetime.strptime(date_2, "%d.%m.%Y")

    date_d = date_2 - date_1
    rcs_list = [obj.split(".") for obj in get_param["rcs"].split("-")]

    roomsData = json.loads(get_param["roomsData"])

    content = {}

    # Обработка всех комнат (Поучления цен и проверка на занятость)

    prices_all = None
    list_creating_booking = []

    price_rcs = []

    hotel = None

    for obj in rcs_list:
        rc_id, count = map(int, obj[0:2])
        food_rate = obj[2]

        rc = RCategory.objects.get(id=rc_id)

        if not hotel:
            hotel = rc.hotel

        food_rate_price = 0
        if food_rate != "nf":
            food_rate_price = int(rc.additional_info.get("food_rate")[food_rate])

        calc_price_result = Booking.calc_price(user, rc, (date_1, date_2), (date_2.date() - date_1.date()).days * food_rate_price)

        if not prices_all:
            prices_all = copy.deepcopy(calc_price_result)
        else:
            if calc_price_result["site"] == 0:
                calc_price_result["site"] = 0
            else:
                prices_all["site"] += calc_price_result["site"]

            prices_all["hotel"] += calc_price_result["hotel"]
            prices_all["room_full"] += calc_price_result["room_full"]

        free_count = len(Booking.get_free_rooms(rc, date_1, date_2))

        for room_index in range(count):
            if f"{rc_id}_{room_index}" in roomsData:
                roomData = roomsData[f"{rc_id}_{room_index}"]

                count_guest = roomData["adults"]
                count_guest += len(
                    [children for children in roomData["childrens_age"] if children > 2])



                if rc.max_adults < count_guest:
                    content = {
                        "status": "error",
                        "error": "room_data_too_big",
                        "error_text": f"Для {rc.name} доступно максимум {rc.max_adults} гостей, сейчас {count_guest}",
                        "url": "",
                    }
                    return JsonResponse(content)
            else:
                content = {
                    "status": "error",
                    "error": "room_data_found_without_a_number",
                    "url": "",
                }
                return JsonResponse(content)



        if free_count < count:
            content = {
                "status": "error",
                "error": "not_enough_rooms",
                "url": "",
            }
            return JsonResponse(content)

        for index in range(count):
            list_creating_booking.append({
                "rc": rc,
                "roomData": roomsData[f"{rc_id}_{index}"],
                "food_rate": food_rate,
                "calc_price_result": calc_price_result,
            })

    value_use_bonus = int(request.POST.get('value_use_bonus'))
    value_use_balanc = int(request.POST.get('value_use_balanc'))

    no_success_create_booking_count = 0

    group_booking = GroupBooking.objects.create()

    price_site = prices_all["site"] - value_use_bonus

    # Определить сколько процентов от максимума суммы выбрал клиент
    if value_use_bonus > 0:
        percent_bonus = value_use_bonus / prices_all["site"]
    else:
        percent_bonus = 0
    if value_use_balanc > 0:
        percent_balanc = value_use_balanc / price_site
    else:
        percent_balanc = 0

    value_use_card = price_site - value_use_balanc

    percent_card = 1 - percent_balanc

    buff_booking = []

    for obj in list_creating_booking:
        booking_result = Booking.new(
            rc=obj["rc"],
            user=user,
            dates=(date_1, date_2),
            adult=obj["roomData"]["adults"],
            age_c=obj["roomData"]["childrens_age"],
            use_bonus=value_use_bonus > 0,
        )


        if (booking_result.get("error") == "no_empty_rooms"):
            return JsonResponse({
                "error": "no_empty_rooms",
                "status": "error",
            })

        booking: Booking = booking_result["booking"]

        booking.site_price = obj["calc_price_result"]["site"]
        booking.hotel_price = obj["calc_price_result"]["hotel"]

        booking.param["food_rate"] = obj["food_rate"]

        booking.save()

        buff_booking.append({
            "booking": booking,
            "rc": obj["rc"].name,
            "prices": {
                "site": booking.site_price,
                "hotel": booking.hotel_price,
            },
            "calc_price_result": {
                "site": obj["calc_price_result"]["site"],
                "hotel": obj["calc_price_result"]["hotel"],
                "room_full": obj["calc_price_result"]["room_full"],
                "first_booking_discount": obj["calc_price_result"]["first_booking_discount"],
            }
        })


        group_booking.bookings.add(booking)
        group_booking.save()

        if booking_result["status"] != "success":
            no_success_create_booking_count += 1

    sum_booking = sum([obj["prices"]["site"] for obj in buff_booking])
    percent_booking = []

    for obj in buff_booking:
        booking = obj["booking"]
        price = obj["prices"]["site"]

        if price == 0:
            price = 1

        if sum_booking == 0:
            sum_booking = 1

        percentage_cost = price / sum_booking

        # Бонусы
        if value_use_bonus > 0:
            value_bonus = value_use_bonus * percentage_cost
            percentage_bonus = value_bonus / value_use_bonus
        else:
            value_bonus = 0
            percentage_bonus = 0

        # Лк рубли
        if value_use_balanc > 0:
            value_balanc = value_use_balanc * percentage_cost
            percentage_balanc = value_balanc / value_use_balanc
        else:
            value_balanc = 0
            percentage_balanc = 0

        # Карта
        if value_use_card > 0:
            value_card = value_use_card * percentage_cost
            percentage_card = value_card / value_use_card
        else:
            value_card = 0
            percentage_card = 0

        first_booking_discount = obj["calc_price_result"]["first_booking_discount"]

        booking.param["prices"] = {
            "percentage_cost": percentage_cost,
            "first_booking_discount": first_booking_discount,
            "room_full": obj["calc_price_result"]["room_full"],
            "bonus": {
                "value": value_bonus,
                "percent": percentage_bonus,
            },
            "balanc": {
                "value": value_balanc,
                "percent": percentage_balanc,
            },
            "card": {
                "value": value_card,
                "percent": percentage_card,
            },
        }

        booking.save()

    # Что нету ошибок в создание брони иначе не будет отниматся средства и бонусы
    if no_success_create_booking_count == 0:
        site_price = prices_all["site"]
        room_full_price = prices_all["room_full"]


        if value_use_bonus > 2:
            site_price -= value_use_bonus  # Если использовались бонусы
            Bonus_rubles.deny(user, value_use_bonus)
            FinancialOperation.new(
                user, -value_use_bonus, True, "booking", "За оформление бронирования")

        lk_balanc = None
        card_balanc = None

        if value_use_balanc > 0:  # Условия что используется рубли лк
            if user.rbal >= value_use_balanc:  # Если на лк рублей больше чем или равно чем ввёл пользователь
                lk_balanc = value_use_balanc
            else:  # Если лк рублей не хватает на то что вёл пользователь
                lk_balanc = user.rbal

        else:  # Если пользователь не платит лк рублями
            lk_balanc = 0

        user.rbal -= lk_balanc
        if (lk_balanc > 0):
            FinancialOperation.new(user, -lk_balanc, False, "booking", "За оформление бронирования ")

        user.save()

        if lk_balanc != None:
            card_balanc = site_price - lk_balanc  # Что нужно доплатить картой

        # Дать бонусы
        result_calc = Constant.cashback_calculation(hotel.type_hotel, "booking", site_price, room_full_price)
        Bonus_rubles.add(user, result_calc["value"], result_calc["lifetime"], "За оформление бронирования")
        FinancialOperation.new(user, result_calc["value"], True, "booking", "За оформление бронирования")

        if card_balanc != None and card_balanc > 0:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}

            response_json = requests.post(
                "https://securepayments.sberbank.ru/payment/rest/register.do", data={
                    "userName": "p231709222803-api",
                    "password": "Nard2203-",
                    "orderNumber": group_booking.id,
                    "amount": card_balanc * 100,
                    "returnUrl": request.build_absolute_uri(reverse("hotel_room_booking_successful_payment")),
                    "failUrl": request.build_absolute_uri(reverse("hotel_room_booking_successful_payment")),
                }, headers=headers, verify=False).json()

            for booking in group_booking.bookings.all():
                booking.param["paymant_url"] = response_json["formUrl"]

                rc : RCategory = booking.booked_room.category

                Notification.new(user, "Бронирование", f"Вы успешно забронировали {rc.name} ({booking.id}), оплатите часть суммы картой чтобы завершить бронирование", f"/profile/booking/?id={booking.id}", True, True, send_by_mail_and_telegram=True)

                booking.orderId = response_json["orderId"]
                booking.save()

            content["button_text"] = "Оплатить картой"
            content["url"] = response_json["formUrl"]
            return JsonResponse(content)
        else:
            all_admin = User.objects.filter(user_type__in=["admin", "moder", "owner"])

            urls_chat = []
            for booking in group_booking.bookings.all():
                booking.payment_status = "site_paid"
                booking.orderId = None
                booking.save()

                rc : RCategory = booking.booked_room.category
                user : RCategory = booking.booking_user

                urls_chat.append(gen_chat_create_booking(user, booking))

                Notification.new(user, "Бронирование", f"Вы успешно забронировали {rc.name}, ожидайте подтверждения", f"/profile/booking/?id={booking.id}", True, True, send_by_mail_and_telegram=True)

                hotel = booking.get_hotel()
                if hotel:Notification.new(hotel.owner, "Бронирование", f"У вас новое бронирование номера {rc.name}", f"/profile/hotel/booking/?id={booking.id}", True, True, send_by_mail_and_telegram=True)

                for obj in all_admin:
                    Notification.new(obj, "Поступило новое бронирование",f"{user.get_FIO()} -> {hotel.name} ({hotel.owner.get_FIO()}) -> {booking.id}", f"/admin/page/list/booking/", True, True, send_by_mail_and_telegram=True)

                booking.payment_status = "site_paid"
                booking.orderId = None
                booking.save()

            content["url"] = urls_chat[0]
            content["button_text"] = "Открыть чат"
            return JsonResponse(content)

    content["response_json"] = response_json

    return JsonResponse(content)


def hotel_room_booking_successful_payment(request):
    orderId: str = request.GET.get("orderId")

    bookings = Booking.objects.filter(orderId=orderId)

    all_admin = User.objects.filter(user_type__in=["admin", "moder", "owner"])
    for booking in bookings:

        rc : RCategory = booking.booked_room.category
        user : RCategory = booking.booking_user

        gen_chat_create_booking(user, booking)

        Notification.new(user, "Бронирование", f"Вы успешно оплатили бронирование {booking.id}, ожидайте подтверждения", f"/profile/booking/?id={booking.id}", True, True, send_by_mail_and_telegram=True)

        hotel = booking.get_hotel()
        if hotel:
            Notification.new(hotel.owner, "Бронирование",
                            f"У вас новое бронирование номера {rc.name}", f"/profile/hotel/booking/full/{booking.id}/", True, True, send_by_mail_and_telegram=True)

        for obj in all_admin:
            Notification.new(obj, "Поступило новое бронирование", f"{user.get_FIO()} -> {hotel.name} ({hotel.owner.get_FIO()}) -> {booking.id}", f"/admin/page/list/booking/", True, True, send_by_mail_and_telegram=True)

        booking: Booking
        booking.payment_status = "site_paid"
        booking.orderId = None
        booking.save()

    return redirect("profile_booking")


def hotel_room_booking_failed_payment(request):
    content = {"status": "NOT", "GET": request.GET}

    return JsonResponse(content)
