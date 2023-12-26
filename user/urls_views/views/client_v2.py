
import datetime
import json
from django.forms import model_to_dict
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import render
from django.urls import resolve, reverse
from django.contrib.auth.decorators import login_required
from brontur.funs import generate_password, validate_post_parameters
from user.models import User, FinancialOperation, Bonus_rubles, Notification
from chat.models import Chat
from hotel.models import Hotel, RCategory, Booking, Bonus, HBoost, HService, RService, Favourite, Comment, Address, Room, PricePerDay
from utils.models import Img
from brontur.funs import add_meta
import user.mail as my_mail


from django.db.models.query import QuerySet, Q

@login_required
def page_home(request: HttpRequest):
    user: User = request.user

    hotels = Hotel.objects.filter(owner=user, is_delete=False)
    if hotels.exists():
        if not request.session.get('hotel'):
            request.session["hotel"] = hotels.first().id
            request.session.modified = True

    context = {
        "user": model_to_dict(user),
        "menu_lk_active": resolve(request.path).url_name,
        "favourite_count": Favourite.objects.filter(user=user).count
    }

    context["user"]['fio'] = user.get_FIO()
    context["user"]['first_letter_fio'] = user.get_FIO()[0].upper()

    context["balanc"] = {
        "bonus": Bonus_rubles.get(user)["sum"],
        "real_rubles": user.rbal,
    }

    hotels = Hotel.objects.filter(owner=request.user)
    if hotels.exists():
        context["balanc"]["bonus_hotel"] = 0

        for bonus in Bonus.objects.filter(hotel__in=hotels):
            context["balanc"]["bonus_hotel"] += bonus.value

    new_message_count = 0
    all_message_count = 0

    personal_me_chat_id = Chat.get_personal_chat(user)

    chats = Chat.objects.filter(Q(users=user) & Q(data__type = "booking")).distinct()

    for chat in chats:
        new_message_count += chat.messages.filter(~Q(read_user=user)).distinct().count()
        all_message_count += chat.messages.count()

    context["chat"] = {
        "count": len(chats),
        "new_message_count": new_message_count,
        "all_message_count": all_message_count,
    }

    add_meta(context, title="Профиль")

    if user.user_type == "hotel":
        return render(request, 'user/v2/home_hotel.html', context)

    return render(request, 'user/v2/home_client.html', context)


def page_profile_edit(request: HttpRequest):

    user: User = request.user

    context = {
        "user": model_to_dict(user),
        "menu_lk_active": resolve(request.path).url_name,
    }

    context["user"]['fio'] = user.get_FIO()
    context["user"]['first_letter_fio'] = user.get_FIO()[0].upper()
    context["user"]['password'] = user.additional_info.get("password")

    add_meta(context, title="Изменить профиль")

    return render(request, 'user/v2/profile_edit.html', context)


def ajax_profile_edit_fio(request: HttpRequest):

    user: User = request.user


    user.username = request.POST.get("username", user.username) if not user.username else user.username
    user.lastname = request.POST.get("lastname", user.lastname) if not user.lastname else user.lastname
    user.middlename = request.POST.get("middlename", user.middlename) if not user.middlename else user.middlename

    user.save()

    content = {
        "result": "ok",
    }

    return JsonResponse(content)


def ajax_profile_edit_email(request: HttpRequest):

    user: User = request.user

    new_email = request.POST.get("email")

    if not new_email:
        return JsonResponse({"result": "not"})

    if (user.email == new_email):
        return JsonResponse({"result": "not"})

    is_reset = False

    if new_email == "reset":
        is_reset = True
        new_email = user.email

    active_code_email = generate_password(30)
    confirmation_email_address_url = request.build_absolute_uri(reverse("confirmation_email_address")) + f"?code={active_code_email}"
    my_mail.send("confirmation_email_address", "Подтвердите свою почту на сайте", new_email, {"confirmation_email_address_url": confirmation_email_address_url})

    if is_reset:
        Notification.new(user, "Вы запросили повторное письмо проверки почты", "Подтвердите почту из письма", "/profile_v2/", True, True)
    else:
        Notification.new(user, "Вы указали новую почту", "Подтвердите почту из письма", "/profile_v2/", True, True)
        user.email = request.POST.get("email", user.email)

    user.active_code_email = active_code_email
    user.active_email = False

    user.save()

    content = {
        "result": "ok",
    }

    return JsonResponse(content)


def ajax_profile_edit_phone(request: HttpRequest):

    user: User = request.user

    new_phone = request.POST.get("phone")

    if not new_phone:
        return JsonResponse({"result": "not"})

    if (user.phone == new_phone):
        return JsonResponse({"result": "not"})

    user.active_phone = False
    user.phone = request.POST.get("phone", user.phone)

    user.save()

    content = {
        "result": "ok",
    }

    return JsonResponse(content)


