import datetime
import json
import math
import time
from django.shortcuts import render
from brontur.funs import find_object_index_by_property
from django.forms.models import model_to_dict
# from hotel.models import Address, HImg, Hotel, RCategory, Room, Comment, RImg, RService, HService, Booking

from hotel.models import Hotel
from hotel.models import RCategory
from hotel.models import Room
from hotel.models import RService
from hotel.models import HService
from hotel.models import Booking
from hotel.models import HBoost
from hotel.models import PricePerDay
from hotel.models import Favourite

from django.db.models import Q, QuerySet, Prefetch
from django.core.cache import cache


from django.http import HttpRequest, HttpResponse, JsonResponse


from django.http import Http404

from utils.models import Img, Place


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

# Сократил в 3.3 раза


def hotel_search(request: HttpRequest, slug: str):
    """Отобразить страницу

    Args:
        request (HttpRequest): Request
        slug (str): Slug города или места

    Raises:
        Http404: Город не найден

    Returns:
        _type_: Страница
    """

    place_name = ""
    if slug == "favourites":
        place_name = "Избранное"
    else:
        place = Place.objects.filter(slug=slug).first()
        if not place:
            raise Http404("Не удалось найти")

        place_name = place.name

    # Собираем параметры запроса
    get_param = {obj[0]: obj[1][0]
                 for obj in dict(request.GET.lists()).items()}
    rooms_data = collect_room_parameters(get_param)

    date_1 = datetime.datetime.now() + datetime.timedelta(days=1)
    date_2 = datetime.datetime.now() + datetime.timedelta(days=2)

    if "date_1" in get_param and "date_2" in get_param:
        date_1 = datetime.datetime.strptime(get_param["date_1"], "%d.%m.%Y")
        date_2 = datetime.datetime.strptime(get_param["date_2"], "%d.%m.%Y")

    # Создаем словарь с параметрами поиска и данными для шаблона
    search = {
        "city": place_name,
        "coord": place.coordinates if place_name != "Избранное" else "0, 0",
        "date_1": date_1.strftime("%d.%m.%Y"),
        "date_2": date_2.strftime("%d.%m.%Y"),
        "rooms_data": rooms_data,
        "slug": slug,
        "url_qp": request.GET.urlencode(),
    }

    # Создаем словарь с возможными значениями для фильтров
    choices = {}

    # Типы объектов
    choices["building"] = [{"code": code, "name": name}
                           for code, name in Hotel.type_hotel_mini]

    # Создание списка услуг номера
    rs_list = ["Компьютер", "Кондиционер", "Посудомоечная машина", "Стиральная машина", "Сушилка",
               "Телефон", "Утюг", "Фен", "Джакузи", "Кухня", "Бесплатный чай/кофе", "Микроволновка", ]
    choices["rservices"] = [{"code": rs.id, "name": rs.name}
                            for rs in RService.objects.filter(name__in=rs_list)]

    # Создание списка услуг отеля
    hs_list = {"Круглосуточная стойка регистрации", "Отель для некурящих", "Курение запрещено на всей территории", "Места для курения", "Курение разрешено", "Лифт", "Отопление", "Мебель на улице", "Только для взрослых",
               "Ресторан («шведский стол»)", "Бесплатный Wi-Fi", "Трансфер от аэропорта", "Бесплатная парковка рядом с отелем", "Общая кухня", "Площадка для барбекю", "Удобства для барбекю", "Горнолыжный склон рядом",
               "Пляж рядом", "Конференц-зал", "Ксерокс", "Тренажерный зал", "Сауна", "Баня", "Детские телеканалы", "Услуги няни и уход за детьми", "Детская игровая площадка", "Не предоставляются отчетные документы",
               "Предоставляются отчетные документы",
               "Размещение с домашними животными",
               "Размещение с домашними животными не допускается",
               "Размещение с домашними животными до 5-ти кг",
               "Бесплатная парковка",
               "Парковка оплачивается отдельно"
               }
    choices["hservices"] = [{"code": item, "name": item} for item in hs_list]

    content = {
        "data": {"city": place_name},
        "choices": choices,
        "search": search,
        "page": {
            "title": f"Тургородок - Поиск - {place_name}"
        },
        "value_search_input_slug": slug,
    }

    return render(request, 'hotel/list.html', content)


