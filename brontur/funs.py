import datetime
import math
import random
import string
from django.conf import settings
from django.urls import reverse
from django.core.mail import send_mail
import pytz


def distance(coord_1, coord_2):
    R = 6371  # радиус Земли в км
    lat1, lon1 = coord_1  # координаты центра города
    lat2, lon2 = coord_2  # координаты отеля
    lat2, lon2 = float(lat2), float(lon2)

    # перевод координат в радианы
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # расчет расстояния между координатами
    d = 2 * R * math.asin(math.sqrt(math.sin((lat2 - lat1) / 2) ** 2 +
                                    math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))

    return d


def find_object_index_by_property(list_of_objects: list, property_name, val):
    for i, obj in enumerate(list_of_objects):
        if obj.get(property_name) == val:
            return i


def send_mail_user(title, content, recipient):
    send_mail(
        title,
        content,
        settings.EMAIL_HOST_USER,
        [recipient],
        fail_silently=True,
    )

    return True

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

def generate_confirmation_url(request, code, user_id):
    # Generate confirmation URL based on user ID
    confirmation_url = request.build_absolute_uri(
        reverse('confirm_email', args=[code, user_id]))
    return confirmation_url


def add_meta(content=None, **args):
    if content is None:
        content = {}
    content['meta'] = {}
    for key in args:
        value = args[key]
        if key == "title":
            content['meta']["title"] = "Тургородок - " + value

        if key == "description":
            content['meta']["description"] = value

        if isinstance(value, str):
            content['meta']["key"] = value

        if isinstance(value, list):
            content['meta']["keywords"] = ', '.join(value)

    return content


def check_html_tags(input_string):
    return input_string == input_string.strip('<>').replace('<', '').replace('>', '')


def validate_post_parameters(request, validation_rules):
    """
    Проверяет параметры POST на соответствие правилам проверки.

    Args:
        request: Объект запроса Django.
        validation_rules: Словарь, содержащий правила проверки для каждого параметра POST.
        - `required`: булево значение, указывающее, является ли параметр обязательным для предоставления. Если параметр обязателен, и его значение не предоставлено, то функция добавляет ошибку в словарь `errors`.
        - `type`: строка, указывающая тип параметра. В функции `validate_post_parameters` поддерживаются типы "int" (целое число) и "num_or_%" (число или процент).
        - `range`: список из двух значений, указывающий минимальное и максимальное допустимое значение параметра. Используется для проверки параметров типа "int" и "num_or_%".
        - `length`: список из двух значений, указывающий минимальную и максимальную допустимую длину значения параметра. Используется для проверки длины текста параметра.

    Returns:
        Словарь ошибок, содержащий название параметра и соответствующую ошибку.

    """
    errors = {}

    for param, rules in validation_rules.items():
        value = request.POST.get(param)

        if rules.get("length") == None:
            rules["length"] = [0, 690731]

        if rules.get("required"):
            if value is None or len(value.strip()) == 0:
                errors[param] = "Обязательный параметр"
            elif len(value.strip()) < rules["length"][0] or len(value.strip()) > rules["length"][1]:
                errors[param] = f"Длина должна быть между {rules['length'][0]} и {rules['length'][1]} символов"
        elif value is None or len(value.strip()) == 0:
            continue
        elif len(value.strip()) < rules["length"][0] or len(value.strip()) > rules["length"][1]:
            errors[param] = f"Длина должна быть между {rules['length'][0]} и {rules['length'][1]} символов"

        if rules.get("type") == "int":
            try:
                value_int = int(value)
                if rules.get("range"):
                    if value_int < rules["range"][0]:
                        errors[param] = f"Значение должно быть больше {rules['range'][0]}"
                    elif value_int > rules["range"][1]:
                        errors[param] = f"Значение должно быть меньше {rules['range'][1]}"
            except ValueError:
                errors[param] = "Неверный формат, пример: 34700"

        if rules.get("type") == "num_or_%":
            num_or_p = number_parser(value)
            if not num_or_p:
                errors[param] = "Неверный формат, пример: 2300 или 34%"
            else:
                if num_or_p:
                    if num_or_p["type"] == "p":
                        if num_or_p["value"] < rules["range"][0]:
                            errors[param] = f"Процент должнен быть больше {rules['range'][0]}"
                        elif num_or_p["value"] > rules["range"][1]:
                            errors[param] = f"Процент должнен быть меньше {rules['range'][1]}"
                    elif num_or_p["type"] == "n":
                        if rules.get("range"):
                            if num_or_p["value"] < rules["range"][0]:
                                errors[param] = f"Значение должно быть больше {rules['range'][0]}"
                            elif num_or_p["value"] > rules["range"][1]:
                                errors[param] = f"Значение должно быть меньше {rules['range'][1]}"
    return errors


def number_parser(value):
    try:
        value = value.replace(' ', '')
        if value.endswith("%"):
            return {"type": "p", "value": int(value[:-1])}
        else:
            return {"type": "n", "value": int(value)}
    except:
        return None


