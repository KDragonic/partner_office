import datetime
import json
import locale
import math
from geopy.distance import geodesic
from time import strptime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.template.loader import get_template, render_to_string
from django.urls import reverse
import requests
from brontur.funs import add_meta, generate_password, distance
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
from hotel.models import PricePerDay
from django.forms.models import model_to_dict

from django.db.models import Q

from user.models import User, Notification, Companion, Bonus_rubles, FinancialOperation
from user.mail import send as send_mail
from django.db.models import Count

from django.http import HttpRequest, HttpResponse, JsonResponse

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.core.management import call_command

from django.http import Http404

from utils.models import Constant, Img, Place

from django.core.paginator import Paginator

from django.core.files.storage import FileSystemStorage


def collect_room_parameters(get_param: dict) -> dict:
    """Собрать из get парметров - параметры номеров в поисковике

    Args:
        get_param (dict): GET параметры

    Returns:
        dict: Данные номеров из поисковика
    """
    roomsData = []

    index = 0
    while True:
        room = {}
        if f'a{index}' in get_param:
            room['adults'] = int(get_param[f'a{index}'][0])
        else:
            break

        if f'ca{index}' in get_param and get_param[f'ca{index}'][0] != '':
            room['childrens_age'] = [
                int(age) for age in get_param[f'ca{index}'].split(',')]
        else:
            room['childrens_age'] = []

        room["id"] = index

        roomsData.append(room)
        index += 1

    return roomsData


def create_review(request: HttpRequest):
    if request.method == 'POST':
        param = request.POST.dict()

        hotel = Hotel.objects.filter(id=param.get("hotel_id")).first()
        booking = Booking.objects.filter(id=param.get("booking"), status__in=["verified", "settled", "left"]).first()
        user = request.user if request.user.is_authenticated else None

        if not hotel:
            return JsonResponse({'success': False, 'error': 'The placement object was not found'})

        if not booking:
            return JsonResponse({'success': False, 'error': 'Reservation not found'})

        if not user:
            return JsonResponse({'success': False, 'error': 'User not found'})

        date=datetime.datetime.now()

        rc = booking.booked_room.category
        comment = Comment.objects.create(
            hotel=hotel,
            rc=rc,
            user=user,
            date=date,
            location=param.get("location", 0),
            price_quality_ratio=param.get("price_quality_ratio", 0),
            purity=param.get("purity", 0),
            food=param.get("food", 0),
            service=param.get("service", 0),
            number_quality=param.get("number_quality", 0),
            hygiene_products=Comment.convert_value("-hygiene", param.get("hygiene_products", 0))["text"],
            wifi_quality=Comment.convert_value("-wifi", param.get("wifi_quality", 0))["text"],
            what_is_good_text=param.get("what_is_good_text", None),
            what_is_bad_text=param.get("what_is_bad_text", None),
            is_pending=True,
        )


        # обрабатываем каждый файл
        for file in request.FILES.getlist('files'):
            Img.new("hotel.comment", comment.id, file.file)



        # Дать бонусы
        result_calc = Constant.cashback_calculation(hotel.type_hotel, "review", booking.site_price, booking.calc_price(booking.booked_room.category, [booking.start_date_time, booking.end_date_time])["room_full"])
        Bonus_rubles.objects.create(
            user=user,
            value=result_calc["value"],
            text="Получено за отзыв",
            lifespan=result_calc["lifetime"]
        )

        FinancialOperation.new(user, round(result_calc["value"]), True, "user", "Получено за написание отзыва")

        booking.is_review_bonus = True
        booking.save()

        return JsonResponse({'result': comment.id})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_reviews(request: HttpRequest):
    hotel_id = request.GET.get('hotel_id')
    sort_by = request.GET.get('sort_by', 'creation_date')
    page = request.GET.get('page', 1)

    if (sort_by == "creation_date"):
        sort_by = "-date"

    if (sort_by == "low_rating"):
        sort_by = "-overall_rating"

    if (sort_by == "high_rating"):
        sort_by = "overall_rating"

    # Получение списка отзывов из базы данных с помощью ORM
    reviews = Comment.objects.filter(hotel_id=hotel_id, is_pending=False).order_by(sort_by)
    paginator = Paginator(reviews, 9999)  # 10 отзывов на страницу
    page_obj = paginator.get_page(page)

    basic_info = {
        "location": 0,
        "price_quality_ratio": 0,
        "purity": 0,
        "food": 0,
        "service": 0,
        "number_quality": 0,
        "hygiene_products": 0,
        "wifi_quality": 0,
    }

    for review in reviews:
        basic_info["location"] += review.location
        basic_info["price_quality_ratio"] += review.price_quality_ratio
        basic_info["purity"] += review.purity
        basic_info["food"] += review.food
        basic_info["service"] += review.service
        basic_info["number_quality"] += review.number_quality
        basic_info["hygiene_products"] += Comment.convert_value("hygiene", review.hygiene_products)["number"]
        basic_info["wifi_quality"] += Comment.convert_value("wifi", review.wifi_quality)["number"]

    basic_info["location"] /= len(reviews)
    basic_info["price_quality_ratio"] //= len(reviews)
    basic_info["purity"] /= len(reviews)
    basic_info["food"] /= len(reviews)
    basic_info["service"] /= len(reviews)
    basic_info["number_quality"] /= len(reviews)
    basic_info["hygiene_products"] /= len(reviews)
    basic_info["wifi_quality"] /= len(reviews)

    basic_info["location"] = round(basic_info["location"], 1)
    basic_info["price_quality_ratio"] = round(
        basic_info["price_quality_ratio"], 1)
    basic_info["purity"] = round(basic_info["purity"], 1)
    basic_info["food"] = round(basic_info["food"], 1)
    basic_info["service"] = round(basic_info["service"], 1)
    basic_info["number_quality"] = round(basic_info["number_quality"], 1)
    basic_info["hygiene_products"] = round(basic_info["hygiene_products"], 1)
    basic_info["wifi_quality"] = round(basic_info["wifi_quality"], 1)

    hotel = Hotel.objects.get(id=hotel_id)

    basic_info["count"] = len(reviews)
    basic_info["overall_rating"] = hotel.rating_stat
    basic_info["overall_rating_text"] = Comment.convert_value("overall_rating", round(hotel.rating_stat))["text"],

    # Формирование списка отзывов для возврата в ответе
    results = []
    for review in page_obj:
        review: Comment

        results.append({
            'id': review.id,
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
            "imgs": list(Img.get_url_list("hotel.comment", review.id)),
            "reply": review.reply,
        })

    # Формирование ответа в формате JSON
    response = {
        "basic_info": basic_info,
        'results': results,
        'pages': paginator.num_pages,
    }

    json_data = json.dumps(response, ensure_ascii=False, indent=4)
    return HttpResponse(json_data, content_type='application/json; charset=utf-8')

    # return JsonResponse(response, safe=False)