def check_distance(center_coord, hotel_coord, radius_m):
    radius = radius_m / 1000  # Из местров в км
    R = 6371  # радиус Земли в км
    lat1, lon1 = map(float, center_coord)  # координаты центра города
    lat2, lon2 = hotel_coord  # координаты отеля
    lat2, lon2 = float(lat2), float(lon2)

    # перевод координат в радианы
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # расчет расстояния между координатами
    d = 2 * R * math.asin(math.sqrt(math.sin((lat2 - lat1) / 2) ** 2 +
                                    math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))

    # raise ValueError()

    # сравнение расстояния с заданным радиусом
    if d <= radius:
        return True
    else:
        return False


def format_time(total_time):
    if (total_time == 0):
        return "0"

    minutes, seconds = divmod(total_time, 60)
    hours, minutes = divmod(minutes, 60)
    milliseconds = int((total_time - int(total_time)) * 1000)

    parts = []
    if hours >= 1:
        parts.append(f"{int(hours)}ч")

    if minutes >= 1:
        parts.append(f"{int(minutes)}м")

    if seconds >= 1:
        parts.append(f"{int(seconds)}с")

    if milliseconds > 0:
        parts.append(f"{int(milliseconds)}мс")

    if len(parts) == 0:
        return "0мс"

    return " ".join(parts)


def f_food(food_value, hotel_obj):
    if "breakfast" in food_value:
        if not (hotel_obj['breakfast'] == True):
            return False

    if "lunch" in food_value:
        if not (hotel_obj['lunch'] == True):
            return False

    if "dinner" in food_value:
        if not (hotel_obj['dinner'] == True):
            return False

    return True


