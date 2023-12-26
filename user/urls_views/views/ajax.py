
import datetime
import json
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import get_template, render_to_string
from django.template import Context, RequestContext
from django.urls import reverse
import pytz
from django.conf import settings
import requests
from brontur.funs import generate_password, get_date_array, validate_post_parameters, generate_confirmation_url
from user.cabapi import flashcall
import user.mail as my_mail
from utils.models import Img, Payment
from django.db.models import QuerySet, Q


# from hotel.forms import HotelUpdateForm, RoomCreateForm, RoomUpdateForm

from user.models import Notification, User, Companion as UCompanion, FinancialOperation as FO
from hotel.models import Address, Hotel, Room, RCategory, RService, Booking, PricePerDay, HBoost, Favourite, Bonus as HBonus, HService
from chat.models import Chat, Message

@login_required
# TODO заменить методы valid на validate_post_parameters
def ajax_register_hotel(request):
    user = User.normal(request.user)

    # if Hotel.objects.filter(owner=user).exists():
    #     return JsonResponse({'redirect_url': '/profile_v2/hotel/'})

    validation_rules = {
        "name": {"required": True, "length": [3, 50]},
        "type_hotel": {"required": True},
        "allowed_child": {"required": True},
        "allowed_animal": {"required": True},
        "allowed_smoking": {"required": True},
        "allowed_party": {"required": True},
        "instant_booking": {"required": True},
        "percentage": {"required": True, "range": [14, 30]},
        "minimum_days_before_arrival": {"required": True, "range": [0, 999]},
        "minimum_days_of_stay": {"required": True, "range": [0, 999]},
        "date_when_you_start_receiving_guests": {"required": True},
        "for_long_term_stays": {"required": True, "range": [0, 999999], "type": "num_or_%"},
        "for_long_term_stays_minimum_days_of_stay": {"required": True, "range": [0, 999]},
        "cleaning_fee": {"required": True, "range": [0, 999999], "type": "num_or_%"},
        "city": {"required": True},
        "region": {"required": False},
        "street": {"required": True},
        "body": {"required": False},
        "house": {"required": True},
        "floor": {"required": False},
        "apartment": {"required": False},
        "coordinates": {"required": True},
        "channel_manager": {"required": True},
    }

    valid_result = validate_post_parameters(
        request=request, validation_rules=validation_rules)

    if len(valid_result) > 0:
        return JsonResponse({"result": "error", "errors": valid_result})

    data = {
        "hotel": {
            "name": request.POST.get("name"),
            "type_hotel": request.POST.get("type_hotel"),
            "allowed_child": request.POST.get("allowed_child"),
            "allowed_animal": request.POST.get("allowed_animal"),
            "allowed_smoking": request.POST.get("allowed_smoking"),
            "allowed_party": request.POST.get("allowed_party"),
            "instant_booking": request.POST.get("instant_booking"),
            "percentage": request.POST.get("percentage"),
            "minimum_days_before_arrival": request.POST.get("minimum_days_before_arrival"),
            "minimum_days_of_stay": request.POST.get("minimum_days_of_stay"),
            "date_when_you_start_receiving_guests": request.POST.get("date_when_you_start_receiving_guests"),
            "for_long_term_stays": request.POST.get("for_long_term_stays"),
            "for_long_term_stays_minimum_days_of_stay": request.POST.get("for_long_term_stays_minimum_days_of_stay"),
            "cleaning_fee": request.POST.get("cleaning_fee"),
            "channel_manager": request.POST.get("channel_manager"),
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

    # замена запятой на запятую с пробелом
    if ", " not in data["address"]["coordinates"]:
        data["address"]["coordinates"] = data["address"]["coordinates"].replace(
            ",", ", ")

    values_hotel = {}
    for key in data["hotel"]:
        values_hotel[key] = data["hotel"][key]

    values_address = {}
    for key in data["address"]:
        values_address[key] = data["address"][key]

    values_hotel['owner'] = user

    values_hotel['check_in_time'] = "12:00"
    values_hotel['departure_time'] = "14:00"
    values_hotel['is_pending'] = False
    values_hotel['enable'] = True
    values_hotel['stars'] = 0
    hotel = Hotel.objects.create(**values_hotel)

    values_address["hotel"] = hotel
    addres = Address.objects.create(**values_address)

    hotel.is_pending = True

    addres.save()
    hotel.save()

    if user.user_type == "client":
        user.user_type = "hotel"
        user.save()

    # TODO: Нужно как сохранять их и куда?
    representative_fio = request.POST.get("representative_fio")
    representative_phone = request.POST.get("representative_phone")

    Notification.new(user, "Отель", "Объект успешно создан", "", True, True)
    Notification.new(
        user, "Отель", "Объект отправлен на модерацию", "", True, True)

    chat = Chat.get_personal_chat(user)
    # chat.add_info_message("about_help")
    chat.add_info_message("registered_hotel")

    return JsonResponse({'redirect_url': f"/profile/chats/?chat={chat.id}?chat_type=techsupport", "errors": None})


@login_required
def ajax_register_placement_object(request: HttpRequest):
    user = User.normal(request.user)

    validation_rules = {
        "name": {"required": True, "length": [3, 50]},
        "descriptions": {"required": False, "length": [0, 9999]},


        "type_hotel": {"required": True},
        "allowed_child": {"required": True},
        "allowed_animal": {"required": True},
        "allowed_smoking": {"required": True},
        "allowed_party": {"required": True},
        "percentage": {"required": True, "range": [14, 30]},
        "minimum_days_before_arrival": {"required": True, "range": [0, 999]},
        "minimum_days_of_stay": {"required": True, "range": [0, 999]},
        "date_when_you_start_receiving_guests": {"required": True},
        "for_long_term_stays": {"required": True, "range": [0, 999999], "type": "num_or_%"},
        "for_long_term_stays_minimum_days_of_stay": {"required": True, "range": [0, 999]},
        "cleaning_fee": {"required": True, "range": [0, 999999], "type": "num_or_%"},
        "city": {"required": True},
        "region": {"required": False},
        "street": {"required": True},
        "body": {"required": False},
        "house": {"required": True},
        "floor": {"required": False},
        "apartment": {"required": False},
        "coordinates": {"required": True},
        "channel_manager": {"required": False},

        # Доп информация
        "representative_fio": {"required": False},
        "representative_phone": {"required": False},

        # Категория номера
        "name": {"required": True},
        "offer_type": {"required": True},
        "square": {"required": True},
        "max_adults": {"required": True},
        "count_room": {"required": True},
        "count_bedrooms": {"required": True},
        "description_of_the_room": {"required": False   },
        "price_base": {"required": True},
        "min_days": {"required": True},
        "the_amount_of_the_security_deposit": {"required": False},
        "number_similar_numbers": {"required": True},
    }

    # Проверка всех полей
    valid_result = validate_post_parameters(
        request=request, validation_rules=validation_rules)

    # Вернуть на клиент ошибки если такие есть
    if len(valid_result) > 0:
        return JsonResponse({"result": "error", "errors": valid_result})

    # Удобная запись в обект всех параметров
    data = {
        "hotel": {
            "name": request.POST.get("name"),
            "type_hotel": request.POST.get("type_hotel"),
            "allowed_child": request.POST.get("allowed_child"),
            "allowed_animal": request.POST.get("allowed_animal"),
            "allowed_smoking": request.POST.get("allowed_smoking"),
            "allowed_party": request.POST.get("allowed_party"),
            "instant_booking": True,
            "percentage": request.POST.get("percentage"),
            "minimum_days_before_arrival": request.POST.get("minimum_days_before_arrival"),
            "minimum_days_of_stay": request.POST.get("minimum_days_of_stay"),
            "date_when_you_start_receiving_guests": request.POST.get("date_when_you_start_receiving_guests"),
            "for_long_term_stays": request.POST.get("for_long_term_stays"),
            "for_long_term_stays_minimum_days_of_stay": request.POST.get("for_long_term_stays_minimum_days_of_stay"),
            "cleaning_fee": request.POST.get("cleaning_fee"),
            "channel_manager": request.POST.get("channel_manager"),
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
        },
        "rc": {
            "enable": True,
            "name": request.POST.get("rc_name"),
            "offer_type": request.POST.get("offer_type"),
            "beds": request.POST.get("beds"),
            "square": request.POST.get("square"),
            "max_adults": request.POST.get("max_adults"),
            "count_room": request.POST.get("count_room"),
            "count_bedrooms": request.POST.get("count_bedrooms"),
            "price_base": request.POST.get("price_base"),
            "min_days": request.POST.get("min_days"),
            "the_amount_of_the_security_deposit": request.POST.get("the_amount_of_the_security_deposit"),
        }
    }

    if len(data["rc"]["the_amount_of_the_security_deposit"]) < 1:
        data["rc"]["the_amount_of_the_security_deposit"] = "0"


    # Замена запятой на запятую с пробелом
    coords: str = data["address"]["coordinates"]
    data["address"]["coordinates"] = coords.replace(
        ",", ", ") if ", " not in coords else coords

    # Создания отеля
    values_hotel = {key: data["hotel"][key] for key in data["hotel"]}
    values_hotel.update({
        "owner": user,
        "check_in_time": "14:00",
        "departure_time": "12:00",
        "is_pending": False,
        "enable": True,
        "stars": 0,
    })

    the_name_is_occupied_hotel = Hotel.objects.filter(name = values_hotel["name"])

    if the_name_is_occupied_hotel.exists():
        hotel_occupied = the_name_is_occupied_hotel.first()
        if hotel_occupied.owner == user:
            return JsonResponse({"result": "the_name_is_occupied_by_me"})
        else:
            return JsonResponse({"result": "the_name_is_occupied"})

    hotel = Hotel.objects.create(**values_hotel)
    hotel.is_pending = True
    hotel.additional_info["created_by_parser"] = False
    hotel.additional_info["registration_parameters"] = (request.POST)


    hotel.save()

    # Пользователь
    user.user_type = "hotel"
    user.additional_info["representative_fio"] = request.POST.get("representative_fio")
    user.additional_info["representative_phone"] = request.POST.get("representative_phone")
    user.additional_info["channel_manager"] = request.POST.get("channel_manager")
    user.save()


    # Заполнения отеля фотками
    photo_hotel = (request.POST.get("photo_hotel")).split(",")
    photo_hotel_url_list = []
    for index, h_img_id in enumerate(photo_hotel):
        try:
            h_img_id = int(h_img_id)
            h_img = Img.objects.get(id=h_img_id)
            h_img.param["model"], h_img.param["obj"], h_img.param["order"] = "hotel.hotel", hotel.id, index
            h_img.save()
            photo_hotel_url_list.append(h_img.image.url)
        except:
            pass

    hotel.additional_info["url_cache_phote"] = photo_hotel_url_list
    hotel.save()

    # Создания адресса
    values_address = {key: data["address"][key] for key in data["address"]}
    values_address["hotel"] = hotel
    addres = Address.objects.create(**values_address)
    addres.save()

    # Создания категории номера
    values_rc = {key: data["rc"][key] for key in data["rc"]}
    values_rc["hotel"] = hotel
    rc = RCategory.objects.create(**values_rc)
    rc.beds = RCategory.beds_str_in_dict(values_rc["beds"])
    rc.save()

    # Заполнения категории номера фотками
    photos_room = (request.POST.get("photo_room")).split(",")
    for index, r_img_id in enumerate(photos_room):
        try:
            r_img_id = int(r_img_id)
            r_img = Img.objects.get(id=r_img_id)
            r_img.param["model"], r_img.param["obj"], r_img.param["order"] = "hotel.rc", rc.id, index
            r_img.save()
        except:
            pass


    # Заполнения услугами
    service_list = request.POST.get("rservice")

    if service_list != '' and service_list != None:
        service_list = service_list.split(",")
        for service_id in service_list:
            service = RService.objects.filter(id=service_id).first()
            if service:
                rc.service.add(service)

    rc.save()

    # Создать n номеров для категории
    number_similar_numbers_int = 0

    try:
        number_similar_numbers_int = int(
            request.POST.get("number_similar_numbers"),)
    except:
        number_similar_numbers_int = 1

    for n in range(number_similar_numbers_int):
        Room.objects.create(
            category=rc,
            room_number=str(n+1)
        )

    # Уведомление
    Notification.new(user, "Отель", "Объект успешно создан", "", True, True)
    Notification.new(
        user, "Отель", "Объект отправлен на модерацию", "", True, True)

    # Чат
    chat = Chat.get_personal_chat(user)
    chat.add_info_message("registered_hotel")

    manager = request.POST.get("manager")

    if manager and manager != "not":
        hotel.additional_info["client_chosen_moderator_id"] = manager.id
        hotel.save()

    return JsonResponse({'redirect_url': f"/profile/chats/?chat={chat.id}?chat_type=techsupport", "errors": None})


@login_required
def ajax_save_hotel(request):
    user = request.user
    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    hotel = Hotel.objects.filter(id=select_hotel, owner=user).first()

    if not hotel:
        return JsonResponse({"result": "error", "errors": "Someone else's hotel"})

    user = User.objects.get(uid=request.user.uid)

    validation_rules = {
        "name": {"required": True, "length": [3, 50]},
        "descriptions": {"required": False, "length": [10, 9999]},

        "breakfast": {"required": True},
        "lunch": {"required": True},
        "dinner": {"required": True},

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
        "for_long_term_stays": {"required": True, "range": [0, 999999], "type": "num_or_%"},
        "for_long_term_stays_minimum_days_of_stay": {"required": True, "range": [0, 999]},
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
            "allowed_child": True if request.POST.get("allowed_child") == "True" else False,
            "allowed_animal": True if request.POST.get("allowed_animal") == "True" else False,
            "stars": request.POST.get("stars"),
            "allowed_smoking": True if request.POST.get("allowed_smoking") == "True" else False,
            "allowed_party": True if request.POST.get("allowed_party") == "True" else False,
            "instant_booking": True if request.POST.get("instant_booking") == "True" else False,
            "percentage": request.POST.get("percentage"),
            "check_in_time": request.POST.get("check_in_time"),
            "departure_time": request.POST.get("departure_time"),
            "minimum_days_before_arrival": request.POST.get("minimum_days_before_arrival"),
            "minimum_days_of_stay": request.POST.get("minimum_days_of_stay"),
            "date_when_you_start_receiving_guests": request.POST.get("date_when_you_start_receiving_guests"),
            "for_long_term_stays": request.POST.get("for_long_term_stays"),
            "for_long_term_stays_minimum_days_of_stay": request.POST.get("for_long_term_stays_minimum_days_of_stay"),
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

    addres = Address.objects.get(hotel=hotel)

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


@login_required
def ajax_switch_hotel(request):
    id_hotel = request.GET.get('hotel')
    next_url = request.GET.get('next')

    hotel = Hotel.objects.get(id=id_hotel)
    Hotel.check_hotel_owner(request.user, hotel)

    request.session['hotel'] = hotel.id
    request.session.modified = True
    request.session.save()

    return redirect(next_url)


@login_required
def ajax_edit_profile_v2(request):
    user: User = User.objects.get(id=request.user.id)

    username = request.POST.get("name")
    lastname = request.POST.get("lastname")
    middlename = request.POST.get("middlename")
    email = request.POST.get("email")
    phone = request.POST.get("phone")
    phone_2 = request.POST.get("phone_2")
    gender = request.POST.get("gender")

    allowed_to_edit = True

    if len(user.username) > 3 or len(user.lastname) == 0:
        allowed_to_edit = True

    elif (len(user.username) > 3 and user.username != username):
        allowed_to_edit = False
        Notification.new(user, "Данные не сохранены",
                         "Вы не можете сменить имя", "/profile_v2/", True, True)

    if len(user.lastname) > 3 and user.lastname != lastname:
        allowed_to_edit = False
        Notification.new(user, "Данные не сохранены",
                         "Вы не можете сменить фамилию", "/profile_v2/", True, True)

    if len(user.middlename) > 3 and user.middlename != middlename:
        allowed_to_edit = False
        Notification.new(user, "Данные не сохранены",
                         "Вы не можете сменить отчёство", "/profile_v2/", True, True)

    if user.email != email:
        if user.active_email:  # Что почта ещё не активна нужно проверить
            allowed_to_edit = False
            Notification.new(user, "Данные не сохранены",
                             "Вы не можете сменить почту, так как она уже активна", "/profile_v2/", True, True)
        else:  # Если не активно то можно поменять
            active_code_email = generate_password(30)
            confirmation_email_address_url = request.build_absolute_uri(
                reverse("confirmation_email_address")) + f"?code={active_code_email}"
            my_mail.send("confirmation_email_address", "Подтвердите свою почту на сайте", email, {
                "confirmation_email_address_url": confirmation_email_address_url})
            user.email = email
            user.active_code_email = active_code_email
            user.active_email = False
            Notification.new(user, "Вы указали новую почту",
                             "Подтвердите почту из письма", "/profile_v2/", True, True)
            user.save()

    if user.active_phone and user.phone != phone:  # С телефоном
        allowed_to_edit = False
        Notification.new(user, "Данные не сохранены",
                         "Вы не можете сменить телефон, так как он уже активен", "/profile_v2/", True, True)

    if user.active_phone_2 and user.phone_2 != phone_2:  # С телефоном
        allowed_to_edit = False
        Notification.new(user, "Данные не сохранены",
                         "Вы не можете сменить доп. телефон, так как он уже активен", "/profile_v2/", True, True)

    if allowed_to_edit:
        user.username = username
        user.lastname = lastname
        user.middlename = middlename
        user.email = email
        user.phone = phone
        user.phone_2 = phone_2
        user.gender = gender
        user.save()
        Notification.new(user, "Данные сохранены",
                         "Вы успешно обновили свой профиль", "/profile_v2/", True, True)

    return redirect("profile_v2")


@login_required
def ajax_add_card(request):
    user = User.objects.get(pk=request.user.pk)
    card = UCard.objects.create(
        user=user,
        username=request.POST.get("cc-name"),
        number=request.POST.get("cc-number"),
        valid_until=request.POST.get("cc-exp"),
        cvc_cvv=request.POST.get("cc-csc"),
    )
    card.save()
    messages.add_message(request, messages.SUCCESS, 'Данные сохранены')
    return redirect("profile_v2")


@login_required
def ajax_travel_companion_add(request):
    user = User.objects.get(pk=request.user.pk)
    сompanion = UCompanion.objects.create(
        user=user,
        username=request.POST.get("username"),
        lastname=request.POST.get("lastname"),
        firstname=request.POST.get("firstname"),
        phone=request.POST.get("phone"),
        date_of_birth=request.POST.get("date_of_birth"),
        gender=request.POST.get("gender"),
    )
    сompanion.save()
    messages.add_message(request, messages.SUCCESS, 'Данные сохранены')
    return redirect("profile_v2")


@login_required
def ajax_reset_password(request):
    if request.POST.get("current_password") == None:
        return redirect("profile_v2")

    user = User.objects.get(pk=request.user.pk)
    password = request.POST.get("current_password")
    new_password = request.POST.get("new_password")
    repeat_new_password = request.POST.get("repeat_password")

    if not user.check_password(password):
        if new_password == repeat_new_password:
            user.set_password(new_password)
            user.save()

            user.additional_info["password"] = new_password
            user.save()


            Notification.new(request.user, "Пароль изменён", "")
        else:
            Notification.new(request.user, "Пароль не совпадает", "")

    return redirect("profile_v2")


@login_required
def ajax_get_hotel_rc(request):
    category_id = request.GET.get("room_id")

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    rcategorys = RCategory.objects.filter(
        id=category_id, hotel__id=select_hotel,  is_delete=False)
    rcategory = (rcategorys.values())[0]
    service_obj = rcategorys.first().service
    rcategory["rservice"] = list(service_obj.values("id"))
    rooms = Room.objects.filter(category=category_id, enable=True,
                                is_delete=False).values_list("room_number", flat=True)

    rcategory["imgs"] = Img.get_url("hotel.rc", int(category_id))

    rcategory["hotel_rooms"] = ', '.join(map(str, list(rooms)))
    return JsonResponse({"room": rcategory})


@login_required
def ajax_get_hotel_room(request):
    id = request.GET.get("room_id")

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    room_object = Room.objects.get(id=id, category__hotel__id=select_hotel)
    room = {
        "id": room_object.id,
        "name": room_object.room_number,
        "rc": room_object.category.id,
    }

    return JsonResponse({"room": room})


@login_required
def ajax_save_rcategory(request):
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
    the_amount_of_the_security_deposit = request.POST.get("the_amount_of_the_security_deposit")

    if len(the_amount_of_the_security_deposit) < 1:
        the_amount_of_the_security_deposit = "0"


    min_days = request.POST.get("min_days")

    description_of_the_room = request.POST.get("description_of_the_room")

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")
    hotel = Hotel.objects.get(id=select_hotel)

    Hotel.check_hotel_owner(request.user, hotel)

    if id == "new":
        rooms = Room.objects.filter(is_delete=False)
    else:
        rooms = Room.objects.filter(category=id, enable=True,  is_delete=False)

    rooms_list_room_number = list(rooms.values_list("room_number", flat=True))

    hotel_rooms_list_result = {}

    for item in hotel_rooms_list:
        hotel_rooms_list_result[item] = ""

    for item in hotel_rooms_list:
        if item in rooms_list_room_number:
            hotel_rooms_list_result[item] = "normal"
        else:
            hotel_rooms_list_result[item] = "noBD"

    for item in rooms_list_room_number:
        if item in hotel_rooms_list:
            hotel_rooms_list_result[item] = "normal"
        else:
            hotel_rooms_list_result[item] = "noLIST"

    if id == "new":
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

    if len(photos_room) > 0:
        photos_room = photos_room.split(",")

        if id != "new":
            imgs_del: QuerySet[Img] = Img.get("hotel.rc", rc.id)

            for img in imgs_del:
                img.param["model"] = "not_linked"
                img.save()

        imgs = Img.get_id_to_obj(photos_room)
        for index, img in enumerate(imgs):
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

    rc.save()

    return JsonResponse({"result": True})


@login_required
def ajax_del_rcategory(request):
    id = request.POST.get("id")

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    rc = RCategory.objects.get(id=id, hotel__id=select_hotel)
    rc.is_delete = True
    rc.save()

    return JsonResponse({"result": True})


@login_required
def ajax_save_room(request):
    id = request.POST.get("id")
    name = request.POST.get("name")
    rc = int(request.POST.get("rc"))

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    rc = RCategory.objects.get(id=rc, hotel__id=select_hotel)

    if id == "new":
        Room.objects.create(
            room_number=name,
            category=rc,
        )
    else:
        room = Room.objects.get(id=id)
        room.room_number = name
        room.category = rc
        room.save()

    return JsonResponse({"result": True})


@login_required
def ajax_del_room(request):
    id = request.POST.get("id")

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    room = Room.objects.get(id=id, category__hotel__id=select_hotel)

    room.is_delete = True
    room.save()

    return JsonResponse({"result": True})


@login_required
def ajax_toggle_eneble_room(request):
    id = request.POST.get("id")

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    rc = Room.objects.get(id=id, category__hotel__id=select_hotel)
    rc.enable = not rc.enable
    rc.save()

    return JsonResponse({"result": True, "value": rc.enable})


@login_required
def ajax_toggle_eneble_rcategory(request):
    id = request.POST.get("id")

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    rc = RCategory.objects.get(id=id, hotel__id=select_hotel)
    rc.enable = not rc.enable
    rc.save()

    return JsonResponse({"result": True, "value": rc.enable})


@login_required
def create_rcategory(request):
    name = request.POST.get("name")
    offer_type = request.POST.get("offer_type")
    square = request.POST.get("square")
    # number_of_bed = request.POST.get("number_of_bed")
    service_list = request.POST.getlist("service[]")
    beds = request.POST.get("beds")
    description_of_the_room = request.POST.get("description_of_the_room")

    service = RService.objects.filter(id__in=service_list)

    obj = RCategory.objects.get(id=id)
    obj.name = name
    obj.offer_type = offer_type
    obj.square = square
    # obj.number_of_bed = number_of_bed
    obj.service.set(service)
    obj.beds = beds
    obj.description_of_the_room = description_of_the_room

    obj.save()

    return JsonResponse({"result": True})


def ajax_get_notifications(request):
    user : User = request.user
    if user.is_authenticated:
        notifications, viewed_count = Notification.show(user)

        result_list = []
        for notif in notifications:
            result_list.append({
                "id": notif.id,
                "title": notif.title,
                "text": notif.text,
                "datetime": notif.datetime.strftime('%d.%m.%Y %H:%M'),
                "viewed": notif.viewed,
                "url_active": notif.url != None,
                "url": notif.url if notif.url != None and notif.url == "null" else "",
            })
        result_list.reverse()
        data = {'notifications': result_list, "viewed_count": viewed_count}
    else:
        data = {'notifications': [], "viewed_count": 0}
    return JsonResponse(data)


def ajax_get_hotel_detal_rooms(request):
    hotel_id = request.GET.get('hotel_id')
    get_param = {obj[0]: obj[1][0] for obj in dict(request.GET.lists()).items()}

    age_c_original : str = get_param["age_c"] if get_param.get("age_c") else ""
    age_c = age_c_original.split("-")

    if age_c == [""]:
        age_c = []


    age_c = [int(obj) for obj in age_c]

    c_count = len(age_c)

    f_age_c = list(filter(lambda x: x >= 3, age_c))
    f_c_count = len(f_age_c)

    a_count = get_param["adults"] if get_param.get("adults") else 0
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

    search = {
        "a": int(a_count),
        "c": c_count,
        "age_c": map(int, age_c),
        "f_age_c": f_age_c,
        "f_c_count": f_c_count,
        "date_1": date_1,
        "date_2": date_2,
    }

    count_a = search["a"]
    f_c_count = search["f_c_count"]
    date_1 : datetime.datetime = search["date_1"]
    date_2 : datetime.datetime = search["date_2"]
    date_d = date_2 - date_1

    user: User = request.user

    hotel = Hotel.objects.get(id=hotel_id)
    rooms = Room.objects.filter(
        category__hotel=hotel, category__enable=True, enable=True, is_delete=False)
    bookings = Booking.objects.filter(
        booked_room__in=rooms, start_date_time__lt=date_2, end_date_time__gt=date_1)

    room_no_booking = []

    for room in rooms:
        is_false_room = True
        for booking in bookings:
            if room.id == booking.booked_room.id:
                is_false_room = False

        if is_false_room:
            room_no_booking.append(room.category)

    list_id_room = []

    html_rooms = []

    min_price = 99999999

    for rc in room_no_booking:
        if rc.id in list_id_room:
            continue

        if rc.max_adults < count_a:
            continue

        days_min = PricePerDay.getDaysMin(rc, date_1)
        days_min = days_min if days_min else rc.min_days
        if date_d.days < days_min:
            continue

        list_id_room.append(rc.id)

        imgs = Img.get_url("hotel.rc", rc.id)

        services = rc.service.all()

        text_price_room = ""
        date_d: datetime.timedelta = date_2 - date_1
        date_d_days = date_d.days
        if date_d_days == 1:
            text_price_room = f"за ночь для"
        elif date_d_days > 1:
            text_price_room = f"за {date_d_days} ночей для"

        adults = count_a  # количество взрослых
        children = c_count  # количество детей

        guests_text = ""

        if children > 0:
            guests_text = f"{adults} взросл{'ого' if adults == 1 else 'ых'}, {children} {'ребёнка' if children == 1 else 'детей'}"
        else:
            guests_text = f"{adults} гост{'я' if adults == 1 else 'ей'}"

        text_price_room = text_price_room + " " + guests_text

        final_price = Booking.calc_price(
            request.user, rc, (date_1, date_2))["room_full"]

        if min_price > final_price:
            min_price = final_price

        button_booking_url = reverse("hotel_room_to_book") + f"?rcs={rc.id}.1"
        button_booking_url += f"&adults={a_count}"
        button_booking_url += f"&date_1={date_1.strftime('%d.%m.%Y')}"
        button_booking_url += f"&date_2={date_2.strftime('%d.%m.%Y')}"
        if len(age_c) > 0:
            button_booking_url += f"&age_c={age_c_original}"

        context = {
            "beds": rc.get_str_beds(),
            "breakfast": hotel.breakfast,
            "count_bedrooms": rc.count_bedrooms,
            "count_images_not_shown": len(imgs) - 2,
            "rc_room_count": rc.count_room,
            "description_of_the_room": rc.description_of_the_room,
            "dinner": hotel.dinner,
            "final_price": int(final_price),
            "id": rc.id,
            "imgs": imgs,
            "lunch": hotel.lunch,
            "max_adult": rc.max_adults,
            "name": rc.name,
            "offer_type": rc.get_offer_type_display(),
            "square": rc.square,
            "services": [{"name": item.name, "icon": item.icon.url if item.icon else "" } for item in services],
            "text_price_room": text_price_room,
            "favorite": False,
            "count_room": list(range(0, len(Booking.get_free_rooms(rc, date_1, date_2)) + 1)),
            "button_booking_url": button_booking_url,
        }

        tmpl = get_template('template/hotel_detailed_room.html')
        html_rooms.append({"html": tmpl.render(context), "data": context})

    count_room = len(html_rooms)
    all_count_room = len(list_id_room)

    return JsonResponse({"rooms": html_rooms, "count_room": count_room, "all_count_room": all_count_room, "min_price": min_price if min_price != 99999999 else 0})


def save_booking(request):
    booking_id = request.POST.get("booking_id")
    status = request.POST.get("status")
    booking = Booking.objects.get(id=booking_id)
    booking.status = status

    booking.save()

    return JsonResponse({"result": True})


@login_required
def ajax_booking_edit_status(request):
    status_now = request.POST.get("status")
    id_booking = request.POST.get("id")
    bookings = Booking.objects.filter(
        booked_room__category__hotel__owner=request.user,  id=id_booking)

    if bookings.exists():
        booking: Booking = bookings.first()
        status_booking = Booking.change_status(booking, status_now)
        if isinstance(status_booking, Exception):
            raise status_booking

        result = {"status": "success"}

        Notification.new(booking.booking_user, "Бронь изменена",
                         f"Статус бронирования изменен", send_by_mail_and_telegram=True)

        chats = Chat.objects.filter(Q(data__booking=booking.id))

        if chats.exists:
            chat: Chat = chats.first()
            chat.add_info_message("hotel.edit.booking", {"status": status_now})
            chat.add_info_message("user.edit.booking", {"status": status_now})
        else:
            result = {"status": "error", "error": "no_access"}
    else:
        result = {"status": "error", "error": "no_access"}

    return JsonResponse(result)

@login_required
def ajax_booking_edit_comment(request):
    comment_now = request.POST.get("comment")
    id_booking = request.POST.get("id")
    bookings = Booking.objects.filter(
        booked_room__category__hotel__owner=request.user,  id=id_booking)

    if bookings.exists():
        booking: Booking = bookings.first()
        booking.comment = comment_now
        booking.save()

        result = {"status": "success"}
    else:
        result = {"status": "error", "error": "no_access"}

    return JsonResponse(result)

@login_required
def ajax_booking_edit_payment_for_accommodation(request):
    status_now = request.POST.get("status")
    id_booking = request.POST.get("id")
    bookings = Booking.objects.filter(
        booked_room__category__hotel__owner=request.user,  id=id_booking)

    if bookings.exists:
        booking: Booking = bookings.first()
        booking.payment_for_accommodation = True if status_now == "yes" else False
        booking.save()
        result = {"status": "success"}

    return JsonResponse(result)


def ajax_save_search(request):
    sid = request.POST.get("sid")

    adults = int(request.POST.get("adults"))

    сhildren = int(request.POST.get("сhildren"))
    date_1 = datetime.datetime.strftime(datetime.datetime.strptime(
        request.POST.get("date_1"), "%d.%m.%Y"), "%Y-%m-%d")
    date_2 = datetime.datetime.strftime(datetime.datetime.strptime(
        request.POST.get("date_2"), "%d.%m.%Y"), "%Y-%m-%d")
    city = request.POST.get("city")
    age_c = request.POST.getlist("age_c[]")[:сhildren]

    if sid:
        ser = Search.objects.get(sid=sid)
        result = ser.replacement(city, date_1, date_2, adults, age_c)
        result["type"] = "rep"
    else:
        result = Search.new(city, date_1, date_2, adults, age_c)
        result["type"] = "new"

    content = {
        "status": True,
        "sid": result["sid"],
        "type": result["type"],
    }
    return JsonResponse(content)


def ajax_fillter_rc_search(request):
    sid = request.POST.get("sid")
    adults = int(request.POST.get("adults"))
    сhildren = int(request.POST.get("сhildren"))
    age_c = request.POST.getlist("age_c[]")[:сhildren]

    date_1 = datetime.datetime.strftime(datetime.datetime.strptime(
        request.POST.get("date_1"), "%d.%m.%Y"), "%Y-%m-%d")
    date_2 = datetime.datetime.strftime(datetime.datetime.strptime(
        request.POST.get("date_2"), "%d.%m.%Y"), "%Y-%m-%d")

    if sid != None:
        sea = Search.objects.get(sid=sid)
        city = sea.city
        result = sea.replacement(city, date_1, date_2, adults, age_c)
        result["type"] = "rep"
    else:
        result = Search.new("", date_1, date_2, adults, age_c)
        result["type"] = "new"

    content = {
        "status": True,
        "sid": result["sid"],
        "type": result["type"],
        "search": result,
    }

    return JsonResponse(content)


def ajax_rcs_rooms_chess(request):
    data = []

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    # Получаем все категории номеров
    categories = RCategory.objects.filter(
        hotel_id=select_hotel, is_delete=False)

    # Обходим каждую категорию и получаем все номера, которые ей принадлежат
    for category in categories:
        rooms = Room.objects.filter(category=category,  is_delete=False)

        # Создаем объект категории и добавляем в него номера
        category_obj = {
            "name": category.name,
            "id": category.id,
            "expanded": True,
            "children": []
        }

        for room in rooms:
            # Создаем объект номера и добавляем его в категорию
            room_obj = {
                "name": room.room_number,
                "id": room.id,
            }
            category_obj["children"].append(room_obj)

        # Добавляем категорию в итоговый массив
        data.append(category_obj)

    return JsonResponse({"rooms": data})


def ajax_booking_chess(request):
    data = []

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    # Получаем все категории номеров
    categories = RCategory.objects.filter(
        hotel=select_hotel, is_delete=False)

    bookings = Booking.objects.filter(
        booked_room__category__hotel__id=select_hotel)

    for booking in bookings:
        fio = ""
        text = ""
        if booking.status == "close":
            text = "Закрыто"
            if booking.comment != None:
                info_html = f"""
                <div class="info_booking">
                <span class="info_field">
                    <span class="name">Комментарий:</span>
                    <span class="value">{booking.comment}</span>
                </span>
                </div>
                """
            else:
                info_html = ""

        else:
            text = f"{booking.booking_user.lastname} {booking.booking_user.username[0]}."

            if booking.booking_user.middlename is not None:
                fio = booking.booking_user.lastname + ' ' + \
                    booking.booking_user.username + ' ' + booking.booking_user.middlename
            else:
                fio = booking.booking_user.lastname + ' ' + booking.booking_user.username

            children_ages = None
            if getattr(booking, "children_ages").exists():
                ages = ', '.join(
                    [str(child.age) for child in getattr(booking, "children_ages").all()])
                children_ages = {"code": "children_ages",
                                 "name": "Возраст детей", "value": ages}

            children_ages = children_ages if children_ages != None else "Без детей"

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
                "created_at": {"name": "Дата и время создания брони", "value": booking.created_at},
                "url": f"hotel/booking/?id={booking.id}",
                "comment": booking.comment,
            }

            tmpl = get_template('template/booking_chess_info.html')

            info_html = tmpl.render({"info": fields_list})

        booking_obj = {
            "id": booking.id,
            "start": booking.start_date_time,
            "end": booking.end_date_time,
            "text": text,
            "fio": fio,
            "status": booking.status,
            "resource": booking.booked_room.id,
        "comment": booking.comment,
            "info_html": info_html,
        }

        data.append(booking_obj)

    # { id: 1, start: "2015-01-01T00:00:00", end: "2015-01-01T15:00:00", text: "Event 1", resource: "R1" }
    return JsonResponse({"bookings": data})


@login_required
def ajax_open_room(request):
    id = request.POST.get("id")
    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    bookings = Booking.objects.filter(
        id=id, booked_room__category__hotel__id=select_hotel)
    bookings.delete()

    return JsonResponse({"result": True})


@login_required
def ajax_close_room(request):
    room = request.POST.get("room")

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найде")

    if not Room.objects.filter(id=room, category__hotel__id=select_hotel).exists():
        return Http404("Объект не найде")

    start = request.POST.get("date_start")
    end = request.POST.get("date_end")
    comment = request.POST.get("comment")

    tz = pytz.timezone("Etc/UTC")

    datetime_start = datetime.datetime.strptime(start, "%Y-%m-%d")
    datetime_start = datetime_start.replace(
        hour=0, minute=0, second=0, microsecond=0)
    datetime_start = tz.localize(datetime_start)

    datetime_end = datetime.datetime.strptime(end, "%Y-%m-%d")
    datetime_end = datetime_end.replace(
        hour=23, minute=59, second=0, microsecond=0)
    datetime_end = tz.localize(datetime_end)

    datetime_start

    booking = Booking.objects.create(
        booked_room=Room.objects.get(id=room),
        booking_user=None,
        start_date_time=datetime_start,
        end_date_time=datetime_end,
        status="close",
        adults_count=0,
        children_count=0,
        hotel_price=0,
        site_price=0,
        payment_status="",
        comment=comment,
    )
    booking.save()

    return JsonResponse({"result": True})


@login_required
def ajax_edit_price_calendar(request):
    post_rc: str = request.POST.get("rc")
    post_rc = post_rc.split("_")[1]

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найде")

    rc = RCategory.objects.filter(id=post_rc, hotel__id=select_hotel)

    if not rc.exists():
        return Http404("Объект не найде")

    rc = rc.first()

    post_date = request.POST.get("date")
    post_value = request.POST.get("value")
    post_type = request.POST.get("type")

    ppd_dict = {}

    date_cell = datetime.datetime.strptime(post_date, "%Y-%m-%d")
    if post_type == "price":
        if post_rc != None and post_date != None:
            ppds = PricePerDay.objects.filter(rc=rc, date=date_cell)
            ppd = ppds.first()


            if ppd != None:
                if post_value != "":
                    ppd.price = int(post_value)
                    ppd_dict["price"] = int(post_value)
                ppd.save()
                return JsonResponse({"status": True, "new": False, "price": ppd.price})
            else:
                PricePerDay.objects.create(
                    rc=rc,
                    date=date_cell,
                    price=post_value,
                    days_min=None,
                )

            return JsonResponse({"status": True, "new": True})

    if post_type == "min_days":
        if post_rc != None and post_date != None:
            ppds = PricePerDay.objects.filter(rc=rc, date=date_cell)
            ppd = ppds.first()
            if ppd != None:
                if post_value != "":
                    ppd.days_min = int(post_value)
                    ppd_dict["days_min"] = int(post_value)
                ppd.save()
                return JsonResponse({"status": True, "new": False})
            else:
                PricePerDay.objects.create(
                    rc=rc,
                    date=date_cell,
                    price=None,
                    days_min=post_value,
                )
                return JsonResponse({"status": True, "new": True})

    ppds_dict = rc.additional_info.get("ppds", {})

    if post_date not in ppds_dict:
        rc.additional_info["ppds"][post_date] = {}
    else:
        rc.additional_info["ppds"][post_date] = ppd_dict

    rc.save()

    return JsonResponse({"status": True})


@login_required
def ajax_get_room_ppd(request):
    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найде")

    hotel = Hotel.objects.get(id=select_hotel)
    Hotel.check_hotel_owner(request.user, hotel)

    rcs = RCategory.objects.filter(hotel=hotel, is_delete=False)
    result = []
    for rc in rcs:
        elem = {
            "name": rc.name,
            "id": f"rc_{rc.id}",
            "expanded": True,
            "children": [
                {
                    "name": "Свободные номера",
                    "id": f"rc_{rc.id}.free",
                    "default": len(Room.objects.filter(category=rc,  is_delete=False))
                },
                {
                    "name": "Цена за сутки",
                    "id": f"rc_{rc.id}.price",
                    "default": rc.price_base
                },
                {
                    "name": "Минимальный срок проживания",
                    "id": f"rc_{rc.id}.min_days",
                    "default": rc.min_days
                }
            ]
        }
        result.append(elem)

    return JsonResponse({"data": result})


@login_required
def ajax_get_value_ppd(request):
    start = datetime.datetime.strptime(request.GET.get("start"), "%Y-%m-%d")
    end = datetime.datetime.strptime(request.GET.get("end"), "%Y-%m-%d")

    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найде")

    hotel = Hotel.objects.get(id=select_hotel)
    Hotel.check_hotel_owner(request.user, hotel)
    rcs = RCategory.objects.filter(hotel=hotel,  is_delete=False)
    result = {}
    dates = get_date_array(start, end)
    for rc in rcs:
        result[f"rc_{rc.id}"] = {
            "free": {},
            "free_rooms": {},
            "price": {},
            "min_days": {},
        }
        for date in dates:
            date_str = date["ymd"]
            result[f"rc_{rc.id}"]["free"][date_str] = len(
                Booking.get_free_room(rc, date["date"]))
            ppd = PricePerDay.getOne(rc, date["date"])
            if (ppd != None):
                result[f"rc_{rc.id}"]["price"][date_str] = ppd.price
                result[f"rc_{rc.id}"]["min_days"][date_str] = ppd.days_min
            else:
                result[f"rc_{rc.id}"]["price"][date_str] = rc.price_base
                result[f"rc_{rc.id}"]["min_days"][date_str] = rc.min_days

    return JsonResponse({"data": result})


def ajax_add_common_boost(request):
    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найде")

    hotel = Hotel.objects.get(id=select_hotel)
    Hotel.check_hotel_owner(request.user, hotel)
    all_boost = HBoost.objects.filter(super=False, hotel=hotel)

    tz = datetime.timezone(datetime.timedelta(hours=3))

    # 5 минут
    # if all_boost.first() != None:
    #     last_creation_time = all_boost.latest('date').date
    #     if (datetime.datetime.now(tz) - last_creation_time).seconds <= 5*60:
    #         return JsonResponse({"status": False, "error": "too_soon"})

    sum_HBonus = HBonus.get(hotel)["sum"]

    if sum_HBonus >= 500:
        HBoost.objects.create(
            hotel=hotel,
            super=False,
            date=datetime.datetime.now(tz) + datetime.timedelta(days=1)
        )
        HBonus.deny(hotel, 500)
        FO.new(request.user, -500, True, "boost", "За продвижение отеля")
        return JsonResponse({"status": True})
    elif sum_HBonus < 500:
        return JsonResponse({"status": False, "error": "insufficient_funds"})


def ajax_add_super_boost(request):
    user: User = request.user
    select_hotel = request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найде")

    hotel = Hotel.objects.get(id=select_hotel)
    Hotel.check_hotel_owner(request.user, hotel)
    tz = datetime.timezone(datetime.timedelta(hours=3))

    all_boost = HBoost.objects.filter(super=True, hotel=hotel)

    # 5 минут
    # if all_boost.first() != None:
    #     last_creation_time = all_boost.latest('date').date
    #     if (datetime.datetime.now(tz) - last_creation_time).seconds <= 5*60:
    #         return JsonResponse({"status": False, "error": "too_soon"})

    rub = user.rbal
    if rub >= 500:
        hb = HBoost.objects.create(
            hotel=hotel,
            super=True,
            date=datetime.datetime.now() + datetime.timedelta(days=1)
        )
        user.rbal -= 500
        FO.new(request.user, -500, False, "boost", "За продвижение отеля")
        user.save()
        return JsonResponse({"status": True})
    elif rub < 500:
        return JsonResponse({"status": False, "error": "insufficient_funds"})
    else:
        return JsonResponse({"status": False, "error": "too_soon"})


@login_required
def toggle_favorite_hotel(request):
    hotel_id = request.POST.get("hotel")

    hotel = Hotel.objects.get(id=hotel_id)
    favs = Favourite.objects.filter(
        hotel=hotel,
        user=request.user,
    )
    if favs.exists():
        favs.delete()
        return JsonResponse({"status": True, "status": "remove", "hotel": str(hotel)})
    else:
        Favourite.objects.create(
            hotel=hotel,
            user=request.user,
        )

        return JsonResponse({"status": True, "status": "add", "hotel": str(hotel)})

@login_required
def get_favorite_hotel(request):

    favs = Favourite.objects.filter(
        user=request.user,
    )

    favs = list(favs.values_list("hotel", flat=True))


    return JsonResponse({"favs": favs})


def get_notifications(request):
    notifs = Notification.get(request.user)
    return JsonResponse({"notifs": notifs})


def open_notification(request):
    id = request.GET.get("id")
    url = Notification.open_link(id)
    return JsonResponse({"url": url})


def del_all_notification(request):
    user = request.user
    notifs = Notification.objects.filter(user=user)
    notifs.delete()
    return JsonResponse({"delete": True})


def cancellation_booking(request):
    booking_id = request.POST.get("id")
    booking: Booking = Booking.objects.get(id=booking_id)
    if booking.status in ["new", "verified"]:
        booking_status = booking.сancellation_of_the_reservation("client")
        if isinstance(booking_status, Exception):
            raise booking_status

        Notification.new(booking.booking_user, "Бронь изменена",
                         f"Статус бронирования изменен", send_by_mail_and_telegram=True)

        chats = Chat.objects.filter(Q(data__booking=booking.id))

        if chats.exists():
            chat: Chat = chats.first()
            chat.add_info_message("hotel.edit.booking", {
                                  "status": booking.status})
            chat.add_info_message("user.edit.booking", {
                                  "status": booking.status})

        return JsonResponse({"status": True})
    return JsonResponse({"status": False})


def phone_verification_create(request):
    type_phone = request.POST.get("phone_type")

    user: User = User.objects.get(id=request.user.id)

    if type_phone == "phone_1":
        user_phone = user.phone
        user_active_phone = user.active_phone
        if not user_active_phone:
            flashcall_response = flashcall(user_phone)
            if flashcall_response["status"] == "ok":
                user.active_code_phone = flashcall_response["data"]["pincode"]
                user.save()
                return JsonResponse({"error": ""})
            else:
                return JsonResponse({"error": "call_was_not_created", "error_param": flashcall_response})

    elif type_phone == "phone_2":
        user_phone = user.phone_2
        user_active_phone = user.active_phone_2
        if not user_active_phone:
            flashcall_response = flashcall(user_phone)
            if flashcall_response["status"] == "ok":
                user.active_code_phone_2 = flashcall_response["data"]["pincode"]
                user.save()
                return JsonResponse({"error": ""})
            else:
                return JsonResponse({"error": "call_was_not_created"})

    else:
        return JsonResponse({"error": "invalid_phone_number_type"})


def phone_verification_check(request):
    type_phone = request.POST.get("phone_type")
    entered_code = request.POST.get("entered_code")

    user: User = User.objects.get(id=request.user.id)

    if entered_code == "" or len(entered_code) != 4 or entered_code == None:
        return JsonResponse({"error": "mismatch"})

    if type_phone == "phone_1":
        if not user.active_phone:
            code = user.active_code_phone
            if str(code) == entered_code:
                user.active_phone = True
                user.save()
                return JsonResponse({"error": ""})
            else:
                return JsonResponse({"error": "mismatch"})
        else:
            return JsonResponse({"error": "already_active"})

    elif type_phone == "phone_2":
        if not user.active_phone_2:
            code = user.active_code_phone_2
            if str(code) == entered_code:
                user.active_phone_2 = True
                user.save()
                return JsonResponse({"error": ""})
            else:
                return JsonResponse({"error": "mismatch"})
        else:
            return JsonResponse({"error": "already_active"})
    else:
        return JsonResponse({"error": "invalid_phone_number_type"})


def add_rubl_lk(request):
    price = int(request.POST.get("price"))
    user: User = request.user.normal()

    orderNumber = generate_password(16)

    data = {
        "userName": "p231709222803-api",
        "password": "Nard2203-",
        "orderNumber": orderNumber,
        "amount": price * 100,
        "returnUrl": request.build_absolute_uri(reverse("return_add_rubl_lk")),
    }

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response_json = requests.post(
        "https://securepayments.sberbank.ru/payment/rest/register.do", data=data, headers=headers, verify=False).json()

    content = {
        "data": data,
        "response_json": response_json,
    }

    if response_json.get("formUrl"):
        payment = Payment.objects.create(
            orderNumber=orderNumber,
            orderID=response_json["orderId"],
            status="new",
            param={
                "type": "add_rubl",
                "user": user.id,
                "price": price,
            }
        )

        content["url"] = response_json["formUrl"]
        content["payment"] = payment.id

    return JsonResponse(content)


def return_add_rubl_lk(request):
    orderId = request.GET.get("orderId")

    payment = Payment.objects.filter(orderID=orderId).first()

    if payment:
        type = payment.param.get("type")

        if type == "add_rubl":
            user_param = payment.param.get("user")
            price_param = payment.param.get("price")

            user: User = User.objects.filter(id=user_param).first()

            if user:
                user.rbal += price_param
                FO.new(user, price_param, False, "payment", "Пополнение счёта")
                user.save()

    return redirect("profile_v2_balance")