def ajax_profile_edit_password(request: HttpRequest):

    user: User = request.user

    old_password = request.POST.get("old_password")
    password_1 = request.POST.get("password_1")
    password_2 = request.POST.get("password_2")

    password_1 = password_1.strip()
    password_2 = password_2.strip()

    if not all([old_password, password_1, password_2]):
        return JsonResponse({"result": "Заполните все поля"})

    if old_password == password_1:
        return JsonResponse({"result": "Старый и новый пароль совпадает"})

    if password_1 != password_2:
        return JsonResponse({"result": "Пароли не совпадают"})

    if not user.check_password(old_password):
        return JsonResponse({"result": "Неправильный старый пароль"})

    user.additional_info["password"] = password_1

    user.set_password(password_1)
    user.save()

    content = {
        "result": "ok",
    }

    return JsonResponse(content)


def page_bookings(request: HttpRequest):

    user: User = request.user

    context = {
        "menu_lk_active": resolve(request.path).url_name,
    }

    return render(request, 'user/v2/booking_list.html', context)


def page_booking(request: HttpRequest):

    user: User = request.user

    booking_id = request.GET.get("id")

    booking = Booking.objects.filter(booking_user=user, id=booking_id).first()
    if not booking:
        raise Http404("Бронирование не найдено")

    if not hasattr(booking, 'booked_room') or not hasattr(booking.booked_room, 'category') or not hasattr(booking.booked_room.category, 'hotel'):
        raise Http404("Бронирование не найдено")

    hotel = booking.booked_room.category.hotel

    hotel_param = model_to_dict(hotel)
    hotel_param["address"] = hotel.adrress_hotel.short() if hasattr(hotel, "adrress_hotel") else ""
    hotel_param["type_hotel"] = hotel.get_type_hotel_display()
    rc_param = model_to_dict(booking.booked_room.category)

    booking_param = model_to_dict(booking)

    start_date_time = booking.start_date_time.replace(
        hour=0, minute=0, second=0, microsecond=0)
    end_date_time = booking.end_date_time.replace(
        hour=0, minute=0, second=0, microsecond=0)
    booking_param['check_in'] = booking.start_date_time
    booking_param['check_out'] = booking.end_date_time
    booking_param['days_booked'] = (end_date_time - start_date_time).days

    if booking.children_ages != None:
        children_ages = booking.children_ages.all()
        children_ages_text = ""
        if children_ages.count() <= 0:
            children_ages_text = None
        else:
            children_ages_list = []
            for child in children_ages:
                children_ages_list.append(str(child.age))

            children_ages_text = ', '.join(children_ages_list)

        booking_param["children_ages"] = children_ages_text

    booking_param["status_text"] = booking.get_status_display()
    booking_param["payment_status"] = booking.payment_status
    booking_param["prices"] = booking.param["prices"]

    booking_param['accommodation_cost'] = booking.param["prices"].get("room_full", 0)
    booking_param['amount_paid'] = booking.site_price

    booking_param["bonuses_for_writing_a_review"] = round(
        booking.site_price * 0.2)

    food_rate = booking.param.get("food_rate")

    if food_rate:
        if food_rate == "breakfast_lunch_dinner":
            booking_param["food_rate"] = "Завтрак, обед, ужин"

        if food_rate == "breakfast_lunch":
            booking_param["food_rate"] = "Завтрак, обед"

        if food_rate == "breakfast_dinner":
            booking_param["food_rate"] = "Завтрак, ужин"

        if food_rate == "lunch_dinner":
            booking_param["food_rate"] = "Обед, ужин"

        if food_rate == "breakfast":
            booking_param["food_rate"] = "Завтрак"

        if food_rate == "lunch":
            booking_param["food_rate"] = "Обед"

        if food_rate == "dinner":
            booking_param["food_rate"] = "Ужин"

    prepayment_for_the_room_before_checkin = booking.param.get("prepayment_for_the_room_before_checkin")

    if prepayment_for_the_room_before_checkin:
        booking_param["prepayment_for_the_room_before_checkin"] = round((prepayment_for_the_room_before_checkin / 100) * booking_param['accommodation_cost'])


    chat = Chat.objects.filter(data__booking=booking.id).first()
    if chat:
        booking_param["chat_id"] = chat.id

    if booking.is_review_bonus == False:
        if booking.status in ["verified", "settled", "left"]:
            if booking.end_date_time.date() < (datetime.datetime.now() - datetime.timedelta(1)).date():
                booking_param["possible_review"] = True

    context = {
        "hotel": hotel_param,
        "rc": rc_param,
        "booking": booking_param,
        "menu_lk_active": resolve(request.path).url_name,
    }

    return render(request, 'user/v2/booking.html', context)