def get_hotel_fillter(request: HttpRequest):
    times = {}
    times["start"] = time.time()

    f_param, map_setting, search, place = collect_parameters(request)

    # Как запущен фильтер: Пусто - Просто как видет его клиент, debug с временим и без ограничения по времени
    mode = request.GET.get("mode")

    # Список отелей и их параметров
    hotels_parameters = []
    # Отфильтрированый список отелей
    filter_hotels_list = []
    # Отсортированный список отелей
    sorted_hotels_list = []

    hotel_count = {
        "cur": 0,
        "max": 0,
    }

    guests_count_all = 0

    for room_data in search["rooms_data"]:
        count_guest = room_data["adults"]
        count_guest += len(
            [children for children in room_data["childrens_age"] if children > 2])

        guests_count_all += count_guest

    times["Обработка запроса"] = time.time()

    hotels_all = None

    citys = []

    if place == "favourites":
        favourites : QuerySet[Favourite] = request.user.favourites.all()
        hotels_all_id = favourites.values_list("hotel", flat=True)
        hotels_all = Hotel.objects.filter(id__in=hotels_all_id, enable=True, is_pending=False)
    else:
        citys = place.get_descendants_name()
        citys.append(place.name)
        qs_param = Q()
        for city in citys:
            qs_param |= Q(adrress_hotel__city__iexact=city)

        # qs_param = qs_param & Q(enable=True, is_pending=False)

        hotels_all = Hotel.objects.filter(qs_param)

    times["Получения всех отелей"] = time.time()

    hotels_all = hotels_all.order_by("-id")

    hotel_count["max"] = len(hotels_all)

    f_param["hotels_all_count"] = len(hotels_all)

    hotels_parameters = []
    future_times = []

    start_time = time.time()

    fillter_id = search["fillter_id"]

    cache_index = cache.get(fillter_id + "_index", 0)
    hotels_parameters: list = cache.get(fillter_id + "_hotels", [])

    final_request = False

    d_time_filter = 5

    if cache_index == 0:
        d_time_filter = 5
    else:
        d_time_filter = max(10, cache_index / 100)

    for index, hotel in enumerate(hotels_all):
        if index < cache_index:
            continue

        if mode == "debug":
            hotel_param, future_time = get_hotel_param_dev(request, hotel, search, f_param)
        else:
            hotel_param, future_time = get_hotel_param(
                request, hotel, search, f_param)

        if hotel_param:
            hotels_parameters.append(hotel_param)
            future_times.append(future_time)

        # Если все отели обработались то удалить кеш
        if index + 1 >= len(hotels_all):
            final_request = True
            break


        if mode == "debug":
            continue

        if place != "favourites":
            # Если отели не успели за 5 секунд
            if time.time() - start_time > d_time_filter:
                if len(hotels_parameters) > 0:
                    cache.set(fillter_id + "_hotels", hotels_parameters, 300)
                    cache.set(fillter_id + "_index", index, 300)
                    break
                else:
                    if time.time() - start_time > 30:
                        cache.set(fillter_id + "_hotels", hotels_parameters, 300)
                        cache.set(fillter_id + "_index", index, 300)
                        break

    hotel_count["cur"] = len(hotels_parameters)

    filter_hotels_list = hotels_parameters

    times["Проход по всем отелям"] = time.time()

    ###################################################################################################################################

    times["Фильтрация"] = time.time()

    # Сортировка
    if f_param["sorting"] == "not":
        sorted_hotels_list = sorted(filter_hotels_list, key=lambda hotel: (
            hotel['boost_super'], hotel['secondary_priority'], hotel["percentage"], hotel['boost_common']), reverse=True)

    elif f_param["sorting"] == "price_up":
        sorted_hotels_list = sorted(
            filter_hotels_list, key=lambda hotel: hotel['min_price'], reverse=True)

    elif f_param["sorting"] == "price_down":
        sorted_hotels_list = sorted(
            filter_hotels_list, key=lambda hotel: hotel['min_price'])

    elif f_param["sorting"] == "rating_up":
        sorted_hotels_list = sorted(
            filter_hotels_list, key=lambda hotel: hotel['rating_stat'], reverse=True)

    elif f_param["sorting"] == "count_up":
        sorted_hotels_list = sorted(
            filter_hotels_list, key=lambda hotel: hotel['reviews_amount'], reverse=True)

    times["Сортировка"] = time.time()

    hotel_count["cur"] = len(sorted_hotels_list)

    hotels_map = []
    for hotel in sorted_hotels_list:
        hotels_map.append({
            "id": hotel["id"],
            "name": hotel['name'],
            "min_price": hotel["min_price"],
            "rating_stat": hotel['rating_stat'],
            "rating_stat_text": hotel['rating_stat_text'],
            "reviews_amount": hotel['reviews_amount'],
            "imgs": hotel['imgs'],
            "stars": hotel['stars'],
            "address": hotel["address"],
            "coordinates": hotel["coordinates"],
        })

    sorted_hotels_list = sorted_hotels_list[:search["count_card_max"]]

    text_price_room = ""
    date_d_days = search["date_d"]
    if date_d_days == 1:
        text_price_room = f"за ночь для"
    elif date_d_days > 1:
        text_price_room = f"за {date_d_days} ночей для"

    guests_text = f"{guests_count_all} гост{'я' if guests_count_all == 1 else 'ей'}"

    text_price_room = text_price_room + " " + guests_text

    times["end"] = time.time()

    if place == "favourites":
        final_request = True

    content = {
        "hotel_count": hotel_count,
        "final_request": final_request,
        "fillter_id": fillter_id,
        "hotel": sorted_hotels_list,
        "hotel_all": list(hotels_all.values()),
        "citys": citys,
        "hotels_map": hotels_map,
        "text_price_room": text_price_room,
        "map_setting": map_setting
    }

    if mode == "debug":
        past_time = times["start"]

        times_result = {}

        for key, obj in times.items():
            start = format_time(obj - times["start"])
            end = format_time(obj - times["start"] + obj - past_time)
            duration = format_time(obj - past_time)
            times_result[key] = {
                "duration":  f"{duration} [{start} ~ {end}]",
                "orig_duration": obj - past_time,
            }

            past_time = obj

        if future_times == None:
            future_times = []

        if len(future_times) > 0:
            averages_future_time = {key: 0 for key in future_times[0].keys()}
        else:
            averages_future_time = {}

        for future_time in future_times:
            past_time = future_time["start"]
            for key, obj in future_time.items():
                start = format_time(obj - times["start"])
                end = format_time(obj - times["start"] + obj - past_time)
                duration = format_time(obj - past_time)

                future_time[key] = {
                    "duration":  f"{duration} [{start} ~ {end}]",
                    "orig_duration": obj - past_time,
                }
                averages_future_time[key] += future_time[key]["orig_duration"]

                past_time = obj

        times_result["Проход по всем отелям"]["averages"] = {key: format_time(
            item / len(future_times)) for key, item in averages_future_time.items()}
        times_result["Проход по всем отелям"]["sum"] = {
            key: format_time(item) for key, item in averages_future_time.items()}


        for key in times_result.keys():
            if key != "Проход по всем отелям":
                times_result[key] = times_result[key]["duration"]

        del times_result["start"]

        content = {
            "hotel_count": f"{hotel_count['cur']} ({hotel_count['max']})",
            "time": times_result,
            "hotels": sorted_hotels_list,
        }

    return JsonResponse(content)