def hotel_detal(request, id):
    hotel = Hotel.objects.get(id=id)
    RCs = RCategory.objects.filter(hotel=hotel,  is_delete=False)

    if not request.user.is_authenticated and (hotel.enable == False or hotel.is_pending == True):
        return render(request, 'error_page.html', status=404, context={
            "status": "404",
        })

    user = request.user.normal() if request.user.is_authenticated else request.user

    if (user.is_authenticated and hotel.enable == False or hotel.is_pending == True):
        if not (user.user_type in ["moder", "admin", "owner"] or hotel.owner == user):
            return render(request, 'error_page.html', status=404, context={
                "status": "404",
            })

    rating_stat = hotel.rating_stat
    if rating_stat == 0:
        rating_stat = 7

    rating_stat_text = ""
    if rating_stat < 7:
        rating_stat_text = "Хорошо"
    elif rating_stat < 9:
        rating_stat_text = "Превосходно"
    else:
        rating_stat_text = "Великолепно"

    data = {
        "hotel": {
            "id": hotel.id,
            "name": hotel.name,
            "descriptions": hotel.descriptions if hotel.descriptions else "",
            "rating_stat": rating_stat,
            "rating_stat_text": rating_stat_text,
            "reviews_amount": hotel.reviews_amount,
            "type_hotel": {
                "map": hotel.get_hotel_type("и", False),  # Именительный
                "review": hotel.get_hotel_type("п", True),  # Предложный
                "servers": hotel.get_hotel_type("р", True),  # Родительный
            },
            "address": hotel.adrress_hotel.short() if hasattr(hotel, "adrress_hotel") else "",
            "check_in_time": hotel.check_in_time,
            "departure_time": hotel.departure_time,
            "stars": hotel.stars,
            "imgs": [],
        }
    }

    buff_coord: str = hotel.adrress_hotel.coordinates if hasattr(hotel, "adrress_hotel") else ""

    data['hotel']['coordinates'] = buff_coord if buff_coord.find(
        ", ") != -1 else buff_coord.replace(",", ", ") if buff_coord.find(",") != -1 else None

    if data['hotel']['coordinates'] == None:
        raise ValueError("Неправильные координаты")

    coordinates: str = data["hotel"]["coordinates"]

    lan, lon = map(float, coordinates.split(", "))

    # Список метро в радиусе 2 км от отеля
    metro_in_radius = []

    for metro_name, metro_coord in Address.metro_cords.items():
        # Вычисление расстояния между координатами метро и отеля
        dist = distance(metro_coord, (lan, lon))

        # Если расстояние меньше или равно 2 км, то добавляем название метро в список
        if dist <= 0.5:
            if dist >= 1:
                dist = round(dist, 2)
                metro_in_radius.append(
                    {"name": metro_name, "distance": f"{dist}км"})
            else:
                dist = round(dist * 1000)
                metro_in_radius.append(
                    {"name": metro_name, "distance": f"{dist}м"})

    data["hotel"]["metros"] = metro_in_radius


    hservices_qs = hotel.service.all()
    hservices_list = list(hservices_qs)
    hservices = {}

    all_hservices_item = []

    for hs in hservices_list:
        hs : HService
        if hs.section not in hservices:
            hservices[hs.section] = []

        hservices[hs.section].append({"id": hs.id, "name": hs.name, "icon": hs.icon.url if hs.icon else ""})
        if hs.icon:
            all_hservices_item.append({"id": hs.id, "name": hs.name, "icon": hs.icon.url if hs.icon else ""})

    result_hservices = []
    for section in hservices:
        result_hservices.append({
            "section": section,
            "items": hservices[section]
        })

    data["hotel"]["services"] = result_hservices

    data["hotel"]["services_mini"] = list(all_hservices_item[0:3])

    data["hotel"]["imgs"] = Img.get_url("hotel.hotel", hotel.id)

    if hotel.minimum_days_before_arrival == 1:
        data["hotel"]["minimum_days_before_arrival"] = "24 часа"
    elif hotel.minimum_days_before_arrival > 1:
        data["hotel"]["minimum_days_before_arrival"] = str(
            int(hotel.minimum_days_before_arrival)) + " дня"
    elif hotel.minimum_days_before_arrival > 4:
        data["hotel"]["minimum_days_before_arrival"] = str(
            int(hotel.minimum_days_before_arrival)) + " дней"
    else:
        data["hotel"]["minimum_days_before_arrival"] = str(
            round(24 * hotel.minimum_days_before_arrival)) + " часов"

    get_param = {obj[0]: obj[1][0]
                 for obj in dict(request.GET.lists()).items()}

    city_str: str = hotel.adrress_hotel.city
    city_str = city_str.lower()

    place = Place.objects.first()
    if not place:
        return render(request, 'error_page.html', status=404, context={
            "status": "404",
            "message": "Не верный адресс",
            "debug_error": {
                "city_str": city_str,
            }
        })

    # Собираем параметры запроса
    get_param = {obj[0]: obj[1][0]
                 for obj in dict(request.GET.lists()).items()}
    rooms_data = collect_room_parameters(get_param)

    date_1 = datetime.datetime.now() + datetime.timedelta(days=1)
    date_2 = datetime.datetime.now() + datetime.timedelta(weeks=1)

    if "date_1" in get_param and "date_2" in get_param:
        date_1 = datetime.datetime.strptime(get_param["date_1"], "%d.%m.%Y")
        date_2 = datetime.datetime.strptime(get_param["date_2"], "%d.%m.%Y")
    date_d = (date_2.date() - date_1.date()).days

    # Создаем словарь с параметрами поиска и данными для шаблона
    search = {
        "city": place.name,
        "date_1": date_1.strftime("%d.%m.%Y"),
        "date_2": date_2.strftime("%d.%m.%Y"),
        "rooms_data": rooms_data,
        "url_qp": request.GET.urlencode(),
    }

    place_coordinates = place.coordinates.split(",")
    center_hotel_meter = distance((lan, lon), place_coordinates)
    if center_hotel_meter > 1:
        data["hotel"]["distance_to_text"] = f"От центра {round(center_hotel_meter, 2)} км"
    else:
        data["hotel"]["distance_to_text"] = f"От центра {round(center_hotel_meter * 1000)} м"

    rooms = RCategory.objects.filter(hotel=hotel,  is_delete=False)

    min_price = 9999999999
    for room in rooms:
        price_room_full = Booking.calc_price(user, room, (date_1, date_1 + datetime.timedelta(days=1)))["room_full"]
        buff = int(price_room_full)
        if buff < min_price:
            min_price = buff

    data["min_price"] = min_price
    data["date_d"] = date_d

    content = {"data": data, "search": search}

    keywords = []

    content = add_meta(content, title=f"{data['hotel']['name']}",
                       description=f"{data['hotel']['descriptions']}", keywords=keywords)

    if request.user.is_authenticated:
        review_date_booking_qs = Booking.objects.filter(
            status__in=["verified", "settled", "left"],
            booking_user=request.user,
            booked_room__category__hotel=hotel,
            is_review_bonus=False,
            end_date_time__lt=datetime.date.today() + datetime.timedelta(1)
        )

        review_date = {
            "bookings": [{"id": booking.id, "name": f"{booking.id} - {booking.booked_room.category.name}"} for booking in review_date_booking_qs]
        }

        review_date["active"] = len(review_date_booking_qs) > 0

        content["review_date"] = review_date
    else:
        review_date_booking_qs = []

    return render(request, 'hotel/detailed.html', content)