def page_chats(request: HttpRequest):

    content = {
        "menu_lk_active": resolve(request.path).url_name,
        "hotel_mod": request.user.user_type == "hotel",
    }

    return render(request, 'user/v2/chats.html', content)


def page_billing(request: HttpRequest):

    content = {
        "menu_lk_active": resolve(request.path).url_name,
        "real": 0,
        "bonus": {
            "client": {
                "list": [],
                "sum": 0,
            }
        }
    }

    r_b = request.user.rbal
    result_bonus = 0

    now_date = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=3)))

    # Бонусы клинета
    bonuses_client = []
    bonuses_client_sum = 0
    for bonus in Bonus_rubles.objects.filter(user=request.user):
        content["bonus"]["client"]["sum"] += bonus.value
        date_del = bonus.date + datetime.timedelta(days=bonus.lifespan)
        timedelta = date_del - now_date
        days_left = timedelta.days

        content["bonus"]["client"]["list"].append({
            "value": bonus.value,
            "date": bonus.date,
            "del_days": days_left,
            "text": bonus.text,
        })

    # Бонусы отеля
    hotels = Hotel.objects.filter(owner=request.user)
    if hotels.exists():
        bonuses_hotel = []
        bonuses_hotel_sum = 0
        content["bonus"]["hotel"] = {
            "list": [],
            "sum": 0,
        }

        for bonus in Bonus.objects.filter(hotel__in=hotels):
            content["bonus"]["hotel"]["sum"] += bonus.value
            date_del = bonus.date + datetime.timedelta(days=bonus.lifespan)
            timedelta = date_del - now_date
            days_left = timedelta.days

            content["bonus"]["hotel"]["list"].append({
                "value": bonus.value,
                "hotel": bonus.hotel.name,
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

    content["FOs"] = FOs

    content["real"] = r_b

    return render(request, 'user/v2/billing.html', content)


def page_hotel_upgrade(request: HttpRequest):

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
        "menu_lk_active": resolve(request.path).url_name,
    }

    return render(request, 'user/v2/hotel_upgrade.html', content)


def page_hotel_bookings(request: HttpRequest):

    user: User = request.user

    context = {
        "menu_lk_active": resolve(request.path).url_name,
    }

    return render(request, 'user/v2/hotel_booking_list.html', context)


def page_hotel_booking(request: HttpRequest):

    user: User = request.user

    booking_id = request.GET.get("id")

    booking = Booking.objects.filter(
        booked_room__category__hotel__owner=user, id=booking_id).first()
    if not booking:
        raise Http404("Бронирование не найдено")

    if not hasattr(booking, 'booked_room') or not hasattr(booking.booked_room, 'category') or not hasattr(booking.booked_room.category, 'hotel'):
        raise Http404("Бронирование не найдено")

    hotel = booking.booked_room.category.hotel

    hotel_param = model_to_dict(hotel)
    hotel_param["address"] = hotel.adrress_hotel.short() if hasattr(hotel, "adrress_hotel") else ""
    hotel_param["type_hotel"] = hotel.get_type_hotel_display()
    rc_param = model_to_dict(booking.booked_room.category)

    booking_param = model_to_dict(booking)

    start_date_time = booking.start_date_time.replace(
        hour=0, minute=0, second=0, microsecond=0)
    end_date_time = booking.end_date_time.replace(
        hour=0, minute=0, second=0, microsecond=0)
    booking_param['check_in'] = booking.start_date_time
    booking_param['check_out'] = booking.end_date_time
    booking_param['days_booked'] = (end_date_time - start_date_time).days

    if booking.children_ages != None:
        children_ages = booking.children_ages.all()
        children_ages_text = ""
        if children_ages.count() <= 0:
            children_ages_text = None
        else:
            children_ages_list = []
            for child in children_ages:
                children_ages_list.append(str(child.age))

            children_ages_text = ', '.join(children_ages_list)

        booking_param["children_ages"] = children_ages_text

    booking_param["status_text"] = booking.get_status_display()
    booking_param["payment_status"] = booking.payment_status
    booking_param["prices"] = booking.param["prices"]

    booking_param['accommodation_cost'] = booking.param["prices"].get("room_full", 0)
    booking_param['amount_paid'] = booking.site_price

    booking_param["bonuses_for_writing_a_review"] = round(
        booking.site_price * 0.2)

    food_rate = booking.param.get("food_rate")

    if food_rate:
        if food_rate == "breakfast_lunch_dinner":
            booking_param["food_rate"] = "Завтрак, обед, ужин"

        if food_rate == "breakfast_lunch":
            booking_param["food_rate"] = "Завтрак, обед"

        if food_rate == "breakfast_dinner":
            booking_param["food_rate"] = "Завтрак, ужин"

        if food_rate == "lunch_dinner":
            booking_param["food_rate"] = "Обед, ужин"

        if food_rate == "breakfast":
            booking_param["food_rate"] = "Завтрак"

        if food_rate == "lunch":
            booking_param["food_rate"] = "Обед"

        if food_rate == "dinner":
            booking_param["food_rate"] = "Ужин"


    chat = Chat.objects.filter(data__booking=booking.id).first()
    if chat:
        booking_param["chat_id"] = chat.id

    user_param = {}
    user_param["fio"] = booking.booking_user.get_FIO()
    user_param["email"] = booking.booking_user.email
    user_param["phone"] = booking.booking_user.phone

    context = {
        "hotel": hotel_param,
        "rc": rc_param,
        "booking": booking_param,
        "user": user_param,
        "menu_lk_active": resolve(request.path).url_name,
    }

    return render(request, 'user/v2/hotel_booking.html', context)


def page_hotel_edit(request: HttpRequest):
    from utils.models import Constant
    user: User = request.user.normal()

    hotels_prop = []

    hotels_qs = Hotel.objects.filter(owner=user)

    select_hotel = None

    for hotel in hotels_qs:
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
        }

        imgs = hotel.additional_info.get("url_cache_phote", [])
        if len(imgs) > 0:
            hotel_prop["img"] = imgs[0]
        else:
            imgs = Img.get_url_list("hotel.hotel", hotel.id)

            hotel.additional_info["url_cache_phote"] = imgs
            hotel.save()
            if len(imgs) > 0:
                hotel_prop["img"] = imgs[0]
            else:
                hotel_prop["img"] = ""

        hotels_prop.append(hotel_prop)

    choices = {}
    choices["hservice"] = []

    service_qs = HService.objects.all()
    for item in service_qs:
        choices["hservice"].append([item.section, item.id, item.name])

    choices["hservice"] = json.dumps(choices["hservice"])

    settings_options_obj : dict = Constant.get("settings_options", "json")

    choices["percentage"] = []
    if settings_options_obj["site_commission"]["not_commission"]:
        choices["percentage"].append({"name": "Без комиссии", "value": 0})

    percentage_start = int(settings_options_obj["site_commission"]["from"])
    percentage_end = int(settings_options_obj["site_commission"]["to"])
    if percentage_start > percentage_end:
        percentage_end, percentage_start = percentage_start, percentage_end

    for perc in range(percentage_start, percentage_end + 1):
            choices["percentage"].append({"name": f"{perc}%", "value": perc})


    content = {
        "mode_menu": "hotel",
        "hotels": hotels_prop,
        "choices": choices,
        "menu_lk_active": resolve(request.path).url_name,
    }

    return render(request, 'user/v2/hotel_edit.html', content)