def collect_parameters(request: HttpRequest):
    name_hotel_value = request.GET.get("name_hotel", "")
    sorting_value = request.GET.get("sorting", "not")
    building_value = request.GET.getlist("buildings[]", [])
    rservices_value = request.GET.getlist("rservices[]", [])
    hservices_value = request.GET.getlist("hservices[]", [])

    fillter_id = request.GET.get("fillter_id")

    f_param = {
        "sorting": sorting_value,
        "name_hotel": name_hotel_value,
        "building": building_value,
        "rservices": rservices_value,
        "hservices": hservices_value,
    }

    duration_value = int(request.GET.get(
        "duration_value", "999999.0").split(".")[0])

    price_value = [int(price.split(".")[0])
                   for price in request.GET.getlist("price_value[]")]
    additional_criteria = request.GET.getlist("additional_criteria[]")

    f_param["additional_criteria"] = additional_criteria
    f_param["price"] = price_value
    f_param["duration"] = duration_value

    get_param = {obj[0]: obj[1][0]
                 for obj in dict(request.GET.lists()).items()}
    rooms_data = collect_room_parameters(get_param)

    date_1 = datetime.datetime.now() + datetime.timedelta(days=1)
    date_2 = datetime.datetime.now() + datetime.timedelta(weeks=1)

    if "date_1" in get_param and "date_2" in get_param:
        date_1 = datetime.datetime.strptime(get_param["date_1"], "%d.%m.%Y")
        date_2 = datetime.datetime.strptime(get_param["date_2"], "%d.%m.%Y")

    date_d = (date_2.date() - date_1.date()).days

    page = int(get_param.get("page", "0"))

    slug = request.GET.get("slug")

    place_name = ""
    if slug == "favourites":
        place_name = "Избранное"
        place = "favourites"
    else:
        place = Place.objects.filter(slug=slug).first()
        if not place:
            raise Http404("Ошибка фильтрации")

        place_name = place.name

    search = {
        "fillter_id": fillter_id,
        "page": page,
        "city": place_name,
        "rooms_data": rooms_data,
        "date_1": date_1,
        "date_2": date_2,
        "date_d": date_d,
        "slug": slug,
        "count_card_max" : int(get_param.get("count_card_max", "20"))
    }

    if place_name == "Избранное":
        map_setting = {
            "center": [0, 0],
            "scale": 1,
            "radius": -1,
        }

        f_param["duration"] = -1

    else:
        map_setting = {
            "center": place.coordinates.split(", "),
            "scale": 14,
            "radius": duration_value,
        }

    f_param["map_setting"] = map_setting

    return f_param, map_setting, search, place


