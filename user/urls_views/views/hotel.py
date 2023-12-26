import datetime
import json
from django.http import Http404, HttpRequest, JsonResponse

from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.urls import reverse
from brontur.funs import get_total_days, get_date_array, add_months

# from hotel.forms import HotelUpdateForm, RoomCreateForm, RoomUpdateForm

from user.models import User, FinancialOperation
from hotel.models import Hotel, Room, Booking, RCategory, RService, PricePerDay, HBoost, Bonus, HService, Comment
from chat.models import Chat
from django.db.models import Q
from django.db.models.query import QuerySet
from utils.models import Img, Doc


@login_required
def page_hotel_chat(request):
    full_chat = None
    chat_id = request.GET.get("chat")
    chats = []
    if chat_id:
        chat_qs = Chat.objects.filter(id=chat_id)
        if chat_qs.exists():
            full_chat = chat_qs.first().id

    user: User = User.normal(request.user.id)
    hotels : QuerySet[Hotel] = user.hotels.all()
    hotels_id = hotels.values_list("id", flat=True)

    chats_qs: QuerySet[Chat] = Chat.objects.filter(
        Q(data__type="booking") & Q(data__hotel__in=hotels_id))

    for chat_item in chats_qs:
        try:
            booking: Booking = Booking.objects.filter(
                id=chat_item.data["booking"]).first()

            if booking:
                if booking.payment_status == "not_paid":
                    continue

                if  not chat_item.users.exists():
                    continue

                rc: RCategory = booking.booked_room.category
                buff_item = {}
                buff_item["id"] = chat_item.id
                buff_item["hotel_name"] = booking.booked_room.category.hotel.name
                buff_item["img"] = Img.get_url("hotel.rc", rc.id, 0)[0]["url"]
                buff_item["url"] = f"/profile/chats/?chat={chat_item.id}&chat_type=booking"
                buff_item["url_booking"] = f"/profile/hotel/booking/?id={booking.id}"
                buff_item["url_booking_text"] = f"Бронирование - {booking.id}"
                buff_item["status"] = booking.get_status_display()
                buff_item["start"] = booking.start_date_time.strftime(
                    "%d.%m.%Y")
                buff_item["end"] = booking.end_date_time.strftime(
                    "%d.%m.%Y")
                buff_item["name"] = rc.name
                chats.append(buff_item)
        except:
            continue

    chats.reverse()

    content = {"full_chat": full_chat, "chats": chats}
    return render(request, 'user/profile_hotel_chat.html', content)


@login_required
def page_chat(request):  # Чат простого пользователя
    full_chat = None
    chat_id = request.GET.get("chat")
    chats = []
    if chat_id:
        chat_qs = Chat.objects.filter(id=chat_id)
        if chat_qs.exists():
            full_chat = chat_qs.first().id

    user: User = request.user.normal()

    # chats_qs: QuerySet[Chat] = Chat.objects.filter(Q(users=user) & Q(data__type="booking"))
    chats_qs: QuerySet[Chat] = Chat.objects.filter(Q(users=user))

    for chat_item in chats_qs:

        booking_id = chat_item.data.get("booking")

        if not booking_id:
            continue

        booking: Booking = Booking.objects.filter(Q(id=booking_id)).first()
        if booking:

            if booking.payment_status == "not_paid":
                continue

            if not booking.booked_room or not booking.booked_room.category:
                continue

            rc: RCategory = booking.booked_room.category
            buff_item = {}
            buff_item["id"] = chat_item.id
            buff_item["hotel_name"] = booking.booked_room.category.hotel.name
            buff_item["img"] = rc.hotel.additional_info["url_cache_phote"][0]
            buff_item["url"] = f"/profile/chats/?chat={chat_item.id}"
            buff_item["url_booking"] = f"/profile/booking/?id={booking.id}"
            buff_item["url_booking_text"] = f"Бронирование - {booking.id}"
            buff_item["status"] = booking.get_status_display()
            buff_item["start"] = booking.start_date_time.strftime(
                "%d.%m.%Y")
            buff_item["end"] = booking.end_date_time.strftime(
                "%d.%m.%Y")
            buff_item["name"] = rc.name
            chats.append(buff_item)

    chats.reverse()

    content = {"full_chat": full_chat, "chats": chats}
    return render(request, 'user/profile_chat.html', content)