def ajax_profile_hotel_edit_get(request: HttpRequest):
    user: User = request.user
    hotel_id = request.GET.get("hotel")
    hotel = Hotel.objects.filter(id=hotel_id, owner=user).first()

    if not hotel:
        return JsonResponse({"error": "The hotel was not found, or does not belong to the user"})

    address = hotel.adrress_hotel if hasattr(hotel, "adrress_hotel") else None

    hotel_prop = {
        "id": hotel.id,
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
        "hotel_type": hotel.type_hotel,
        "minimum_days_before_arrival": hotel.minimum_days_before_arrival,
        "minimum_days_of_stay": hotel.minimum_days_of_stay,
        "date_when_you_start_receiving_guests": datetime.datetime.strftime(hotel.date_when_you_start_receiving_guests, "%Y-%m-%d"),
        "cleaning_fee": hotel.cleaning_fee,
        "descriptions": hotel.descriptions if hotel.descriptions else "",
        "check_in_time": hotel.check_in_time,
        "departure_time": hotel.departure_time,

        "city": address.city if address else "",
        "region": address.region if address else "",
        "street": address.street if address else "",
        "house": address.house if address else "",
        "body": address.body if address else "",
        "floor": address.floor if address else "",
        "apartment": address.apartment if address else "",
        "coordinates": address.coordinates if address else "",
    }

    imgages = Img.get_url("hotel.hotel", hotel.id)

    hotel_prop["images"] = imgages

    hotel_prop["hservice"] = list(
        hotel.service.all().values_list("id", flat=True))

    return JsonResponse(hotel_prop)