def get_hotel_param(request: HttpRequest, hotel: Hotel, search, f_param):
    hotel_param, times = {}, {"start": time.time()}

    # Получения параметров с одинаковым названием
    hotel_param = model_to_dict(hotel, exclude=["additional_info", "service"])

    times["Запись: model_to_dict"] = time.time()

    if hotel_param["rating_stat"] == 0 and hotel_param["rating_amount"] == 0:
        hotel_param["rating_stat"] = 7

    rating_stat_text = ""
    if hotel_param["rating_stat"] < 7:
        rating_stat_text = "Хорошо"
    elif hotel_param["rating_stat"] < 9:
        rating_stat_text = "Превосходно"
    else:
        rating_stat_text = "Великолепно"

    hotel_param["rating_stat_text"] = rating_stat_text

    # Обработка обычных параметров
    hotel_param["stars_text"] = "★" * hotel.stars
    hotel_param["address"] = hotel.adrress_hotel.short() if hasattr(hotel, "adrress_hotel") else ""
    hotel_param["coordinates"] = None
    if hotel.adrress_hotel.coordinates:
        hotel_param["coordinates"] = [coord.strip()
                                      for coord in hotel.adrress_hotel.coordinates.split(",")]
    hotel_param["delta_date_when_you_start_receiving_guests"] = search["date_1"].date(
    ) - hotel.date_when_you_start_receiving_guests

    times["Обработка и Запись: обычных параметров"] = time.time()

    # Обработка параметров зависящие от категорий номеров
    max_price, min_price = 0, 999999
    rcs_obj_list, rc_list, rc_service_list, price_list = [], [], [], []

    rooms_data = search["rooms_data"]
    searchable_items_count = 0

    all_count_room_searchable = 0

    used_room_ids = []

    date_fill_1 = datetime.datetime(year=search["date_1"].year, month=search["date_1"].month, day=search["date_1"].day, hour=hotel.check_in_time.hour)
    date_fill_2 = datetime.datetime(year=search["date_2"].year, month=search["date_2"].month, day=search["date_2"].day, hour=hotel.departure_time.hour)

    for rc in RCategory.objects.filter(hotel=hotel, enable=True, is_delete=False):
        rc: RCategory

        rooms = Room.objects.filter(
            category=rc, category__enable=True, enable=True, is_delete=False)

        bookings = Booking.objects.filter(Q(booked_room__in=rooms) &
            (
                Q(start_date_time__lte=date_fill_1) & Q(end_date_time__gte=date_fill_2))
            )

        room_bookings = [booking.booked_room.id for booking in bookings]

        room_no_booking = [
            room.category for room in rooms if room.id not in room_bookings]

        hotel_param["bookings"] = {}

        hotel_param["bookings"].update({
            "list": {
                rc.name: list(bookings.values_list('booked_room', flat=True))
            },
            "room_bookings": {
                rc.name: list(bookings.values_list(
                    'booked_room__room_number', flat=True))
            },
            "room_no_booking": {
                rc.name: [room.room_number for room in rooms if room.id not in room_bookings],
            }
        })

        if len(room_no_booking) <= 0:
            continue

        days_min = PricePerDay.getDaysMin(rc, search["date_1"]) or rc.min_days
        if search["date_d"] < days_min:
            continue

        rcs_obj_list_obj = {
            "max_guests": rc.max_adults,
            "count_room": len(room_no_booking),
            "busy": [],
        }

        valid_all_count_room_searchable = False

        for room_data in rooms_data:
            if room_data["id"] in used_room_ids:
                continue

            if len(rcs_obj_list_obj["busy"]) < rcs_obj_list_obj["count_room"]:
                count_guest = room_data["adults"]
                count_guest += len(
                    [children for children in room_data["childrens_age"] if children > 2])

                if rcs_obj_list_obj["max_guests"] >= count_guest:
                    rcs_obj_list_obj["busy"].append(room_data["id"])
                    used_room_ids.append(room_data["id"])
                    valid_all_count_room_searchable = True


        if valid_all_count_room_searchable:
            searchable_items_count += 1
            price_list.append(Booking.calc_price(request.user, rc, (search["date_1"], search["date_2"]))["room_full"])


        rcs_obj_list.append(rcs_obj_list_obj)
        rc_list.append(rc.name)

        rc_service_list.extend(service.id for service in rc.service.all())

        if hotel.type_hotel in ["apartments", "flat"]:
            apartment_text = ""
            if rc.square > 0:
                apartment_text = ", ".join(
                    [f"Площадь {rc.square} м²", f"{rc.count_room} комнаты", f"{rc.count_bedrooms} спальни"])
            else:
                apartment_text = ", ".join(
                    [f"{rc.count_room} комнаты", f"{rc.count_bedrooms} спальни"])

            hotel_param["apartment_text"] = apartment_text

    if len(rcs_obj_list) == 0:
        return None, None

    # На всех не хватило места в отеле
    if searchable_items_count < len(rooms_data):
        return None, None

    times["Обработка: номеров"] = time.time()

    # Запись в список параметров полученых значений номеров
    hotel_param["rcs"] = rc_list
    hotel_param["rcs_obj_list"] = rcs_obj_list
    hotel_param["rcs_service"] = list(set(rc_service_list))
    hotel_param["max_price"] = max(price_list) if len(price_list) > 0 else 0
    hotel_param["min_price"] = min(price_list) if len(price_list) > 0 else 0
    hotel_param["prices"] = price_list

    times["Запись: номеров"] = time.time()

    # Запись услуг
    hotel_param["hotel_service"] = list(
        hotel.service.all().values_list("name", flat=True))

    times["Обработка и Запись: услуг"] = time.time()

    # Фильтрация
    if not hotel_filter(hotel_param, f_param):
        return None, None

    # Получения значения бустов
    hotel_param["boost_common"], hotel_param["boost_super"] = HBoost.get_value_boost(
        hotel=hotel)

    given_to_man = hotel.additional_info.get("given_to_man")

    hotel_param["secondary_priority"] = 0

    if given_to_man == True:
        hotel_param["secondary_priority"] += 1


    times["Обработка и Запись: бустов"] = time.time()

    # Получения url изображений
    if not hotel.additional_info.get("url_cache_phote"):
        url_list = Img.get_url_list("hotel.hotel", hotel.id)
        hotel.additional_info["url_cache_phote"] = list(url_list)
        hotel.save()

    hotel_param["imgs"] = hotel.additional_info["url_cache_phote"] if hotel.additional_info.get(
        "url_cache_phote") else []

    times["Обработка и Запись: изображений"] = time.time()

    return hotel_param, times