@login_required
def page_hotel(request):
    user: User = request.user.normal()

    hotels_prop = []

    hotel_id = request.session.get('hotel')

    if hotel_id == None:
        hotel = None
    else:
        hotel = Hotel.objects.get(id=hotel_id)
        Hotel.check_hotel_owner(user, hotel)

    choices = {}
    choices["meal"] = []
    choices["meal"] = json.dumps(
        [
            ["breakfast", "Завтрак"],
            ["lunch", "Обед"],
            ["dinner", "Ужин"],
        ]
    )

    choices["hotel_type"] = []
    for code, name in Hotel.type_hotel_choices:
        choices["hotel_type"].append([code, name])

    choices["hservice"] = []

    service_qs = HService.objects.all()
    for item in service_qs:
        choices["hservice"].append([item.section, item.id, item.name])

    choices["hservice"] = json.dumps(choices["hservice"])

    choices["hotel_type"] = json.dumps(choices["hotel_type"])

    checkeds = {}

    checkeds["hotel_type"] = json.dumps([hotel.type_hotel])

    checkeds["hservice"] = json.dumps(
        list(hotel.service.all().values_list("id", flat=True)))

    address = hotel.adrress_hotel

    status = ""

    if hotel.is_delete:
        status = "Удалён"

    elif hotel.is_pending:
        status = "На модерации"

    elif not hotel.enable:
        status = "Выключен"

    else:
        status = "Активен"

    hotel_prop = {
        "id": hotel.id,
        "status": status,
        "name": hotel.name,
        "percentage": hotel.percentage,
        "allowed_child": hotel.allowed_child,
        "allowed_animal": hotel.allowed_animal,
        "allowed_smoking": hotel.allowed_smoking,
        "allowed_party": hotel.allowed_party,
        "instant_booking": hotel.instant_booking,
        "percentage": hotel.percentage,
        "stars": hotel.stars,
        "breakfast": hotel.breakfast,
        "lunch": hotel.lunch,
        "dinner": hotel.dinner,
        "minimum_days_before_arrival": hotel.minimum_days_before_arrival,
        "minimum_days_of_stay": hotel.minimum_days_of_stay,
        "date_when_you_start_receiving_guests": datetime.datetime.strftime(hotel.date_when_you_start_receiving_guests, "%Y-%m-%d"),
        "for_long_term_stays": hotel.for_long_term_stays,
        "for_long_term_stays_minimum_days_of_stay": hotel.for_long_term_stays_minimum_days_of_stay,
        "cleaning_fee": hotel.cleaning_fee,
        "descriptions": hotel.descriptions if hotel.descriptions else "",
        "check_in_time": hotel.check_in_time,
        "departure_time": hotel.departure_time,
        "address": {
            "city": address.city if address.city else "",
            "region": address.region if address.region else "",
            "street": address.street if address.street else "",
            "house": address.house if address.house else "",
            "body": address.body if address.body else "",
            "floor": address.floor if address.floor else "",
            "apartment": address.apartment if address.apartment else "",
            "coordinates": address.coordinates if address.coordinates else "",
        },
    }

    imgages = Img.get_url("hotel.hotel", hotel.id)

    hotel_prop["images"] = imgages

    content = {
        "mode_menu": "hotel",
        "hotel": hotel_prop,
        "session": [f"{key}: {value}<br>" for key, value in request.session.items()],
        "choices": choices,
        "checkeds": checkeds
    }


    return render(request, 'user/profile_hotel.html', content)