def gen_uid():
    """Генерация uid

    Returns:
        str: Индификатор пользователя
    """

    list_part = {}
    for i in range(4):
        list_part[i] = ""
        for x in range(4):  # Количество символов (16)
            # Символы, из которых будет составлен пароль
            list_part[i] += random.choice(
                list('1234567890abcdefghigklmnopqrstuvyxwzABCDEFGHIGKLMNOPQRSTUVYXWZ'))

    uid = f"{list_part[0]}-{list_part[1]}-{list_part[2]}-{list_part[3]}"
    return uid


def generate_booking_id():
    from hotel.models import Booking
    new_booking_id = str(Booking.objects.count() + 2)
    return new_booking_id


def generate_password(length=10, chars=string.ascii_letters + string.digits):
    """
    Генерирует случайный пароль заданной длины из заданного набора символов.
    По умолчанию длина пароля - 10 символов, используются символы из `string.ascii_letters` (строчные и заглавные буквы) и `string.digits` (цифры).
    """
    return ''.join(random.choice(chars) for i in range(length))


def get_month(month_number):
    months = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
              7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}
    return months[month_number]


def get_weekday(weekday_number):
    days = {0: [False, 'Пн'], 1: [False, 'Вт'], 2: [False, 'Ср'], 3: [
        False, 'Чт'], 4: [False, 'Пт'], 5: [True, 'Сб'], 6: [True, 'Вс']}
    return days[weekday_number]


def get_total_seconds(date) -> int:
    data_0 = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
    date = date.replace(tzinfo=pytz.UTC)
    d_date: datetime.timedelta = date - data_0
    ts = d_date.total_seconds()
    return ts


def get_total_days(date: datetime.datetime) -> float:
    data_0 = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
    date = date.replace(tzinfo=pytz.UTC)
    d_date: datetime.timedelta = date - data_0
    ds = round(d_date.total_seconds() / 86400, 3)
    return ds


def get_date_array(start_date, end_date):
    start = start_date
    curr = start
    end = end_date
    seconds = get_total_seconds(curr)
    days = get_total_days(curr)
    date_array = []
    while curr <= end:
        date_array.append({
            "date": curr,
            "ymd": curr.strftime('%Y-%m-%d'),
            'day': curr.day,
            'month': get_month(curr.month),
            'year': curr.year,
            'day_of_week': get_weekday(curr.weekday()),
            'total_seconds': seconds,
            'total_days': days,
        })
        curr += datetime.timedelta(days=1)
    return date_array


def gen_chat_create_booking(user, booking):
    from chat.models import Chat, Message

    user_owner_hotel = booking.booked_room.category.hotel.owner

    hotel = booking.booked_room.category.hotel

    chat, create = Chat.objects.get_or_create(
        data={
            "type": "booking",
            "hotel": hotel.id,
            "booking": booking.id,
        }
    )

    if create == True:
        chat.users.add(user)
        chat.users.add(user_owner_hotel)

        chat.add_info_message("hotel.start.chat")
        chat.add_info_message("user.start.chat")

    return f"/profile/chats/?chat={chat.id}"


def add_bonus_user_booking_left(booking):
    from chat.models import Chat, Message
    from user.models import Bonus_rubles
    from hotel.models import Booking
    booking: Booking = booking
    if (booking.datetime_stay_bonus == None):
        booking.datetime_stay_bonus = datetime.datetime.now() + \
            datetime.timedelta(days=1)
        booking.save()


def add_bonus_hotel_booking_left(booking):
    from chat.models import Chat, Message
    from user.models import Bonus_rubles
    from hotel.models import Booking
    booking: Booking = booking
    if (booking.datetime_hotel_bonus == None):
        booking.datetime_hotel_bonus = datetime.datetime.now() + \
            datetime.timedelta(days=1)
        booking.save()


def return_rub_bookig(booking, value: float):
    from user.models import User, FinancialOperation
    from hotel.models import Booking

    booking: Booking = booking

    user: User = booking.booking_user

    rbal_d = int(value)

    user.rbal += rbal_d
    FinancialOperation.new(user, rbal_d, False, "booking",
                           "Отмена  бронирования")
    user.save()

    booking.payment_status = "site_refund"
    booking.save()


def add_months(date: datetime.datetime, month_add):
    tz = datetime.timezone(datetime.timedelta(hours=3))

    year = date.year
    # raise ValueError()
    month = date.month + month_add

    if (month <= 0):
        year -= 1
        month = 12 + month

    elif (month > 12):
        year += 1
        month = month - 12

    new_date = datetime.datetime(
        year=year,
        month=month,
        day=date.day,
        hour=date.hour,
        minute=date.minute,
        second=date.second,
        microsecond=date.microsecond,
        tzinfo=tz,
    )

    return new_date


def get_str_model(model, fields):
    values = []
    for field in fields:
        value = getattr(model, field, '-')
        values.append(str(value))
    name = model.__class__.__name__
    return f"[{model.id}] {name} - {', '.join(values)}"