def get_hotel_param_dev(request: HttpRequest, hotel: Hotel, search, f_param):
    hotel_param, times = {}, {"start": time.time()}

    # Получения параметров с одинаковым названием
    hotel_param = model_to_dict(hotel, exclude=["additional_info", "service"])
    times["Запись: model_to_dict"] = time.time()


    # hotel.rcs_hash_occupied_numbers_update()

    if hotel_param["rating_stat"] == 0 and hotel_param["rating_amount"] == 0:
        hotel_param["rating_stat"] = 7

    rating_stat_text = ""
    if hotel_param["rating_stat"] < 7:
        rating_stat_text = "Хорошо"
    elif hotel_param["rating_stat"] < 9:
        rating_stat_text = "Превосходно"
    else:
        rating_stat_text = "Великолепно"

    hotel_param["rating_stat_text"] = rating_stat_text

    # Обработка обычных параметров
    hotel_param["stars_text"] = "★" * hotel.stars
    hotel_param["address"] = hotel.adrress_hotel.short() if hasattr(hotel, "adrress_hotel") else ""
    hotel_param["coordinates"] = None
    if hotel.adrress_hotel.coordinates:
        hotel_param["coordinates"] = [coord.strip()
                                      for coord in hotel.adrress_hotel.coordinates.split(",")]
    hotel_param["delta_date_when_you_start_receiving_guests"] = search["date_1"].date(
    ) - hotel.date_when_you_start_receiving_guests

    times["Обработка и Запись: обычных параметров"] = time.time()

    # Обработка параметров зависящие от категорий номеров
    max_price, min_price = 0, 999999
    rcs_obj_list, rc_list, rc_service_list, price_list = [], [], [], []

    rooms_data = search["rooms_data"]
    searchable_items_count = 0

    all_count_room_searchable = 0

    used_room_ids = []

    date_fill_1 = datetime.datetime(year=search["date_1"].year, month=search["date_1"].month, day=search["date_1"].day, hour=hotel.check_in_time.hour)
    date_fill_2 = datetime.datetime(year=search["date_2"].year, month=search["date_2"].month, day=search["date_2"].day, hour=hotel.departure_time.hour)

    for rc in RCategory.objects.filter(hotel=hotel, enable=True, is_delete=False):
        rc: RCategory
        c_price = Booking.calc_price_v2(request.user, rc, (search["date_1"], search["date_2"]))["room_full"]
        price_list.append(c_price)

        days_min = PricePerDay.getDaysMin_v2(rc, search["date_1"])
        if days_min == False:
            days_min = rc.min_days

        if search["date_d"] < days_min:
            continue

        count_room_no_booking = rc.check_for_available(date_fill_1, date_fill_2)

        if count_room_no_booking <= 0:
            continue

        rcs_obj_list_obj = {
            "max_guests": rc.max_adults,
            "count_room": count_room_no_booking,
            "busy": [],
        }

        valid_all_count_room_searchable = False

        for room_data in rooms_data:
            if room_data["id"] in used_room_ids:
                continue

            if len(rcs_obj_list_obj["busy"]) < rcs_obj_list_obj["count_room"]:
                count_guest = room_data["adults"]
                count_guest += len(
                    [children for children in room_data["childrens_age"] if children > 2])

                if rcs_obj_list_obj["max_guests"] >= count_guest:
                    rcs_obj_list_obj["busy"].append(room_data["id"])
                    used_room_ids.append(room_data["id"])
                    valid_all_count_room_searchable = True

        if valid_all_count_room_searchable:
            searchable_items_count += 1

        rcs_obj_list.append(rcs_obj_list_obj)
        rc_list.append(rc.name)

        rc_service_list.extend(service.id for service in rc.service.all())

        if hotel.type_hotel in ["apartments", "flat"]:
            apartment_text = ""
            if rc.square > 0:
                apartment_text = ", ".join(
                    [f"Площадь {rc.square} м²", f"{rc.count_room} комнаты", f"{rc.count_bedrooms} спальни"])
            else:
                apartment_text = ", ".join(
                    [f"{rc.count_room} комнаты", f"{rc.count_bedrooms} спальни"])

            hotel_param["apartment_text"] = apartment_text

    if len(rcs_obj_list) == 0:
        return None, None

    # На всех не хватило места в отеле
    if searchable_items_count < len(rooms_data):
        return None, None

    times["Обработка: номеров"] = time.time()

    # Запись в список параметров полученых значений номеров
    hotel_param["rcs"] = rc_list
    hotel_param["rcs_obj_list"] = rcs_obj_list
    hotel_param["rcs_service"] = list(set(rc_service_list))
    hotel_param["max_price"] = max(price_list)
    hotel_param["min_price"] = min(price_list)
    hotel_param["prices"] = price_list

    times["Запись: номеров"] = time.time()

    # Запись услуг
    hotel_param["hotel_service"] = list(
        hotel.service.all().values_list("name", flat=True))

    times["Обработка и Запись: услуг"] = time.time()

    # Фильтрация
    if not hotel_filter(hotel_param, f_param):
        return None, None

    # Получения значения бустов
    hotel_param["boost_common"], hotel_param["boost_super"] = HBoost.get_value_boost(
        hotel=hotel)



    given_to_man = hotel.additional_info.get("given_to_man")

    hotel_param["secondary_priority"] = 0

    if given_to_man == True:
        hotel_param["secondary_priority"] += 1


    times["Обработка и Запись: бустов"] = time.time()

    # Получения url изображений
    if not hotel.additional_info.get("url_cache_phote"):
        url_list = Img.get_url_list("hotel.hotel", hotel.id)
        hotel.additional_info["url_cache_phote"] = list(url_list)
        hotel.save()

    hotel_param["imgs"] = hotel.additional_info["url_cache_phote"] if hotel.additional_info.get(
        "url_cache_phote") else []

    times["Обработка и Запись: изображений"] = time.time()

    return hotel_param, times