@login_required
def page_hotel_balance(request):
    hotel_id = request.session.get('hotel')
    hotel = Hotel.objects.get(id=hotel_id)
    Hotel.check_hotel_owner(request.user, hotel)

    r_b = request.user.rbal
    bonuses_qs = Bonus.objects.filter(hotel=hotel)
    result_bonus = 0
    now_date = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=3)))
    bonuses = []
    for bonus in bonuses_qs:
        result_bonus += bonus.value
        date_del = bonus.date + datetime.timedelta(days=bonus.lifespan)
        timedelta = date_del - now_date
        days_left = timedelta.days

        bonuses.append({
            "value": bonus.value,
            "date": bonus.date,
            "del_days": days_left,
            "text": bonus.text,
        })

    FO_qs = FinancialOperation.objects.filter(user=request.user)
    FOs = []
    for fo in FO_qs:
        if fo.operation_type not in ["bonus", "client"]:
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
    return render(request, 'user/profile_balance.html', {"balance_sum": balance_sum, "bonuses": bonuses, "hotel_mod": True, "FOs": FOs})


@login_required
def page_hotel_boost(request):
    hotel_id = request.session.get('hotel')
    hotel = Hotel.objects.get(id=hotel_id)
    Hotel.check_hotel_owner(request.user, hotel)
    current_time = datetime.datetime.now()
    boosts = HBoost.objects.filter(hotel=hotel)
    common: HBoost = boosts.filter(
        super=False, date__gt=current_time).order_by("-date").first()
    super_s = boosts.filter(
        super=True, date__gt=current_time).order_by("-date")

    super = super_s.first()

    super_list = []
    for boost in super_s:
        super_list.append({
            "date": boost.date.astimezone(),
            "dateISO": boost.date.isoformat(),
        })

    content = {
        "common": {
            "date": common.date.isoformat() if common != None else 0,
        },
        "super": {
            "date": super.date.isoformat() if super != None else 0,
            "count": super_s.count(),
        },
        "super_list": super_list,
    }
    return render(request, 'user/profile_hotel_boost.html', content)


@login_required
def page_hotel_rcs(request):
    hotel_id = request.session.get('hotel')
    hotel = Hotel.objects.get(id=hotel_id)
    Hotel.check_hotel_owner(request.user, hotel)

    rcs = []
    for rc in RCategory.objects.filter(hotel=hotel,  is_delete=False):
        rcs.append({
            "id": rc.id,
            "name": rc.name,
            "eneble": rc.enable,
            "max_adults": rc.max_adults,
            "price_base": rc.price_base,
        })

    choices = {}

    choices["offer_type"] = []
    for item in RCategory.offer_type_choices:
        choices["offer_type"].append([item[0], item[1]])

    choices["rservice"] = []
    service_qs = RService.objects.all()
    for item in service_qs:
        choices["rservice"].append([item.id, item.name])

    choices["offer_type"] = json.dumps(choices["offer_type"])
    choices["rservice"] = json.dumps(choices["rservice"])

    content = {
        "rcs":  rcs,
        "hotel_id": hotel.id,
        "choices": choices
    }

    return render(request, 'user/profile_hotel_rcs.html', content)


@login_required
def page_hotel_rooms(request):
    hotel_id = request.session.get('hotel')
    hotel = Hotel.objects.get(id=hotel_id)
    Hotel.check_hotel_owner(request.user, hotel)

    rooms = []
    for rc in Room.objects.filter(category__hotel=hotel,  is_delete=False, category__is_delete=False):
        rooms.append({
            "id": rc.id,
            "name": rc.room_number,
            "eneble": rc.enable,
            "category": rc.category.name,
        })

    choices = {"rcs": []}
    for item in RCategory.objects.filter(hotel=hotel,  is_delete=False):
        choices["rcs"].append([item.id, item.name])

    choices["rcs"] = json.dumps(choices["rcs"])

    return render(request, 'user/profile_hotel_rooms.html', {"rooms":  rooms, "hotel_id": hotel.id, "choices": choices})


@login_required
def page_hotel_booking(request):
    return render(request, 'user/profile_hotel_booking.html')