def ajax_profile_hotel_edit_save(request: HttpRequest):
    user = request.user
    select_hotel = request.POST.get('hotel_id')
    if not select_hotel:
        return JsonResponse({"result": "error", "errors": "The object was not found or does not belong to the user"})

    hotel = Hotel.objects.filter(id=select_hotel, owner=user).first()

    if not hotel:
        return JsonResponse({"result": "error", "errors": "The object was not found or does not belong to the user"})

    user = User.objects.get(uid=request.user.uid)

    validation_rules = {
        "name": {"required": True, "length": [3, 50]},
        "descriptions": {"required": False, "length": [10, 9999]},
        "allowed_child": {"required": True},
        "allowed_animal": {"required": True},
        "allowed_smoking": {"required": True},
        "allowed_party": {"required": True},
        "instant_booking": {"required": True},
        "percentage": {"required": True, "range": [14, 30]},
        "check_in_time": {"required": True},
        "departure_time": {"required": True},
        "minimum_days_before_arrival": {"required": True, "range": [0, 999]},
        "minimum_days_of_stay": {"required": True, "range": [0, 999]},
        "date_when_you_start_receiving_guests": {"required": True},
        "cleaning_fee": {"required": True, "range": [0, 999999], "type": "num_or_%"},
        "city": {"required": True},
        "region": {"required": False},
        "street": {"required": True},
        "body": {"required": False},
        "house": {"required": True},
        "floor": {"required": False},
        "apartment": {"required": False},
        "coordinates": {"required": True},
        "stars": {"required": True},
    }

    valid_result = validate_post_parameters(
        request=request, validation_rules=validation_rules)

    if len(valid_result) > 0:
        return JsonResponse({"result": "error", "errors": valid_result})

    data = {
        "hotel": {
            "name": request.POST.get("name"),
            "descriptions": request.POST.get("descriptions"),
            "allowed_child": True if request.POST.get("allowed_child") == "true" else False,
            "allowed_animal": True if request.POST.get("allowed_animal") == "true" else False,
            "allowed_smoking": True if request.POST.get("allowed_smoking") == "true" else False,
            "allowed_party": True if request.POST.get("allowed_party") == "true" else False,
            "stars": request.POST.get("stars"),
            "instant_booking": True if request.POST.get("instant_booking") == "True" else False,
            "percentage": request.POST.get("percentage"),
            "check_in_time": request.POST.get("check_in_time"),
            "departure_time": request.POST.get("departure_time"),
            "minimum_days_before_arrival": request.POST.get("minimum_days_before_arrival"),
            "minimum_days_of_stay": request.POST.get("minimum_days_of_stay"),
            "date_when_you_start_receiving_guests": request.POST.get("date_when_you_start_receiving_guests"),
            "for_long_term_stays": "0",
            "for_long_term_stays_minimum_days_of_stay": 0,
            "cleaning_fee": request.POST.get("cleaning_fee"),
            "breakfast": True if request.POST.get("breakfast") == "True" else False,
            "lunch": True if request.POST.get("lunch") == "True" else False,
            "dinner": True if request.POST.get("dinner") == "True" else False,
        },
        "address": {
            "city": request.POST.get("city"),
            "region": request.POST.get("region"),
            "street": request.POST.get("street"),
            "body": request.POST.get("body"),
            "house": request.POST.get("house"),
            "floor": request.POST.get("floor"),
            "apartment": request.POST.get("apartment"),
            "coordinates": request.POST.get("coordinates"),
        }
    }

    cur_data_hotel = {
        "hotel.name": hotel.name,
    }

    values_hotel = {}
    for key in data["hotel"]:
        values_hotel[key] = data["hotel"][key]

    # замена запятой на запятую с пробелом
    if ", " not in data["address"]["coordinates"]:
        data["address"]["coordinates"] = data["address"]["coordinates"].replace(
            ",", ", ")

    values_address = {}
    for key in data["address"]:
        values_address[key] = data["address"][key]

    values_hotel['owner'] = user

    for item in values_hotel:
        setattr(hotel, item, values_hotel[item])

    hservice_get = request.POST.get("hservice[]")

    if len(hservice_get) > 0:
        service_list = hservice_get.split(",")
        service = HService.objects.filter(id__in=service_list)
        hotel.service.set(service)

    addres = Address.objects.filter(hotel=hotel).first()
    if not addres:
        addres = Address.objects.create(
            hotel=hotel,
            city="",
            street="",
            house="",
            coordinates="",
        )

    cur_data_addres = {
        "addres.city": addres.city,
        "addres.region": addres.region,
        "addres.street": addres.street,
        "addres.body": addres.body,
        "addres.house": addres.house,
        "addres.floor": addres.floor,
        "addres.apartment": addres.apartment,
        "addres.coordinates": addres.coordinates
    }

    for item in values_address:
        setattr(addres, item, values_address[item])

    images_hotel: str = request.POST.get("images_hotel[]")
    images_hotel = images_hotel.split(",")

    imgs_del: QuerySet[Img] = Img.get("hotel.hotel", hotel.id)

    for img in imgs_del:
        img.param["model"] = "not_linked"
        img.save()

    imgs = Img.get_id_to_obj(images_hotel)
    for index, img in enumerate(imgs):
        img.param["model"] = "hotel.hotel"
        img.param["obj"] = hotel.id
        img.param["order"] = index
        img.save()

    url_list = Img.get_url_list("hotel.hotel", hotel.id)
    hotel.additional_info["url_cache_phote"] = list(url_list)
    hotel.save()

    is_moderator = False

    if cur_data_hotel["hotel.name"] != values_hotel["name"] or \
            cur_data_addres["addres.city"] != values_address["city"] or \
            cur_data_addres["addres.region"] != values_address["region"] or \
            cur_data_addres["addres.street"] != values_address["street"] or \
            cur_data_addres["addres.body"] != values_address["body"] or \
            cur_data_addres["addres.house"] != values_address["house"] or \
            cur_data_addres["addres.floor"] != values_address["floor"] or \
            cur_data_addres["addres.apartment"] != values_address["apartment"] or \
            cur_data_addres["addres.coordinates"] != values_address["coordinates"]:
        Notification.new(
            user, "Отель", "Объект отправлен на модерацию", "", True, True)
        hotel.is_pending = True
        is_moderator = True
        hotel.save()

    addres.save()
    hotel.save()
    Notification.new(user, "Отель", "Объект изменён", "", True, True)

    return JsonResponse({"result": "save", "moderator": is_moderator,  "errors": None})