def hotel_filter(hotel, f_param):
    try:
        # name_hotel_value #
        if len(f_param["name_hotel"]) > 0:
            if hotel['name'].lower().find(f_param["name_hotel"].lower()) == -1:
                return False

        # date_when_you_start_receiving_guests #
        if hotel['delta_date_when_you_start_receiving_guests'].days < 0:
            return False

        # duration_value (Радиус) #
        if f_param["duration"] > 0:

            is_check = check_distance(
                f_param["map_setting"]["center"], hotel['coordinates'], f_param["duration"])

            # Если есть ограничение по фильтру применить его
            if f_param["duration"] < 100000 and not is_check:
                return False

            # Если это маленкий город применять фильтер даже если он 100км
            if f_param["hotels_all_count"] < 500 and not is_check:
                return False

        if len(f_param["building"]) > 0:
            # building_value #
            if not hotel['type_hotel'] in f_param["building"]:
                return False

        # raise ValueError(f_param)
        # rservices_value #
        if len(f_param["rservices"]) > 0:
            f_param["rservices"] = [int(x) if isinstance(
                x, str) else x for x in f_param["rservices"]]
            if not set(f_param["rservices"]).issubset(hotel["rcs_service"]):
                return False

        # hservices_value #
        if len(f_param["hservices"]) > 0:

            hs_list_fill = {
                "Круглосуточная стойка регистрации": ["Круглосуточная стойка регистрации"],
                "Отель для некурящих": ["Отель для некурящих"],
                "Курение запрещено на всей территории": ["Курение запрещено на всей территории"],
                "Места для курения": ["Места для курения"],
                "Курение разрешено": ["Курение разрешено"],
                "Лифт": ["Лифт", "Работают лифты для доступа к верхним этажам"],
                "Отопление": ["Отопление"],
                "Мебель на улице": ["Мебель на улице"],
                "Только для взрослых": ["Только для взрослых"],
                "Ресторан («шведский стол»)": ["Ресторан («шведский стол»)"],
                "Бесплатный Wi-Fi": ["Бесплатный Wi-Fi"],
                "Трансфер от аэропорта": ["Трансфер от аэропорта"],
                "Бесплатная парковка рядом с отелем": ["Бесплатная парковка рядом с отелем"],
                "Общая кухня": ["Общая кухня"],
                "Площадка для барбекю": ["Площадка для барбекю"],
                "Удобства для барбекю": ["Удобства для барбекю"],
                "Горнолыжный склон рядом": ["Горнолыжный склон рядом"],
                "Пляж рядом": ["Пляж рядом"],
                "Конференц-зал": ["Конференц-зал"],
                "Ксерокс": ["Ксерокс"],
                "Тренажерный зал": ["Тренажерный зал"],
                "Сауна": ["Сауна"],
                "Баня": ["Баня"],
                "Детские телеканалы": ["Детские телеканалы"],
                "Услуги няни и уход за детьми": ["Услуги няни и уход за детьми"],
                "Детская игровая площадка": ["Детская игровая площадка"],
                "Не предоставляются отчетные документы": ["Не предоставляются отчетные документы"],
                "Предоставляются отчетные документы": ["Предоставляются отчетные документы"],
                "Размещение с домашними животными": ["Размещение с домашними животными"],
                "Размещение с домашними животными не допускается": ["Размещение с домашними животными не допускается"],
                "Размещение с домашними животными до 5-ти кг": ["Размещение с домашними животными до 5-ти кг"],
                "Бесплатная парковка": ["Бесплатная парковка"],
                "Парковка оплачивается отдельно": ["Парковка оплачивается отдельно"],
            }

            hs_list_need = []

            for hs in f_param["hservices"]:
                if hs in hs_list_fill.keys():
                    hs_list_need.append(hs_list_fill[hs])

            for hs_list_list in hs_list_need:
                if not any(elem in hs_list_list for elem in hotel["hotel_service"]):
                    return False

        # price_value #
        if not any(map(lambda y: f_param["price"][0] <= y <= f_param["price"][1], hotel["prices"])):
            return False

        # additional_criteria #
        if len(f_param["additional_criteria"]) > 0:
            if not (hotel['allowed_animal'] == (True if "allowed_animal" in f_param["additional_criteria"] else False) or
                    hotel['allowed_smoking'] == (True if "allowed_smoking" in f_param["additional_criteria"] else False) or
                    hotel['allowed_party'] == (True if "allowed_party" in f_param["additional_criteria"] else False)):
                return False

        return True
    except:
        return False