@login_required
def page_hotel_booking_full(request, id):
    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    bookings = Booking.objects.filter(booked_room__category__hotel__id=select_hotel, id=id)


    if not bookings.exists:
        return render(request, '404.html', status=404)

    booking: Booking = bookings.first()

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

    start_date_time = booking.start_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date_time = booking.end_date_time.replace(hour=0, minute=0, second=0, microsecond=0)

    booked_room = booking.booked_room

    if booked_room != None:
        booked_hotel_name = booked_room.category.hotel.name
        booked_hotel_id = booked_room.category.hotel.id
        booked_room_category_name = booked_room.category.name
        accommodation_cost = Booking.calc_price(booking.booking_user, booked_room.category, (
            start_date_time, end_date_time))["room_full"]

    booking_data = {
        'id': booking.id,
        'hotel': booking.booked_room.category.hotel.name,
        'created_at': booking.created_at,
        'payment_status': booking.get_payment_status_display(),
        'check_in': booking.start_date_time,
        'check_out': booking.end_date_time,
        'days_booked': (end_date_time - start_date_time).days,
        'count_a': booking.adults_count,
        'count_c': booking.children_count,
        'status': booking.status,
        'children_ages': children_ages_text,
        'accommodation_cost': accommodation_cost,
        'amount_paid': booking.site_price,
        "payment_for_accommodation": booking.payment_for_accommodation,
        "cost_difference": booking.hotel_price
    }

    chat = Chat.objects.filter(Q(data__booking=booking.id)).first()

    user_data = {
        "username": booking.booking_user.username,
        "lastname": booking.booking_user.lastname,
        "middlename": booking.booking_user.middlename,
        "phone_1": booking.booking_user.phone if booking.booking_user.phone else "",
        "phone_2": booking.booking_user.phone_2 if booking.booking_user.phone_2 else "",
        "email": booking.booking_user.email,
        "gender": "Мужской" if booking.booking_user.gender == "male" else "Женский",
        'chat_url': f"/profile/hotel/chat/?chat={chat.id}" if chat else "",
    }

    companions_data = []
    companions_data_JQ = list(booking.companions.all())
    for comp in companions_data_JQ:
        companions_data.append({
            "username": comp.username,
            "lastname": comp.lastname,
            "firstname": comp.firstname,
            "phone": comp.phone,
            "date_of_birth": comp.date_of_birth,
            "gender": comp.gender,
        })

    room_data = {
        "name": booking.booked_room.category.name,
        "room_number": booking.booked_room.room_number,
        "price": getattr(booking.booked_room.category, f"price_base"),
    }

    context = {
        'booking_data': booking_data,
        "user_data": user_data,
        "room_data": room_data,
        "companions_data": companions_data,
    }

    return render(request, 'user/profile_hotel_booking_full.html', context)


@login_required
def page_hotel_booking_сhess(request):
    html = booking_chess(request, 30, "today")

    return render(request, 'user/profile_hotel_booking_chess.html', {"html": html})


@login_required
def page_hotel_booking_сhess(request):
    return render(request, 'user/profile_hotel_booking_chess_new.html')