def page_hotel_rooms(request: HttpRequest):
    hotel_id = request.session.get('hotel')
    hotel = Hotel.objects.get(id=hotel_id)
    Hotel.check_hotel_owner(request.user, hotel)

    rcs = []
    for rc in hotel.rcategory_hotel.filter(is_delete=False):
        rc : RCategory
        img_hash = rc.additional_info.get("img_hash")
        if not img_hash:
            img_hash = rc.hash_image_update()

        rcs.append({
            "id": rc.id,
            "name": rc.name,
            "img": img_hash[0] if len(img_hash) > 0 else "",
            "eneble": rc.enable,
            "max_adults": rc.max_adults,
            "price_base": rc.price_base,
            "beds_text": rc.get_str_beds(),
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
        "choices": choices,
                "menu_lk_active": resolve(request.path).url_name,
    }
    return render(request, 'user/v2/hotel_rooms.html', content)


def ajax_profile_hotel_rooms_edit_get(request: HttpRequest):
    rc_id = request.GET.get("rc")
    rc = RCategory.objects.filter(id=rc_id, hotel__owner=request.user).first()

    if not rc:
        return JsonResponse({"error": "RCategory не найден или не принадлежит пользователю"})

    rc_prop = model_to_dict(rc, exclude=["service"])
    rc_prop["rooms"] = list(Room.objects.filter(
        category=rc).values_list("room_number", flat=True))
    rc_prop["images"] = Img.get_url("hotel.rc", rc.id)
    rc_prop["rservice"] = list(rc.service.all().values_list("id", flat=True))

    return JsonResponse(rc_prop)


def ajax_profile_hotel_rooms_edit_save(request: HttpRequest):
    id = request.POST.get("id")
    name = request.POST.get("name")
    offer_type = request.POST.get("offer_type")
    square = request.POST.get("square")
    max_adults = request.POST.get("max_adults")
    count_room = request.POST.get("count_room")
    count_bedrooms = request.POST.get("count_bedrooms")
    service_list = request.POST.getlist("rservice[]")
    beds = request.POST.get("beds")
    hotel_rooms_str = str(request.POST.get("hotel_rooms"))
    hotel_rooms_list = hotel_rooms_str.split(", ")
    price_base = request.POST.get("price_base")
    the_amount_of_the_security_deposit = request.POST.get(
        "the_amount_of_the_security_deposit")

    if len(the_amount_of_the_security_deposit) < 1:
        the_amount_of_the_security_deposit = "0"

    min_days = request.POST.get("min_days")

    description_of_the_room = request.POST.get("description_of_the_room")

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")
    hotel = Hotel.objects.get(id=select_hotel)

    Hotel.check_hotel_owner(request.user, hotel)



    if id in ["new", "copy"]:
        rc = RCategory.objects.create(
            enable=True,
            name=name,
            hotel=hotel,
            offer_type=offer_type,
            square=square,
            max_adults=max_adults,
            beds=RCategory.beds_str_in_dict(beds),
            description_of_the_room=description_of_the_room,
            count_room=count_room,
            count_bedrooms=count_bedrooms,
            price_base=price_base,
            min_days=int(min_days),
            the_amount_of_the_security_deposit=the_amount_of_the_security_deposit,
        )
        rc.additional_info = {}
        rc.save()
    else:
        rc = RCategory.objects.get(id=id)

    photos_room = request.POST.get("photo_room[]")


    if id == "copy":
        if len(photos_room) > 0:
            first_img_obj_url = None
            photos_room = photos_room.split(",")

            imgs = Img.get_id_to_obj(photos_room)
            for index, img in enumerate(imgs):
                new_img = Img.objects.create(
                    image=img.image,
                    created_date=img.created_date,
                    updated_date=img.updated_date,
                    param=img.param,
                )

                if not first_img_obj_url:
                    first_img_obj_url = img.image.url

                new_img.param["model"] = "hotel.rc"
                new_img.param["obj"] = rc.id
                new_img.param["order"] = index
                img.save()

    else:
        if len(photos_room) > 0:
            first_img_obj_url = None
            photos_room = photos_room.split(",")

            if id != "new":
                imgs_del: QuerySet[Img] = Img.get("hotel.rc", rc.id)

                for img in imgs_del:
                    img.param["model"] = "not_linked"
                    img.save()

            imgs = Img.get_id_to_obj(photos_room)
            for index, img in enumerate(imgs):

                if not first_img_obj_url and img.param.get("order") == 1:
                    first_img_obj_url = img.image.url

                img.param["model"] = "hotel.rc"
                img.param["obj"] = rc.id
                img.param["order"] = index
                img.save()

    if id != "new":
        rc.name = name
        rc.hotel = hotel
        rc.offer_type = offer_type
        rc.square = square
        rc.beds = RCategory.beds_str_in_dict(beds)
        rc.description_of_the_room = description_of_the_room
        rc.max_adults = max_adults
        rc.count_room = count_room
        rc.count_bedrooms = count_bedrooms
        rc.price_base = price_base
        rc.min_days = int(min_days)
        rc.the_amount_of_the_security_deposit = the_amount_of_the_security_deposit

    if service_list[0] != '':
        service_list = service_list[0].split(",")
        service = RService.objects.filter(id__in=service_list)
        rc.service.set(service)

    if rc.additional_info == None:
        rc.additional_info = {}

    numbers_param_dict = {}

    the_same_type_of_numbers = request.POST.get("the_same_type_of_numbers")
    if the_same_type_of_numbers:
        numbers_param_dict = list(json.loads(the_same_type_of_numbers).values())

        exist_room_number = [item["name"] for item in numbers_param_dict if item["type"] == "exist"]
        new_room_number = [item["name"] for item in numbers_param_dict if item["type"] == "new"]

        rooms = rc.rooms.all()
        for room in rooms:
            room : Room



            if room.room_number in exist_room_number:
                exist_room_number.remove(room.room_number)
            else:
                bookings : QuerySet[Booking] = room.rbooking.all()
                if not bookings.exists():
                    room.delete()

        for room in new_room_number:
            Room.objects.create(
                category=rc,
                room_number=room,
            )





    # Тарифы питания
    rc.additional_info["food_rate"] = {}
    food_rate = rc.additional_info["food_rate"]

    for key in ["breakfast_lunch_dinner", "breakfast_lunch", "breakfast_dinner", "lunch_dinner", "breakfast", "lunch", "dinner"]:
        if request.POST.get(f"food_rate_{key}"):
            food_rate[key] = request.POST.get(f"food_rate_{key}")

    # Тарифы питания
    rc.additional_info["prepayment_for_the_room_before_checkin"] = 0

    rc.additional_info["prepayment_for_the_room_before_checkin"] = int(request.POST.get(f"prepayment_for_the_room_before_checkin", "0"))
    if rc.additional_info["prepayment_for_the_room_before_checkin"] > 100:
        rc.additional_info["prepayment_for_the_room_before_checkin"] = 100

    if rc.additional_info["prepayment_for_the_room_before_checkin"] < 0:
        rc.additional_info["prepayment_for_the_room_before_checkin"] = 0

    rc.hash_image_update()

    rc.save()

    return JsonResponse(
        {
            "result": True,
            "rc": {
                "id": rc.id,
                "name": rc.name,
                "price_base": rc.price_base,
                "max_adults": rc.max_adults,
                "img": first_img_obj_url,
                "additional_info": rc.additional_info,
                "numbers_param_dict": numbers_param_dict,
            }
        }
    )

def ajax_profile_hotel_rooms_edit_remove(request: HttpRequest):
    rc_id = request.POST.get("rc")
    rc = RCategory.objects.filter(id=rc_id, hotel__owner=request.user).first()

    if not rc:
        raise Http404({"RCategory не найден или не принадлежит пользователю"}   )

    imgs = Img.get("hotel.rc", rc.id)
    for img in imgs:
        img.param = {
                "model": "not_linked",
            }
        img.save()

    rc.delete()

    return JsonResponse({'result': "Ok"})



def page_hotel_price_calendar(request: HttpRequest):
    content = {
        "menu_lk_active": resolve(request.path).url_name,
    }
    return render(request, 'user/v2/price_calendar.html', content)


def get_date_range(date1, date2) -> list[datetime.date]:
    # Создание списка диапазона между двумя датами включительно
    date_range = []
    current_date = date1
    while current_date <= date2:
        date_range.append(current_date)
        current_date += datetime.timedelta(days=1)

    return date_range

def ajax_hotel_price_calendar_weekend_prices_save(request: HttpRequest):
    weekend_prices : dict = json.loads(request.body.decode('utf-8'))

    weekend_prices_keys = list(weekend_prices.keys())
    if len(weekend_prices) > 0:
        rc_id = weekend_prices_keys[0]
        rc = RCategory.objects.filter(id=rc_id).first()
        if not rc:
            return JsonResponse({'result': "Не найдена категория номера"})

        hotel = rc.hotel

        if hotel.owner.id != request.user.id:
            return JsonResponse({'result': "Номера не принадлежат пользователю"})

        hotel.additional_info["weekend_prices"] = weekend_prices

        ppds_dict = []

        for key, weekend_prices_obj in weekend_prices.items():
            rc : RCategory = RCategory.objects.filter(id=key).first()
            for obj in weekend_prices_obj["items"]:
                date1_obj = datetime.datetime.strptime(obj["dates"][0], "%d.%m.%Y").date()
                date2_obj = datetime.datetime.strptime(obj["dates"][1], "%d.%m.%Y").date()

                date_list = get_date_range(date1_obj, date2_obj)
                for date in date_list:
                    day_of_week = (date.weekday() + 1) % 7

                    if obj["weekday"][day_of_week]:
                        defaults = {}
                        if obj["price"]:
                            defaults["price"] = obj["price"]

                        if obj["min_days"]:
                            defaults["days_min"] = obj["min_days"]

                        PricePerDay.objects.update_or_create(
                            date=date,
                            rc=rc,
                            defaults=defaults,
                        )

            ppd_dict = {}

            for ppd in PricePerDay.objects.filter(rc=rc):
                ppd_dict[ppd.date.strftime("%d.%m.%Y")] = {
                    "price": ppd.price,
                    "days_min": ppd.days_min,
                }

            rc.additional_info["ppds"] = ppd_dict

            ppds_dict.append({
                "rc": rc.name,
                "ppds": ppd_dict,
            })

            rc.save()

        hotel.save()



    if len(weekend_prices.items()) == 0:
        hotel_id = request.session.get('hotel')
        hotel = Hotel.objects.get(id=hotel_id)
        Hotel.check_hotel_owner(request.user, hotel)
        hotel.additional_info["weekend_prices"] = {}
        hotel.save()

    return JsonResponse({'result': "Ok", "param": weekend_prices})

def ajax_hotel_price_calendar_weekend_prices_get(request: HttpRequest):
    hotel_id = request.session.get('hotel')
    hotel = Hotel.objects.get(id=hotel_id)
    Hotel.check_hotel_owner(request.user, hotel)
    weekend_prices = hotel.additional_info.get("weekend_prices", {})

    return JsonResponse({'weekend_prices': weekend_prices})



def page_hotel_booking_chess(request: HttpRequest):
    content = {
        "menu_lk_active": resolve(request.path).url_name,
    }
    return render(request, 'user/v2/booking_chess.html', content)



def page_hotel_reviews(request: HttpRequest):

    content = {
        "menu_lk_active": resolve(request.path).url_name,
    }

    return render(request, 'user/v2/hotel_reviews.html', content)


def page_reviews(request: HttpRequest):

    content = {
        "menu_lk_active": resolve(request.path).url_name,
    }

    return render(request, 'user/v2/reviews.html', content)


def ajax_get_review(request: HttpRequest):
    # Получение списка отзывов из базы данных с помощью ORM
    reviews_qs = Comment.objects.filter(user=request.user).order_by("-date")

    # Формирование списка отзывов для возврата в ответе
    results = []
    for review in reviews_qs:
        review: Comment

        imgs = Img.get_url_list("hotel.comment", review.id)

        hotel_name = review.rc.hotel.name

        results.append({
            "id": review.id,
            'username': hotel_name,
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
    content = {
        'results': results,
    }

    return JsonResponse(content)


def page_ts(request: HttpRequest):

    content = {}

    return render(request, 'user/v2/ts.html', content)



def page_new_login(request: HttpRequest):

    content = {}

    return render(request, 'user/v2/reglogin.html', content)