def collect_room_parameters(get_param: dict) -> dict:
    """Собрать из get парметров - параметры номеров в поисковике

    Args:
        get_param (dict): GET параметры

    Returns:
        dict: Данные номеров из поисковика
    """
    roomsData = []

    index = 0
    while True:
        room = {}
        if f'a{index}' in get_param:
            room['adults'] = int(get_param[f'a{index}'][0])
        else:
            break

        if f'ca{index}' in get_param and get_param[f'ca{index}'][0] != '':
            room['childrens_age'] = [
                int(age) for age in get_param[f'ca{index}'].split(',')]
        else:
            room['childrens_age'] = []

        room["id"] = index

        roomsData.append(room)
        index += 1

    return roomsData


def ajax_get_rooms(request: HttpResponse):
    hotel_id = request.GET.get('hotel_id')

    # Собираем параметры запроса
    get_param = {obj[0]: obj[1][0]
                 for obj in dict(request.GET.lists()).items()}
    rooms_data = collect_room_parameters(get_param)

    date_1 = datetime.datetime.now() + datetime.timedelta(days=1)
    date_2 = datetime.datetime.now() + datetime.timedelta(weeks=1)

    if "date_1" in get_param and "date_2" in get_param:
        date_1 = datetime.datetime.strptime(get_param["date_1"], "%d.%m.%Y")
        date_2 = datetime.datetime.strptime(get_param["date_2"], "%d.%m.%Y")

    date_d = (date_2.date() - date_1.date()).days

    search = {
        "date_1": date_1.strftime("%d.%m.%Y"),
        "date_2": date_2.strftime("%d.%m.%Y"),
        "rooms_data": rooms_data,
    }

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
            room_no_booking.append(room)

    rooms_data = search["rooms_data"]

    valid_rooms = {}

    for index, room in enumerate(room_no_booking):
        room: Room

        if room.category.id not in valid_rooms.keys():
            valid_rooms[room.category.id] = {
                "id": room.id,
                "rc": {
                    "id": room.category.id,
                    "name": room.category.name,
                    "max_adults": room.category.max_adults,
                },
                "count_room": 0,
                "count_busy": 0,
            }

        valid_rooms[room.category.id]["count_room"] += 1

    for index, room_data in enumerate(rooms_data):
        for room in valid_rooms.values():

            if room["count_busy"] < room["count_room"]:
                count_guest = room_data["adults"] + len(
                    [children for children in room_data["childrens_age"] if children > 2])

                if room["rc"]["max_adults"] >= count_guest:
                    room["count_busy"] += 1
                    break

    valid_rooms_distributed_count_rc = {}
    for key, value in valid_rooms.items():
        if key not in valid_rooms_distributed_count_rc:
            valid_rooms_distributed_count_rc[key] = 0

            valid_rooms_distributed_count_rc[key] += value["count_busy"]

    u_list_rcs_no_booking = []

    rcs_no_booking = []
    for room in room_no_booking:
        rc = room.category
        if rc.id in u_list_rcs_no_booking:
            continue

        u_list_rcs_no_booking.append(rc.id)

        rcs_no_booking.append(rc)

    html_rooms = []

    min_price = 99999999

    min_price_one_day = 99999999

    for rc in rcs_no_booking:
        rc : RCategory
        days_min = PricePerDay.getDaysMin(rc, date_1)
        days_min = days_min if days_min else rc.min_days
        if date_d < days_min:
            continue

        imgs = Img.get_url("hotel.rc", rc.id)

        services = rc.service.all()

        final_price = Booking.calc_price(
            request.user, rc, (date_1, date_2))["room_full"]

        if min_price > final_price:
            min_price = final_price

        final_price_one_day = Booking.calc_price(
            request.user, rc, (date_1, date_1 + datetime.timedelta(days=1)))["room_full"]

        if min_price_one_day > final_price_one_day:
            min_price_one_day = final_price_one_day

        if rc.additional_info:
            food_rate = rc.additional_info.get("food_rate")
        else:
            food_rate = None

        food_rate_list = []
        if food_rate:
            for key, price in food_rate.items():
                label = key
                if key == "breakfast_lunch_dinner": label = "Завтрак, обед, ужин"
                if key == "breakfast_lunch": label = "Завтрак, обед"
                if key == "breakfast_dinner": label = "Завтрак, ужин"
                if key == "lunch_dinner": label = "Обед, ужин"
                if key == "breakfast": label = "Завтрак"
                if key == "lunch": label = "Обед"
                if key == "dinner": label = "Ужин"

                food_rate_list.append({
                    "code": key,
                    "label": label,
                    "price": int(price) * date_d,
                })

            food_rate_list.reverse()

        count_day_str = ""
        count_day = (date_2 - date_1).days
        if count_day % 10 == 1 and count_day % 100 != 11:
            count_day_str = f"{count_day} ночь"
        elif 2 <= count_day % 10 <= 4 and (count_day % 100 < 10 or count_day % 100 >= 20):
            count_day_str = f"{count_day} ночи"
        else:
            count_day_str = f"{count_day} ночей"

        min_price = min_price if min_price <= 9999999 else 0

        context = {
            "selected_numbers": valid_rooms_distributed_count_rc[rc.id],
            "beds": rc.get_str_beds(),
            "breakfast": hotel.breakfast,
            "count_bedrooms": rc.count_bedrooms,
            "count_images_not_shown": len(imgs) - 2,
            "rc_room_count": rc.count_room,
            "description_of_the_room": rc.description_of_the_room,
            "dinner": hotel.dinner,
            "final_price": int(final_price),
            "price_one_day": int(final_price / (date_2 - date_1).days),
            "count_day_str": count_day_str,
            "count_day": count_day,
            "id": rc.id,
            "imgs": imgs,
            "lunch": hotel.lunch,
            "max_adult": rc.max_adults,
            "name": rc.name,
            "offer_type": rc.get_offer_type_display(),
            "square": rc.square,
            "services": [{"name": item.name, "icon": item.icon.url if item.icon else "" } for item in services],
            "text_price_room": "",
            "favorite": False,
            "count_room": list(range(0, len(Booking.get_free_rooms(rc, date_1, date_2)) + 1)),
            "food_rates": food_rate_list,
        }


        tmpl = get_template('template/hotel_detailed_room.html')

        html_rooms.append({"html": tmpl.render(context), "data": context})

    count_room = len(html_rooms)

    return JsonResponse({"rooms": html_rooms, "count_room": count_room, "valid_rooms_distributed_count_rc": valid_rooms_distributed_count_rc, "min_price_one_day": min_price_one_day, "min_price": min_price if min_price <= 9999999 else 0})