def booking_chess(request, visibility_days, date_start):
    content = {}
    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    hotel = Hotel.objects.get(id=select_hotel)
    Hotel.check_hotel_owner(request.user, hotel)

    # Даты
    if date_start == 'today':
        start_date = datetime.datetime.today()
    else:
        start_date = datetime.datetime.strptime(date_start, "%Y-%m-%d")

    future_date = start_date + datetime.timedelta(days=visibility_days)
    dates = get_date_array(
        start_date, future_date)

    content["dates"] = dates[0:-1]

    content["dates_count"] = len(dates) + 1

    content["visibility_days"] = visibility_days

    content["date_start_calendar"] = start_date

    # Комнаты
    rcs_qs = RCategory.objects.filter(hotel=hotel,  is_delete=False)

    rooms = []
    for category in rcs_qs:
        category_dict = {"rc": {"id": category.id,
                                "name": category.name}, "rooms": []}
        for room in Room.objects.filter(category=category,  is_delete=False):
            room_dict = {"id": room.id, "name": room.room_number}
            category_dict["rooms"].append(room_dict)
        rooms.append(category_dict)

    content["rooms"] = rooms

    # Брони
    bookings_qs = Booking.objects.filter(booked_room__category__hotel=hotel)

    bookings = []
    start_calendar_days = get_total_days(start_date)
    for booking in bookings_qs:
        if booking.status in ["left", "cancelled"]:
            continue

        start_days_unprocessed = get_total_days(booking.start_date_time)
        end_days_unprocessed = get_total_days(booking.end_date_time)

        start_days = round(start_days_unprocessed - start_calendar_days, 3)
        end_days = round(end_days_unprocessed - start_calendar_days, 3)

        if start_days < 0:
            start_days = 0

        if end_days <= 0:
            continue

        diff_days = round(end_days - start_days, 3)

        if booking.status == "close":
            result = {
                "id": booking.id,
                "start": start_days,
                "end": end_days,
                "start_date":  booking.start_date_time.strftime('%Y-%m-%d'),
                "end_date": booking.end_date_time.strftime('%Y-%m-%d'),
                "diff": diff_days,
                "room": booking.booked_room.id,
                "rc": booking.booked_room.category,
                "comment": booking.comment,
                "status": "close",
                "name": f"Закрыто",
                "info": {
                    "booking_user": {"name": "", "value": "Закрыто для брони"},
                    "booked_room": {"name": "Номер", "value": booking.booked_room.room_number},
                    "start_date_time": {"name": "Дата и время начала", "value": booking.start_date_time},
                    "end_date_time": {"name": "Дата и время конца", "value": booking.end_date_time},
                }
            }
            bookings.append(result)
            continue

        children_ages = None
        if getattr(booking, "children_ages").exists():
            ages = ', '.join([str(child.age)
                             for child in getattr(booking, "children_ages").all()])
            children_ages = {"code": "children_ages",
                             "name": "Возраст детей", "value": ages}

        if booking.booking_user.middlename is not None:
            fio = booking.booking_user.lastname + ' ' + \
                booking.booking_user.username + ' ' + booking.booking_user.middlename
        else:
            fio = booking.booking_user.lastname + ' ' + booking.booking_user.username

        fields_list = {
            "booking_user": {"name": "", "value": fio},
            "id": {"name": "ID", "value": booking.id},
            "booked_room": {"name": "Номер", "value": booking.booked_room.room_number},
            "start_date_time": {"name": "Дата и время начала", "value": booking.start_date_time},
            "end_date_time": {"name": "Дата и время конца", "value": booking.end_date_time},
            "adults_count": {"name": "Количество взрослых", "value": booking.adults_count},
            "children_count": {"name": "Количество детей", "value": booking.children_count},
            "children_ages": {"name": "Возраст детей", "value": children_ages},
            "status": {"name": "Статус", "value": booking.get_status_display()},
            "created_at": {"name": "Дата создания", "value": booking.created_at},
        }

        result = {
            "id": booking.id,
            "start": start_days,
            "end": end_days,
            "diff": diff_days,
            "room": booking.booked_room.id,
            "rc": booking.booked_room.category,
            "name": f"{booking.booking_user.lastname} {booking.booking_user.username[0]}.",
            "status": booking.status,
            "url": reverse("profile_hotel_booking_full", args=[booking.id]),
            "info": fields_list,
        }
        bookings.append(result)

    content["bookings"] = bookings

    tmpl = get_template('template/booking_chess.html')

    return tmpl.render(content)


@login_required
def page_hotel_price_calendar_new(request):
    content = {}
    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")
    hotel = Hotel.objects.get(id=select_hotel)
    Hotel.check_hotel_owner(request.user, hotel)

    start_date = datetime.datetime.today()

    future_date = start_date + datetime.timedelta(days=30)
    dates = get_date_array(start_date, future_date)

    content["dates"] = dates[0:-1]

    content["dates_count"] = len(dates) + 1

    rcs_qs = RCategory.objects.filter(
        hotel=hotel, enable=True,  is_delete=False)

    rcs = []
    for rc in rcs_qs:
        r_rc = {}
        r_rc["price_base"] = rc.price_base
        r_rc["days_min"] = rc.min_days
        r_rc["items"] = []
        r_rc["name"] = rc.name
        r_rc["id"] = rc.id

        for date in dates[0:-1]:
            cell = PricePerDay.getOne(rc, date["date"])
            r_cell = {
                "room_free": len(Booking.get_free_room(rc, date["date"])),
                "ymd": date["ymd"],
            }

            if cell:
                if cell.price != None:
                    r_cell["price"] = cell.price
                else:
                    r_cell["price"] = ""

                if cell.days_min != None:
                    r_cell["days_min"] = cell.days_min
                else:
                    r_cell["days_min"] = ""

            r_rc["items"].append(r_cell)
        rcs.append(r_rc)

    content["rcs"] = rcs

    return render(request, 'user/profile_hotel_price_calendar_new.html', content)

def page_back_url_login_page(request):
    return render(request, 'user/page_back_url_login_page.html')


def page_hotel_reviews(request: HttpRequest):
    return render(request, 'user/profile_hotel_reviews.html')


def ajax_hotel_get_reviews(request: HttpRequest):
    hotel_id = request.session.get('hotel')
    hotel = Hotel.objects.get(id=hotel_id)
    Hotel.check_hotel_owner(request.user, hotel)

    reviews_qs = Comment.objects.filter(hotel=hotel).order_by("-date")

    # Формирование списка отзывов для возврата в ответе
    results = []
    for review in reviews_qs:
        review: Comment

        imgs = Img.get_url_list("hotel.comment", review.id)

        results.append({
            "id": review.id,
            'username': review.author_name if review.user == None else review.user.get_FIO(),
            'date': review.date.strftime("%m.%Y"),
            'rcategory': review.author_room if review.rc == None else review.rc.name,
            'location': review.location,
            'price_quality_ratio': review.price_quality_ratio,
            'purity': review.purity,
            'food': review.food,
            'service': review.service,
            'number_quality': review.number_quality,
            'hygiene_products': Comment.convert_value("hygiene", review.hygiene_products)["text"],
            'wifi_quality': Comment.convert_value("wifi", review.wifi_quality)["text"],
            'what_is_good_text': review.what_is_good_text,
            'what_is_bad_text': review.what_is_bad_text,
            "overall_rating": review.overall_rating,
            "overall_rating_text": Comment.convert_value("overall_rating", round(review.overall_rating))["text"],
            "imgs": list(imgs),
            "reply": review.reply,
        })

    # Формирование ответа в формате JSON
    response = {
        'results': results,
        'hotel': hotel.name,
    }

    return JsonResponse(response)


def ajax_hotel_documents_get(request: HttpRequest):
    if request.method == 'GET':
        hotel_id = request.GET.get("hotel")

        hotel = Hotel.objects.filter(id=hotel_id).first()
        docs = {}
        if hotel:
            docs = hotel.additional_info.get("docs", {})

        return JsonResponse({"docs": docs})
    else:
        return JsonResponse({"success": False, "error": "Invalid request method."})

def ajax_hotel_sending_documents(request: HttpRequest):
    if request.method == 'POST':
        param : dict = json.loads(request.body.decode('utf-8'))
        docs : dict = param.get("docs")

        new_docs = {}

        hotel_id = param.get("hotel")
        hotel = Hotel.objects.filter(id=hotel_id).first()
        if hotel:
            for key_docs_item, docs_item in docs.items():
                new_docs
                for index_doc, doc in enumerate(docs_item):
                    doc = Doc.objects.get(id=doc)
                    doc.param["model"] = "hotel.doc"
                    doc.param["obj"] = hotel.id
                    doc.param["order"] = index_doc
                    doc.save()
                    docs[key_docs_item][index_doc] = {
                        "id": doc.id,
                        "url": doc.file.url,
                        "checked": {
                            "date": None,
                            "user": None,
                            "note": None,
                            "status": False,
                        },
                        "updated_at": datetime.datetime.now().timestamp(),
                    }

            hotel.additional_info["docs"] = docs


            hotel.save()

        return JsonResponse({"docs": docs})
    else:
        return JsonResponse({"success": False, "error": "Invalid request method."})


def ajax_hotel_update_reviews(request: HttpRequest):
    if request.method == 'POST':
        update_reviews : dict = json.loads(request.body.decode('utf-8'))

        update_reviews_count = 0

        for id, review_param in update_reviews.items():
            review_obj = Comment.objects.filter(id=id).first()
            if review_obj:
                update_reviews_count += 1

                if review_param["reply"]:
                    review_obj.reply = review_param["reply"]

                review_obj.save()

        return JsonResponse({"update_reviews_count": update_reviews_count})
    else:
        return JsonResponse({"success": False, "error": "Invalid request method."})