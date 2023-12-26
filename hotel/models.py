from copy import deepcopy
import datetime
import json
import os
import random
import string
from io import BytesIO
from typing import List, Tuple

from PIL import Image
from os import path
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from brontur.funs import generate_booking_id, add_bonus_user_booking_left, add_bonus_hotel_booking_left, return_rub_bookig
from user.models import User, Bonus_rubles, Child, Companion
from django.forms.models import model_to_dict
from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet, Prefetch

class Hotel(models.Model):
    # Включена ли модели, или 'удалена'
    enable = models.BooleanField(default=1, verbose_name='Включен')

    type_hotel_choices = [
        ('apart-hotel', 'Апарт-отель'),
        ('apartments', 'Апартамент'),
        ('flat', 'Квартира'),
        ('recreation center', 'База отдыха'),
        ('hotel_1', 'Гостиница'),
        ('bungalow', 'Бунгало'),
        ('boutique hotel', 'Бутик-отель'),
        ('villa', 'Вилла'),
        ('glamping', 'Глэмпинг'),
        ('guest house', 'Гостевой дом'),
        ('residential premises', 'Жилое помещение'),
        ('castle', 'Замок'),
        ('camping', 'Кемпинг'),
        ('resort hotel', 'Курортный отель'),
        ('furnished rooms', 'Меблированные комнаты'),
        ('mini-hotel', 'Мини-отель'),
        ('bed and breakfast (b&b)', 'Ночлег и завтрак (B&B)'),
        ('hotel', 'Отель'),
        ('sanatorium', 'Санаторий'),
        ('farm', 'Ферма'),
        ('hostel', 'Хостел'),
        ('private house', 'Частный дом'),
        ('chalet', 'Шале'),
    ]

    type_hotel_mini = [
        ('hotel', 'Отели'),
        ('furnished rooms', 'Меблированные комнаты'),
        ('hostel', 'Хостелы'),
        ('residential premises', 'Жилые помещения'),
        ('apartments', 'Апартаменты'),
        ('flat', 'Квартиры'),
        ('apart-hotel', 'Апарт-отели'),
        ('guest house', 'Гостевой дома'),
        ('villa', 'Виллы'),
        ('camping', 'Кемпинги'),
        ('glamping', 'Глэмпинги'),
    ]

    # Главные поля
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE,
                              related_name="hotels", verbose_name='Владелец')
    name = models.CharField(max_length=200, verbose_name='Название')

    # Видные простым клиентам
    descriptions = models.TextField(
        blank=True, null=True, verbose_name='Описание')

    type_hotel = models.CharField(
        max_length=450, choices=type_hotel_choices, default="hotel", verbose_name='Тип отеля')
    check_in_time = models.TimeField(
        blank=True, null=True, verbose_name='Время заезда')
    departure_time = models.TimeField(
        blank=True, null=True, verbose_name='Время выезда')
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], verbose_name='Звезды')
    service = models.ManyToManyField(
        "HService", related_name="hservice", blank=True, verbose_name='Услуги')

    breakfast = models.BooleanField(
        blank=True, null=True, verbose_name='Завтрак')  # Завтрак
    lunch = models.BooleanField(
        blank=True, null=True, verbose_name='Обед')  # Обед
    dinner = models.BooleanField(
        blank=True, null=True, verbose_name='Ужин')  # Ужин

    # Системные поля
    real_money = models.IntegerField(default=0, verbose_name='Реальные деньги')

    rating_stat = models.SmallIntegerField(
        default=0, verbose_name='Статистика рейтинга')
    rating_amount = models.SmallIntegerField(
        default=0, verbose_name='Количество рейтингов')
    reviews_amount = models.SmallIntegerField(default=0, verbose_name='Отзывы')
    coordinates = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='Координаты')
    percentage = models.PositiveSmallIntegerField(
        default=14, validators=[MinValueValidator(14), MaxValueValidator(30)], verbose_name='Процент')
    rank_points = models.PositiveIntegerField(
        default=0, verbose_name='Очки рейтинга')
    instant_booking = models.BooleanField(
        verbose_name='Мгновенное бронирование')

    date_when_you_start_receiving_guests = models.DateField(
        verbose_name='Дата начала приема гостей')

    # Разрешения
    allowed_child = models.BooleanField(verbose_name='Дети разрешены')
    allowed_animal = models.BooleanField(
        verbose_name='Домашние животные разрешены')
    allowed_smoking = models.BooleanField(verbose_name='Курение разрешено')
    allowed_party = models.BooleanField(verbose_name='Вечеринки разрешены')
    minimum_days_before_arrival = models.FloatField(
        verbose_name='Минимальное количество дней до заселение')  # Минимум дней до заселение
    minimum_days_of_stay = models.SmallIntegerField(
        verbose_name='Минимальное количество дней пребывания')  # Минимум дней пребывания

    # Поля изменения цены
    for_long_term_stays = models.CharField(
        max_length=10, verbose_name='Скидка при длительном проживании')  # При длительном проживании скидка
    for_long_term_stays_minimum_days_of_stay = models.SmallIntegerField(
        verbose_name='Минимальное количество дней при длительном проживании')  # Минимум дней

    cleaning_fee = models.CharField(
        max_length=10, verbose_name='Плата за уборку')  # Плата за уборку

    is_delete = models.BooleanField(
        default=False, verbose_name='Флаг удаления')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pending = models.BooleanField(default=True)

    channel_manager = models.CharField(
        max_length=100, verbose_name='Ченел менедеж', default="", blank=True)  # Плата за уборку

    additional_info = models.JSONField(
        default=dict, blank=True, verbose_name='Доп. параметры')  # Дополнителные параметры

    def __str__(self):
        return 'Отель - %s (%s)' % (self.name, self.enable)

    def check_hotel_owner(user: "User", hotel: "Hotel"):
        # Проверяем, принадлежит ли отель текущему пользователю
        if user == hotel.owner:
            return True

        raise PermissionDenied

    def rcs_hash_occupied_numbers_update(self):
        for rc in self.rcategory_hotel.all():
            rc.hash_occupied_numbers_update()

    @staticmethod
    def hash_list_hotel_to_user_update(user: User):
        user.additional_info["hash_hotels"] = [{"id": hotel.id, "name": hotel.name} for hotel in user.hotels]
        return user.additional_info["hash_hotels"]


    def reset_place_position(self):
        from utils.models import Place

        if self.adrress_hotel:
            adrress: Address = self.adrress_hotel
            city = adrress.city
            coordinates = adrress.coordinates.split(",")
            coordinates = [coordinates[0].strip(), coordinates[1].strip()]
            places = Place.objects.filter(name=city)
        else:
            places = []

        for place in self.places.all():
            place: Place
            place.hotels.remove(self)

        if len(places) == 1:
            place = places.first()
            place.hotels.add(self)
            return {"type": "one", "place": f"({place.id}) {place.name}"}

        return {"type": "other"}

    def update(self):
        # Изменения рейтинга отеля
        comments = Comment.objects.filter(hotel=self)
        reviews_amount = rating_amount = len(comments)
        sum = 0
        for comment in comments:
            sum += comment.overall_rating
        if (sum == 0 or rating_amount == 0):
            return
        rating_stat = sum / rating_amount
        self.rating_stat = rating_stat
        self.rating_amount = rating_amount
        self.reviews_amount = reviews_amount

        # Изменения очков отеля
        points = 0
        points += 30 - self.percentage  # *******00
        hotel_boost = HBoost.objects.filter(hotel=self)
        for boost in hotel_boost:
            if not boost.super:
                points += 100  # *****00**
            else:
                points += 1000  # **000****
        self.rank_points = points

        self.save()

    def BTU(self, user):
        """
        Принадлежит пользователю
        """

        return self.owner == user

    def get_hotel_type(hotel, case='и', lower=False):
        types = {
            "flat": {"и": "Квартира", "р": "Квартиры", "д": "Квартире", "в": "Квартиру", "т": "Квартирой", "п": "Квартире"},
            "apartment": {"и": "Апартамент", "р": "Апартамента", "д": "Апартаменту", "в": "Апартамент", "т": "Апартаментом", "п": "Апартаменте"},
            "house": {"и": "Дом", "р": "Дома", "д": "Дому", "в": "Дом", "т": "Домом", "п": "Доме"},
            "cottage": {"и": "Коттедж", "р": "Коттеджа", "д": "Коттеджу", "в": "Коттедж", "т": "Коттеджом", "п": "Коттедже"},
            "room": {"и": "Комната", "р": "Комнаты", "д": "Комнате", "в": "Комнату", "т": "Комнатой", "п": "Комнате"},
            "hotel": {"и": "Отель", "р": "Отеля", "д": "Отелю", "в": "Отель", "т": "Отелем", "п": "Отеле"},
            "hotel_1": {"и": "Гостиница", "р": "Гостиницы", "д": "Гостинице", "в": "Гостиницу", "т": "Гостиницей", "п": "Гостинице"},
            "apart_hotel": {"и": "Апарт-отель", "р": "Апарт-отеля", "д": "Апарт-отелю", "в": "Апарт-отель", "т": "Апарт-отелем", "п": "Апарт-отеле"},
            "mini_hotel": {"и": "Мини-гостиница", "р": "Мини-гостиницы", "д": "Мини-гостинице", "в": "Мини-гостиницу", "т": "Мини-гостиницей", "п": "Мини-гостинице"},
            "guest_house": {"и": "Гостевой дом", "р": "Гостевого дома", "д": "Гостевому дому", "в": "Гостевой дом", "т": "Гостевым домом", "п": "Гостевом доме"},
            "glamping_guest_house": {"и": "Глэмпинг", "р": "Глэмпинга", "д": "Глэмпингу", "в": "Глэмпинг", "т": "Глэмпингом", "п": "Глэмпинге"},
            "recreation_center": {"и": "База отдыха", "р": "Базы отдыха", "д": "Базе отдыха", "в": "Базу отдыха", "т": "Базой отдыха", "п": "Базе отдыха"},
            "hostel": {"и": "Хостел", "р": "Хостела", "д": "Хостелу", "в": "Хостел", "т": "Хостелом", "п": "Хостеле"},
        }

        if case not in ['и', 'р', 'д', 'в', 'т', 'п']:
            case = "и"

        for key in types:
            if key in hotel.type_hotel:
                type_name = types[key][case]
                break
        else:
            type_name = '[Неизвестный тип]'

        if lower == True:
            type_name = type_name.lower()

        return type_name

    def get_absolute_url(self):
        return f"/hotel/{self.id}/"

    def get_status(self):
        status_code = ""
        status_text = ""
        status_color = "#fff"

        if self.is_delete:
            status_text = "Удалён"
            status_code = "delete"
            status_color = "red"
        elif self.is_pending:
            status_text = "На модерации"
            status_code = "is_pending"
            status_color = "#d0a100"
        elif not self.enable:
            status_text = "Выключен"
            status_code = "not_enable"
            status_color = "gray"
        else:
            status_text = "Активен"
            status_code = "active"
            status_color = "#00d200"

        return {
            "code": status_code,
            "text": status_text,
            "color": status_color,
        }

    def calc_overall_rating(self):
        overall_rating_sum = 0
        rating_amount = 0
        for comment in self.comments.all():
            comment: Comment
            comment.calc_overall_rating()
            overall_rating_sum += comment.overall_rating
            rating_amount += 1

        if rating_amount > 0:
            self.rating_stat = round(overall_rating_sum / rating_amount, 1)
            self.rating_amount = rating_amount
            self.reviews_amount = rating_amount
            self.save()


    class Meta:
        verbose_name = 'Отель'
        verbose_name_plural = 'Отели'

class Bonus(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    value = models.PositiveIntegerField()
    date = models.DateTimeField(default=timezone.now)
    text = models.CharField(max_length=100, default="")  # Описания бонуса
    notification_marks = models.JSONField(default=dict, blank=True)
    lifespan = models.PositiveIntegerField(default=182)  # Срок жизни бонуса

    def __str__(self):
        return f"({self.id}) hotel-{self.hotel.id} {self.value}"

    def get_notification_marks(self):
        marks = {
            "5_m": "5 месяцев",
            "4_m": "4 месяца",
            "3_m": "3 месяца",
            "2_m": "2 месяца",
            "1_m": "1 месяц",
            "7_d": "неделю до сгорания",
            "2_d": "2 дня",
        }
        return {marks[k]: v for k, v in self.notification_marks.items()}

    def get_last_false(self):
        for k in self.notification_marks:
            if not self.notification_marks[k]:
                return self.notification_marks

    def days_left(self):
        # жизненный цикл бонуса - 6 месяцев
        bonus_lifetime = timezone.timedelta(days=6*30)
        time_passed = timezone.now() - self.date
        time_left = bonus_lifetime - time_passed
        return time_left.days  # количество дней до конца жизни бонуса

    def get_days_left(self):
        marks = {
            "5_m": 150,
            "4_m": 120,
            "3_m": 90,
            "2_m": 60,
            "1_m": 30,
            "7_d": 7,
            "2_d": 2
        }
        last_false = self.get_last_false()
        if last_false is None:
            return None
        days_left = marks[last_false]
        bonus_date = self.date + datetime.timedelta(days=days_left)
        return (bonus_date - datetime.datetime.now()).days

    def get(hotel: Hotel):
        """
        Функция принимает объект типа Hotel и возвращает словарь, содержащий количество и сумму бонусных рублей пользователя.

        Параметры:
        - user: Объект типа Hotel, обязательный параметр.

        Возвращаемое значение:
        Словарь, содержащий:
        - count: количество бонусных рублей пользователя.
        - sum: сумма бонусных рублей пользователя.

        Если при вычислении суммы произойдет ошибка, функция вернет словарь {"count": 0, "sum": 0}.

        Пример использования:
        ```
        from models import User, Bonus_rubles

        user = User.objects.first()
        bonus_dict = get(user)
        print(bonus_dict)
        ```

        Описание работы функции:
        Функция получает объект Hotel, затем находит все записи в таблице Bonus_rubles, связанные с данным пользователем и вычисляет сумму бонусных рублей. Если при этом происходит ошибка, функция возвращает словарь {"count": 0, "sum": 0}. Если ошибок не происходит, функция возвращает словарь, содержащий количество и сумму бонусных рублей пользователя.
        """
        brs = Bonus.objects.filter(hotel=hotel)
        try:
            sum = 0
            for br in brs:
                sum += br.value

            count = len(brs)
        except:
            return {"count": 0, "sum": 0}
        else:
            return {"count": count, "sum": sum}

    def add(hotel: Hotel, value: int):
        """
        Функция создает новую запись в БД таблице HBonus.

        :param user: объект класса Hotel
        :param value: целочисленное значение баллов
        :param date: дата создания записи
        """
        if value > 0:
            Bonus.objects.create(
                hotel=hotel,
                value=value,
                date=timezone.now(),
            )
        elif value < 0:  # Если за самма отрицательная то это онимания баллов
            Bonus.deny(hotel, -value)

    def deny(hotel: Hotel, value: int):
        """
        Функция удаляет запись из таблицы Bonus_rubles и вызывает сама себя, если необходимо отнять баллов больше, чем есть в одной записи.

        :param user: объект класса User
        :param value: целочисленное значение баллов
        """
        if Bonus.get(hotel)["sum"] - value >= 0:
            last_bonus = Bonus.objects.filter(
                hotel=hotel).order_by("-date").first()

            last_bonus_value = last_bonus.value

            if last_bonus_value >= value:  # Если больше отнимается чем есть в одном
                last_bonus.value -= value
                last_bonus.save()
            else:
                value -= last_bonus_value
                last_bonus.delete()
                Bonus.deny(hotel, value)

    class Meta:
        verbose_name = 'Бонус отеля'
        verbose_name_plural = 'Бонусы отеля'

class Room(models.Model):
    # Включена ли модели, или 'удалена'
    enable = models.BooleanField(default=1)
    category = models.ForeignKey(
        "RCategory", on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=50)
    is_delete = models.BooleanField(
        default=False, verbose_name='Флаг удаления')

    def __str__(self):
        return '(%s) Комната - [%s], категории [%s], отеля [%s]' % (self.id, self.room_number, self.category.name, self.category.hotel.name)

    def BTU(self, user):
        """
        Принадлежит пользователю
        """

        return self.hotel.owner == user

    def BTUs(objs: list["Room"], user: User):
        """
        Принадлежит пользователю (Множество)\n
        Вернёт список обектов
        """
        objs_result = []
        for obj in objs:
            if obj.hotel.owner == user:
                objs_result.append(obj)
        return objs_result

    def included(self, mode: bool):
        self.enable = mode
        self.save()

    class Meta:
        verbose_name = 'Номер отеля'
        verbose_name_plural = 'Номера отеля'

class RCategory(models.Model):
    # Включена ли модели, или 'удалена'
    enable = models.BooleanField(default=False)

    offer_type_choices = [
        (r"number", r"Номер"),
        (r"place_in_the_room", r"Место в номере"),
        (r"atelier", r"Студия"),
        (r"flat", r"Квартира"),
        (r"apartments", r"Апартаменты"),
        (r"house", r"Дом"),
        (r"cottage", r"Коттедж"),
        (r"villa", r"Вилла"),
        (r"separate_room", r"Отдельная комната"),
    ]

    # Общие настройки
    name = models.CharField(max_length=200)
    hotel = models.ForeignKey(
        Hotel, on_delete=models.CASCADE, related_name="rcategory_hotel")

    price_base = models.PositiveIntegerField()
    min_days = models.IntegerField()

    offer_type = models.CharField(max_length=20, choices=offer_type_choices)

    # Что должен пользователь заплатить при заезде, не считается просто строчка
    the_amount_of_the_security_deposit = models.CharField(max_length=40)

    # Вместимость номера
    square = models.PositiveIntegerField()
    max_adults = models.PositiveIntegerField()
    count_room = models.PositiveIntegerField()
    count_bedrooms = models.PositiveIntegerField()

    # Оснащение номеро
    service = models.ManyToManyField(
        "RService", related_name="rservice", blank=True)

    # Предпочтения в номере
    beds = models.JSONField(default=dict, null=True, blank=True)

    # Описание номера
    description_of_the_room = models.TextField(null=True, blank=True)

    is_delete = models.BooleanField(
        default=False, verbose_name='Флаг удаления')

    additional_info = models.JSONField(
        default=dict, blank=True, verbose_name='Доп. параметры')  # Дополнителные параметры

    def __str__(self):
        return '(%s) %s' % (self.id, self.name)

    def get_subcategories(self, category):
        if isinstance(category, (int, str)):
            return RSubCategory.objects.filter(parent_category=category)
        elif isinstance(category, RCategory):
            return RSubCategory.objects.filter(parent_category=category.id)
        else:
            raise TypeError('Неверный тип параметра category')

    def get_str_beds(self):
        beds_type = {
            "bed_1": "Односпальная",
            "bed_2": "Двухспальная",
            "bed_1.5": "Полутороспальная",
            "sofa_1": "Софа",
            "two_tier": "Двух-ярусная",
            "sofa_2": "Диван",
            "armchair": "Кресло",
            "baby_bed": "Детская кровать",
            "baby_cradle": "Детская люлька",
        }

        beds = self.beds
        beds_str = ''
        for bed, count in beds.items():
            if count > 0:
                beds_str += f'{beds_type[bed]} ({count} шт), '
        beds_str = beds_str.rstrip(', ')
        if beds_str == "" or beds_str == " ":
            beds_str = "Кровати не указаны"

        return beds_str

    def beds_str_in_dict(beds_str):
        beds_dict = {}
        for pair in beds_str.split('&'):
            key, value = pair.split('=')
            beds_dict[key] = int(value)

        return beds_dict

    def hash_occupied_numbers_update(self):
        today = datetime.date.today() - datetime.timedelta(days=5)
        date_fill = datetime.datetime(year=today.year, month=today.month, day=today.day, hour=self.hotel.check_in_time.hour)

        bookings_dict = {}
        for i in range(365):
            date = date_fill + datetime.timedelta(days=i)
            count_free_rooms = len(Booking.get_free_room(self, date))
            count_occupied_rooms = self.max_adults - count_free_rooms
            if count_occupied_rooms > 0:
                bookings_dict[date.strftime("%d.%m.%Y")] = count_occupied_rooms

        self.additional_info["occupied_numbers"] = bookings_dict
        self.save()

    def hash_image_update(self):
        from utils.models import Img
        imgs = Img.get_url_list("hotel.rc", self.id)

        self.additional_info["img_hash"] = imgs
        self.save()

        return imgs


    def check_for_available(self, datetime_1 : datetime.datetime, datetime_2 : datetime.datetime):
        current_date = datetime_1
        count_free = self.max_adults

        if not self.additional_info.get("occupied_numbers"):
            self.additional_info["occupied_numbers"] = {}
            self.save()
            return self.max_adults


        while current_date <= datetime_2:
            date = current_date.strftime("%d.%m.%Y")
            count_occupied_numbers = self.additional_info["occupied_numbers"].get(date)
            if count_occupied_numbers != None:
                count_free = min(count_occupied_numbers, count_free)
            current_date += datetime.timedelta(days=1)
        return count_free

    class Meta:
        verbose_name = 'Категория комнаты'
        verbose_name_plural = 'Категории комнат'

class RSubCategory(models.Model):
    price_base = models.IntegerField()
    name = models.CharField(max_length=50)
    parent_category = models.ForeignKey(RCategory, on_delete=models.CASCADE)
    max_adults = models.PositiveSmallIntegerField(default=2)
    max_children = models.PositiveSmallIntegerField(default=1)

class Favourite(models.Model):
    hotel = models.ForeignKey(
        Hotel, related_name="favourites", on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, related_name="favourites", on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Избраный отель'
        verbose_name = 'Избраные отели'

class PricePerDay(models.Model):
    rc = models.ForeignKey(RCategory, on_delete=models.CASCADE)
    subrc = models.ForeignKey(
        RSubCategory, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateField()
    price = models.CharField(max_length=10, blank=True, null=True)
    days_min = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"[{self.date.strftime('%d.%m.%Y')}] [{self.rc}] {self.price} - {self.days_min}"

    def getDaysMin(rc, date: datetime.date | datetime.datetime) -> False or int:
        if isinstance(date, datetime.datetime):
            date_value = date.date()
        else:
            date_value = date

        ppds = PricePerDay.objects.filter(rc=rc, date=date_value)

        if ppds.exists():
            return ppds.first().days_min if ppds.first().days_min != None else False

        return False

    def getOne(rc, date):
        ppd = PricePerDay.objects.filter(rc=rc, date=date).first()
        return ppd

    def calculate_total_price(date1: datetime.datetime, date2: datetime.datetime, rc: RCategory):
        total_price = 0
        date1 += datetime.timedelta(days=1)
        diff: datetime.timedelta = date2 - date1
        diff_days = diff.days + 1
        ppds = PricePerDay.objects.filter(rc=rc, date__range=[date1, date2])
        len_ppds = len(ppds)
        for ppd in ppds:
            if ppd.price:
                total_price += int(ppd.price)
        if diff_days <= 0:
            raise ValueError("Отрицательное количество дней")
        result = total_price + (diff_days - len_ppds) * rc.price_base
        if result <= 0:
            raise ValueError("Отрицательная цена")

        return result

    def calculate_total_price_v2(date1: datetime.datetime, date2: datetime.datetime, rc: RCategory):
        total_price = 0
        date1 += datetime.timedelta(days=1)
        diff: datetime.timedelta = date2 - date1
        diff_days = diff.days + 1
        ppds_all : dict = rc.additional_info.get("ppds", {})
        prices = [value["price"] for key, value in ppds_all.items() if date1 <= datetime.datetime.strptime(key, "%Y-%m-%d") <= date2 and value.get("price")]
        len_ppds = len(prices)
        total_price = sum(prices)

        result = total_price + (diff_days - len_ppds) * rc.price_base

        if diff_days <= 0:
            raise ValueError("Отрицательное количество дней")
        if result <= 0:
            raise ValueError("Отрицательная цена")

        return result


    def getDaysMin_v2(rc, date: datetime.date | datetime.datetime) -> False or int:
        if isinstance(date, datetime.datetime):
            date_value = date.date()
        else:
            date_value = date

        ppds = rc.additional_info.get("ppds", {})
        date_str = datetime.datetime.strftime(date_value, "%Y-%m-%d")
        if date_str in ppds:
            return ppds["ppds"]["days_min"]

        return False

class RService(models.Model):
    name = models.CharField(max_length=60)
    icon = models.FileField(upload_to="img/icon")

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        verbose_name = 'Услуга номера'
        verbose_name_plural = 'Услуги номера'

class HService(models.Model):
    name = models.CharField(max_length=60)
    section = models.CharField(max_length=50)
    icon = models.FileField(upload_to="img/icon/hservice/")

    def __str__(self):
        return '%s' % (self.name)

    def regen_upload_icon(self):
        service_name = self.name
        section_name = self.section

        icon_path = f"media/img/icon/hservice/{service_name}.svg"
        section_path = f"media/img/icon/hservice/{section_name}.svg"
        if os.path.exists(icon_path):
            self.icon.name = f'img/icon/hservice/{service_name}.svg'
            self.save()
            return self.icon
        elif os.path.exists(section_path):
            self.icon.name = f'img/icon/hservice/{section_name}.svg'
            self.save()
            return self.icon
        else:
            return None

    class Meta:
        verbose_name = 'Услуга отеля'
        verbose_name_plural = 'Услуги отеля'

class Address(models.Model):
    hotel = models.OneToOneField(
        Hotel, on_delete=models.CASCADE, related_name="adrress_hotel")
    city = models.CharField(max_length=50)  # Город
    region = models.CharField(max_length=50, null=True, blank=True)  # Район
    street = models.CharField(max_length=50)  # Улица
    body = models.CharField(max_length=50, null=True, blank=True)  # Корпус
    house = models.CharField(max_length=50)  # Дом
    floor = models.CharField(max_length=4, null=True, blank=True)  # Этаж
    apartment = models.CharField(
        max_length=15, null=True, blank=True)  # Квартира

    coordinates = models.CharField(max_length=100, null=True, blank=True)

    metro_cords = {
        "Новокосино, Калининская": [55.745113, 37.864052], "Новогиреево, Калининская": [55.752237, 37.814587], "Перово, Калининская": [55.75098, 37.78422], "Шоссе Энтузиастов, Калининская": [55.75809, 37.751703], "Авиамоторная, Калининская": [55.751933, 37.717444], "Площадь Ильича, Калининская": [55.747115, 37.680726], "Марксистская, Калининская": [55.740746, 37.65604], "Третьяковская, Калининская": [55.741125, 37.626142], "Ховрино, Замоскворецкая": [55.8777, 37.4877], "Беломорская, Замоскворецкая": [55.8651, 37.4764], "Речной вокзал, Замоскворецкая": [55.854152, 37.476728], "Водный стадион, Замоскворецкая": [55.838978, 37.487515], "Войковская, Замоскворецкая": [55.818923, 37.497791], "Сокол, Замоскворецкая": [55.805564, 37.515245], "Аэропорт, Замоскворецкая": [55.800441, 37.530477], "Динамо, Замоскворецкая": [55.789704, 37.558212], "Белорусская, Замоскворецкая": [55.777439, 37.582107], "Маяковская, Замоскворецкая": [55.769808, 37.596192], "Тверская, Замоскворецкая": [55.765343, 37.603918], "Театральная, Замоскворецкая": [55.758808, 37.61768], "Новокузнецкая, Замоскворецкая": [55.742391, 37.62928], "Павелецкая, Замоскворецкая": [55.729741, 37.638693], "Автозаводская, Замоскворецкая": [55.706634, 37.657008], "Технопарк, Замоскворецкая": [55.695, 37.664167], "Коломенская, Замоскворецкая": [55.677423, 37.663719], "Каширская, Замоскворецкая": [55.655745, 37.649683], "Кантемировская, Замоскворецкая": [55.636107, 37.656218], "Царицыно, Замоскворецкая": [55.620982, 37.669612], "Орехово, Замоскворецкая": [55.61269, 37.695214], "Домодедовская, Замоскворецкая": [55.610131, 37.717111], "Красногвардейская, Замоскворецкая": [55.614075, 37.742697], "Алма-Атинская, Замоскворецкая": [55.63349, 37.765678], "Медведково, Калужско-Рижская": [55.888103, 37.661562], "Бабушкинская, Калужско-Рижская": [55.870641, 37.664341], "Свиблово, Калужско-Рижская": [55.855558, 37.653379], "Ботанический сад, Калужско-Рижская": [55.844597, 37.637811], "ВДНХ, Калужско-Рижская": [55.819626, 37.640751], "Алексеевская, Калужско-Рижская": [55.807794, 37.638699], "Рижская, Калужско-Рижская": [55.792494, 37.636114], "Проспект Мира, Калужско-Рижская": [55.781827, 37.633199], "Сухаревская, Калужско-Рижская": [55.772315, 37.63285], "Тургеневская, Калужско-Рижская": [55.765371, 37.636732], "Китай-город, Калужско-Рижская": [55.756498, 37.631326], "Третьяковская, Калужско-Рижская": [55.74073, 37.625624], "Октябрьская, Калужско-Рижская": [55.731232, 37.612851], "Шаболовская, Калужско-Рижская": [55.718828, 37.607892], "Ленинский проспект, Калужско-Рижская": [55.70678, 37.58499], "Академическая, Калужско-Рижская": [55.687147, 37.5723], "Профсоюзная, Калужско-Рижская": [55.677671, 37.562595], "Новые Черемушки, Калужско-Рижская": [55.670077, 37.554493], "Калужская, Калужско-Рижская": [55.656682, 37.540075], "Беляево, Калужско-Рижская": [55.642357, 37.526115], "Коньково, Калужско-Рижская": [55.631857, 37.519156], "Теплый Стан, Калужско-Рижская": [55.61873, 37.505912], "Ясенево, Калужско-Рижская": [55.606182, 37.5334], "Новоясеневская, Калужско-Рижская": [55.601947, 37.553017], "Бульвар Рокоссовского, Сокольническая": [55.814916, 37.732227], "Черкизовская, Сокольническая": [55.802787, 37.744863], "Преображенская площадь, Сокольническая": [55.796322, 37.713582], "Сокольники, Сокольническая": [55.789282, 37.679895], "Красносельская, Сокольническая": [55.780014, 37.666097], "Комсомольская, Сокольническая": [55.774072, 37.654565], "Красные ворота, Сокольническая": [55.768307, 37.6478], "Чистые пруды, Сокольническая": [55.76499, 37.638293], "Лубянка, Сокольническая": [55.759889, 37.625336], "Охотный ряд, Сокольническая": [55.757228, 37.615078], "Библиотека им.Ленина, Сокольническая": [55.752123, 37.610388], "Кропоткинская, Сокольническая": [55.745297, 37.604217], "Парк культуры, Сокольническая": [55.736163, 37.595027], "Фрунзенская, Сокольническая": [55.727462, 37.58022], "Спортивная, Сокольническая": [55.722388, 37.562041], "Воробьевы горы, Сокольническая": [55.709169, 37.557293], "Университет, Сокольническая": [55.69329, 37.534511], "Проспект Вернадского, Сокольническая": [55.676549, 37.504584], "Юго-Западная, Сокольническая": [55.663146, 37.482852], "Тропарево, Сокольническая": [55.6459, 37.4725], "Румянцево, Сокольническая": [55.633, 37.4419], "Саларьево, Сокольническая": [55.6227, 37.424], "Филатов луг, Сокольническая": [55.5997, 37.4075], "Прокшино, Сокольническая": [55.5813, 37.4425], "Ольховая, Сокольническая": [55.5692, 37.4589], "Коммунарка, Сокольническая": [55.559765, 37.468716], "Щелковская, Арбатско-Покровская": [55.809962, 37.798261], "Первомайская, Арбатско-Покровская": [55.794376, 37.799364], "Измайловская, Арбатско-Покровская": [55.787713, 37.779896], "Партизанская, Арбатско-Покровская": [55.788401, 37.74882], "Семеновская, Арбатско-Покровская": [55.783096, 37.719289], "Электрозаводская, Арбатско-Покровская": [55.782057, 37.7053], "Бауманская, Арбатско-Покровская": [55.772405, 37.67904], "Курская, Арбатско-Покровская": [55.758564, 37.659039], "Площадь Революции, Арбатско-Покровская": [55.756741, 37.62236], "Арбатская, Арбатско-Покровская": [55.752312, 37.60349], "Смоленская, Арбатско-Покровская": [55.747713, 37.583802], "Киевская, Арбатско-Покровская": [55.743117, 37.564132], "Парк Победы, Арбатско-Покровская": [55.735679, 37.516865], "Славянский бульвар, Арбатско-Покровская": [55.729542, 37.470973], "Кунцевская, Арбатско-Покровская": [55.730673, 37.446522], "Молодежная, Арбатско-Покровская": [55.741375, 37.415627], "Крылатское, Арбатско-Покровская": [55.756842, 37.408139], "Строгино, Арбатско-Покровская": [55.803831, 37.402405], "Мякинино, Арбатско-Покровская": [55.823342, 37.385214], "Волоколамская, Арбатско-Покровская": [55.835154, 37.382453], "Митино, Арбатско-Покровская": [55.846098, 37.36122], "Пятницкое шоссе, Арбатско-Покровская": [55.853634, 37.353108], "Кунцевская, Филевская": [55.730815, 37.446754], "Пионерская, Филевская": [55.736027, 37.466728], "Филевский парк, Филевская": [55.739665, 37.483902], "Багратионовская, Филевская": [55.743544, 37.497042], "Фили, Филевская": [55.746763, 37.514035], "Кутузовская, Филевская": [55.740544, 37.5341], "Студенческая, Филевская": [55.738761, 37.54842], "Киевская, Филевская": [55.743168, 37.565425], "Смоленская, Филевская": [55.749083, 37.582173], "Арбатская, Филевская": [55.752122, 37.601553], "Александровский сад, Филевская": [55.752255, 37.608775], "Выставочная, Филевская": [55.750243, 37.542641], "Международная, Филевская": [55.748324, 37.533282], "Алтуфьево, Серпуховско-Тимирязевская": [55.899034, 37.586473], "Бибирево, Серпуховско-Тимирязевская": [55.883868, 37.603011], "Отрадное, Серпуховско-Тимирязевская": [55.864273, 37.605066], "Владыкино, Серпуховско-Тимирязевская": [55.848236, 37.590451], "Петровско-Разумовская, Серпуховско-Тимирязевская": [55.836565, 37.575512], "Тимирязевская, Серпуховско-Тимирязевская": [55.81866, 37.574498], "Дмитровская, Серпуховско-Тимирязевская": [55.808056, 37.581734], "Савёловская, Серпуховско-Тимирязевская": [55.794054, 37.587163], "Менделеевская, Серпуховско-Тимирязевская": [55.781999, 37.599141], "Цветной бульвар, Серпуховско-Тимирязевская": [55.771653, 37.620466], "Чеховская, Серпуховско-Тимирязевская": [55.765747, 37.608493], "Боровицкая, Серпуховско-Тимирязевская": [55.750399, 37.60934], "Полянка, Серпуховско-Тимирязевская": [55.736795, 37.618594], "Серпуховская, Серпуховско-Тимирязевская": [55.726548, 37.624792], "Тульская, Серпуховско-Тимирязевская": [55.70961, 37.622569], "Нагатинская, Серпуховско-Тимирязевская": [55.682099, 37.620917], "Нагорная, Серпуховско-Тимирязевская": [55.672962, 37.610397], "Нахимовский проспект, Серпуховско-Тимирязевская": [55.662379, 37.605274], "Севастопольская, Серпуховско-Тимирязевская": [55.651451, 37.59809], "Чертановская, Серпуховско-Тимирязевская": [55.640538, 37.606065], "Южная, Серпуховско-Тимирязевская": [55.622436, 37.609047], "Пражская, Серпуховско-Тимирязевская": [55.610962, 37.602386], "Улица Академика Янгеля, Серпуховско-Тимирязевская": [55.596753, 37.601498], "Аннино, Серпуховско-Тимирязевская": [55.583477, 37.596999], "Бульвар Дмитрия Донского, Серпуховско-Тимирязевская": [55.568201, 37.576856], "Планерная, Таганско-Краснопресненская": [55.859676, 37.436808], "Сходненская, Таганско-Краснопресненская": [55.84926, 37.44076], "Тушинская, Таганско-Краснопресненская": [55.825479, 37.437024], "Спартак, Таганско-Краснопресненская": [55.8182, 37.4352], "Щукинская, Таганско-Краснопресненская": [55.8094, 37.463241], "Октябрьское поле, Таганско-Краснопресненская": [55.793581, 37.493317], "Полежаевская, Таганско-Краснопресненская": [55.777201, 37.517895], "Беговая, Таганско-Краснопресненская": [55.773505, 37.545518], "Улица 1905 года, Таганско-Краснопресненская": [55.763944, 37.562271], "Баррикадная, Таганско-Краснопресненская": [55.760793, 37.581242], "Пушкинская, Таганско-Краснопресненская": [55.765607, 37.604356], "Кузнецкий мост, Таганско-Краснопресненская": [55.761498, 37.624423], "Китай-город, Таганско-Краснопресненская": [55.75436, 37.633877], "Таганская, Таганско-Краснопресненская": [55.739502, 37.653605], "Пролетарская, Таганско-Краснопресненская": [55.731546, 37.666917], "Волгоградский проспект, Таганско-Краснопресненская": [55.725546, 37.685197], "Текстильщики, Таганско-Краснопресненская": [55.709211, 37.732117], "Кузьминки, Таганско-Краснопресненская": [55.705493, 37.763295], "Рязанский проспект, Таганско-Краснопресненская": [55.716139, 37.792694], "Выхино, Таганско-Краснопресненская": [55.715983, 37.816788], "Лермонтовский проспект, Таганско-Краснопресненская": [55.702036, 37.851044], "Жулебино, Таганско-Краснопресненская": [55.684722, 37.855833], "Котельники, Таганско-Краснопресненская": [55.6743, 37.8582], "Новослободская, Кольцевая": [55.779606, 37.601252], "Проспект Мира, Кольцевая": [55.779584, 37.633646], "Комсомольская, Кольцевая": [55.775672, 37.654772], "Курская, Кольцевая": [55.758631, 37.661059], "Таганская, Кольцевая": [55.742396, 37.653334], "Павелецкая, Кольцевая": [55.731414, 37.636294], "Добрынинская, Кольцевая": [55.728994, 37.622533], "Октябрьская, Кольцевая": [55.729264, 37.611049], "Парк культуры, Кольцевая": [55.735221, 37.593095], "Киевская, Кольцевая": [55.74361, 37.56735], "Краснопресненская, Кольцевая": [55.760378, 37.577114], "Белорусская, Кольцевая": [55.775179, 37.582303], "Селигерская, Люблинско-Дмитровская": [55.86483, 37.55005], "Верхние Лихоборы, Люблинско-Дмитровская": [55.85566, 37.56282], "Окружная, Люблинско-Дмитровская": [55.848889, 37.571111], "Петровско-Разумовская, Люблинско-Дмитровская": [55.836667, 37.575556], "Фонвизинская, Люблинско-Дмитровская": [55.822778, 37.588056], "Бутырская , Люблинско-Дмитровская": [55.813333, 37.602778], "Марьина Роща, Люблинско-Дмитровская": [55.793723, 37.61618], "Достоевская, Люблинско-Дмитровская": [55.781667, 37.613889], "Трубная, Люблинско-Дмитровская": [55.76771, 37.621926], "Сретенский бульвар, Люблинско-Дмитровская": [55.766106, 37.635688], "Чкаловская, Люблинско-Дмитровская": [55.755951, 37.659293], "Римская, Люблинско-Дмитровская": [55.747027, 37.679996], "Крестьянская застава, Люблинско-Дмитровская": [55.732278, 37.665325], "Дубровка, Люблинско-Дмитровская": [55.71807, 37.676259], "Кожуховская, Люблинско-Дмитровская": [55.706156, 37.68544], "Печатники, Люблинско-Дмитровская": [55.692921, 37.728338], "Волжская, Люблинско-Дмитровская": [55.690446, 37.754314], "Люблино, Люблинско-Дмитровская": [55.676596, 37.761639], "Братиславская, Люблинско-Дмитровская": [55.658817, 37.748415], "Марьино, Люблинско-Дмитровская": [55.649158, 37.743844], "Борисово, Люблинско-Дмитровская": [55.6325, 37.743333], "Шипиловская, Люблинско-Дмитровская": [55.621667, 37.743611], "Зябликово, Люблинско-Дмитровская": [55.611944, 37.745278], "Каширская, Каховская": [55.654327, 37.647705], "Варшавская, Каховская": [55.653294, 37.619522], "Каховская, Каховская": [55.652923, 37.596573], "Бунинская аллея, Бутовская": [55.537977, 37.515899], "Улица Горчакова, Бутовская": [55.542281, 37.532063], "Бульвар Адмирала Ушакова, Бутовская": [55.545207, 37.542329], "Улица Скобелевская, Бутовская": [55.548103, 37.552721], "Улица Старокачаловская, Бутовская": [55.569194, 37.576074], "Лесопарковая, Бутовская": [55.581656, 37.577816], "Битцевский Парк, Бутовская": [55.600066, 37.556058], "Деловой центр, Солнцевская": [55.7491, 37.5395], "Парк Победы, Солнцевская": [55.736478, 37.514401], "Минская, Солнцевская": [55.7232, 37.5038], "Ломоносовский проспект, Солнцевская": [55.7055, 37.5225], "Раменки, Солнцевская": [55.6961, 37.505], "Мичуринский проспект, Солнцевская": [55.6888, 37.485], "Озёрная, Солнцевская": [55.6698, 37.4495], "Говорово, Солнцевская": [55.6588, 37.4174], "Солнцево, Солнцевская": [55.649, 37.3911], "Боровское шоссе, Солнцевская": [55.647, 37.3701], "Новопеределкино, Солнцевская": [55.6385, 37.3544], "Рассказовка, Солнцевская": [55.6324, 37.3328], "Окружная, МЦК": [55.848889, 37.571111], "Владыкино, МЦК": [55.847222, 37.591944], "Ботанический сад, МЦК": [55.845556, 37.640278], "Ростокино, МЦК": [55.839444, 37.667778], "Белокаменная, МЦК": [55.83, 37.700556], "Бульвар Рокоссовского, МЦК": [55.817222, 37.736944], "Локомотив, МЦК": [55.803219, 37.745742], "Измайлово, МЦК": [55.788611, 37.742778], "Соколиная Гора, МЦК": [55.77, 37.745278], "Шоссе Энтузиастов, МЦК": [55.758633, 37.748477], "Андроновка, МЦК": [55.741111, 37.734444], "Нижегородская, МЦК": [55.732222, 37.72825], "Новохохловская, МЦК": [55.723889, 37.716111], "Угрешская, МЦК": [55.718333, 37.697778], "Дубровка, МЦК": [55.71268, 37.677775], "Автозаводская, МЦК": [55.70631, 37.66314], "ЗИЛ, МЦК": [55.698333, 37.648333], "Верхние Котлы, МЦК": [55.69, 37.618889], "Крымская, МЦК": [55.690038, 37.605], "Площадь Гагарина, МЦК": [55.706944, 37.585833], "Лужники, МЦК": [55.720278, 37.563056], "Кутузовская, МЦК": [55.740833, 37.533333], "Деловой центр, МЦК": [55.747222, 37.532222], "Шелепиха, МЦК": [55.7575, 37.525556], "Хорошево, МЦК": [55.777222, 37.507222], "Зорге, МЦК": [55.787778, 37.504444], "Панфиловская, МЦК": [55.799167, 37.498889], "Стрешнево, МЦК": [55.813611, 37.486944], "Балтийская, МЦК": [55.825833, 37.496111], "Коптево, МЦК": [55.839637, 37.520037], "Лихоборы, МЦК": [55.847222, 37.551389], "Тимирязевская, Монорельс": [55.819049, 37.578882], "Улица Милашенкова, Монорельс": [55.821876, 37.591206], "Телецентр, Монорельс": [55.821795, 37.608975], "Улица Академика Королёва, Монорельс": [55.821821, 37.627167], "Выставочный центр, Монорельс": [55.824086, 37.638494], "Улица Сергея Эйзенштейна, Монорельс": [55.829305, 37.644997], "Мичуринский проспект, Большая кольцевая линия": [55.688333, 37.485], "Проспект Вернадского, Большая кольцевая линия": [55.677778, 37.505], "Новаторская, Большая кольцевая линия": [55.670833, 37.52], "Воронцовская, Большая кольцевая линия": [55.658333, 37.540833], "Зюзино, Большая кольцевая линия": [55.489722, 37.572222], "Каховская, Большая кольцевая линия": [55.653056, 37.598333], "Варшавская, Большая кольцевая линия": [55.653333, 37.619444], "Каширская, Большая кольцевая линия": [55.655, 37.648611], "Кленовый бульвар, Большая кольцевая линия": [55.674444, 37.680833], "Нагатинский Затон, Большая кольцевая линия": [55.684444, 37.703611], "Печатники, Большая кольцевая линия": [55.694722, 37.7275], "Текстильщики, Большая кольцевая линия": [55.708333, 37.728333], "Нижегородская, Большая кольцевая линия": [55.7325, 37.728611], "Авиамоторная, Большая кольцевая линия": [55.753056, 37.718611], "Лефортово, Большая кольцевая линия": [55.764444, 37.702778], "Электрозаводская, Большая кольцевая линия": [55.782057, 37.7053], "Сокольники, Большая кольцевая линия": [55.791111, 37.678889], "Рижская, Большая кольцевая линия": [55.792222, 37.633889], "Марьина Роща, Большая кольцевая линия": [55.798333, 37.617222], "Савёловская, Большая кольцевая линия": [55.794054, 37.587163], "Петровский парк, Большая кольцевая линия": [55.79233, 37.55952], "ЦСКА, Большая кольцевая линия": [55.78643, 37.53502], "Хорошевская, Большая кольцевая линия": [55.77643, 37.51981], "Шелепиха, Большая кольцевая линия": [55.75723, 37.52571], "Деловой центр, Большая кольцевая линия": [55.7491, 37.5395], "Народное Ополчение, Большая кольцевая линия": [55.775278, 39.484444], "Мнёвники, Большая кольцевая линия": [55.761153, 37.47139], "Терехово, Большая кольцевая линия": [55.749167, 38.460556], "Кунцевская, Большая кольцевая линия": [55.730278, 37.445833], "Давыдково, Большая кольцевая линия": [55.765278, 37.451667], "Аминьевская, Большая кольцевая линия": [55.697222, 37.464167], "Косино, Некрасовская": [55.7026, 37.8511], "Улица Дмитриевского, Некрасовская": [55.7093, 37.8792], "Лухмановская, Некрасовская": [55.7078, 37.9004], "Некрасовка, Некрасовская": [55.7029, 37.9264], "Юго-Восточная, Некрасовская": [55.71, 37.82], "Окская, Некрасовская": [55.72, 37.77], "Стахановская, Некрасовская": [55.73, 37.76], "Нижегородская, Некрасовская": [55.73, 37.73], "Лефортово, Некрасовская": [55.764444, 37.702778], "Электрозаводская, Некрасовская": [55.782057, 37.7053], "Авиамоторная, Некрасовская": [55.751933, 37.717444], "Лобня, МЦД - 1": [56.0048, 37.29057], "Шереметьевская, МЦД - 1": [55.983882, 37.498752], "Хлебниково, МЦД - 1": [55.970682, 37.504638], "Водники, МЦД - 1": [55.953419, 37.511143], "Долгопрудная, МЦД - 1": [55.938656, 37.520542], "Новодачная, МЦД - 1": [55.924459, 37.527877], "Марк, МЦД - 1": [55.904458, 37.538242], "Лианозово, МЦД - 1": [55.897316, 37.553261], "Бескудниково, МЦД - 1": [55.882713, 37.567768], "Дегунино, МЦД - 1": [55.86586, 37.573235],
        "Окружная, МЦД - 1": [55.848889, 37.571111], "Тимирязевская, МЦД - 1": [55.81866, 37.574498], "Савёловская, МЦД - 1": [55.793936, 37.587038], "Белорусская, МЦД - 1": [55.775179, 37.582303], "Беговая, МЦД - 1": [55.773505, 37.545518], "Тестовская, МЦД - 1": [55.754292, 37.531551], "Фили, МЦД - 1": [55.744263, 37.514526], "Славянский бульвар, МЦД - 1": [55.729722, 37.470556], "Кунцевская, МЦД - 1": [55.730554, 37.445591], "Рабочий Посёлок, МЦД - 1": [55.726957, 37.415577], "Сетунь, МЦД - 1": [55.723713, 37.397259], "Немчиновка, МЦД - 1": [55.715668, 37.374611], "Сколково, МЦД - 1": [55.666801, 37.424618], "Баковка, МЦД - 1": [55.682816, 37.315205], "Одинцово, МЦД - 1": [55.67798, 37.27773], "Нахабино, МЦД - 2": [55.841522, 37.185204], "Аникеевка, МЦД - 2": [55.832099, 37.219829], "Опалиха, МЦД - 2": [55.82333, 37.246843], "Красногорская, МЦД - 2": [55.814571, 37.303337], "Павшино, МЦД - 2": [55.815231, 37.341461], "Пенягино, МЦД - 2": [55.822539, 37.361049], "Волоколамская, МЦД - 2": [55.835154, 37.382453], "Трикотажная, МЦД - 2": [55.833137, 37.398967], "Тушинская, МЦД - 2": [55.825479, 37.437024], "Покровское-Стрешнево, МЦД - 2": [55.814247, 37.47678], "Стрешнево, МЦД - 2": [55.813611, 37.486944], "Красный Балтиец, МЦД - 2": [55.815514, 37.526367], "Гражданская, МЦД - 2": [55.805527, 37.55315], "Дмитровская, МЦД - 2": [55.808056, 37.581734], "Рижская, МЦД - 2": [55.792494, 37.636114], "Каланчёвская, МЦД - 2": [55.77667, 37.65111], "Курская, МЦД - 2": [55.757622, 37.660767], "Москва Товарная, МЦД - 2": [55.745358, 37.688839], "Калитники, МЦД - 2": [55.733981, 37.702203], "Новохохловская, МЦД - 2": [55.718523, 37.719236], "Текстильщики, МЦД - 2": [55.708934, 37.731283], "Люблино, МЦД - 2": [55.676596, 37.761639], "Депо, МЦД - 2": [55.674257, 37.728446], "Перерва, МЦД - 2": [55.660809, 37.716278], "Курьяново, МЦД - 2": [55.649722, 37.701667], "Москворечье, МЦД - 2": [55.641239, 37.689789], "Царицыно, МЦД - 2": [55.618309, 37.668846], "Покровское, МЦД - 2": [55.814247, 37.47678], "Красный строитель, МЦД - 2": [55.589455, 37.615093], "Битца, МЦД - 2": [55.571186, 37.611443], "Бутово, МЦД - 2": [55.548279, 37.555668], "Щербинка, МЦД - 2": [55.509724, 37.562008], "Остафьево, МЦД - 2": [55.50337, 37.520055], "Силикатная, МЦД - 2": [55.470278, 37.555278], "Подольск, МЦД - 2": [55.431667, 37.565], "Девяткино, Кировско-Выборгская": [60.050182, 30.443045], "Гражданский проспект, Кировско-Выборгская": [60.034969, 30.418224], "Академическая, Кировско-Выборгская": [60.012806, 30.396044], "Политехническая, Кировско-Выборгская": [60.008942, 30.370907], "Площадь Мужества, Кировско-Выборгская": [59.999828, 30.366159], "Лесная, Кировско-Выборгская": [59.984947, 30.344259], "Выборгская, Кировско-Выборгская": [59.970925, 30.347408], "Площадь Ленина, Кировско-Выборгская": [59.955611, 30.35605], "Чернышевская, Кировско-Выборгская": [59.94453, 30.359919], "Площадь Восстания, Кировско-Выборгская": [59.930279, 30.361069], "Владимирская, Кировско-Выборгская": [59.927628, 30.347898], "Пушкинская, Кировско-Выборгская": [59.92065, 30.329599], "Технологический институт 1, Кировско-Выборгская": [59.916512, 30.318485], "Балтийская, Кировско-Выборгская": [59.907211, 30.299578], "Нарвская, Кировско-Выборгская": [59.901218, 30.274908], "Кировский завод, Кировско-Выборгская": [59.879688, 30.261921], "Автово, Кировско-Выборгская": [59.867325, 30.261337], "Ленинский проспект, Кировско-Выборгская": [59.85117, 30.268274], "Проспект Ветеранов, Кировско-Выборгская": [59.84211, 30.250588], "Парнас, Московско-Петроградская": [60.06699, 30.333839], "Проспект Просвещения, Московско-Петроградская": [60.051456, 30.332544], "Озерки, Московско-Петроградская": [60.037098, 30.321495], "Удельная, Московско-Петроградская": [60.016697, 30.315607], "Пионерская, Московско-Петроградская": [60.002487, 30.296759], "Чёрная речка, Московско-Петроградская": [59.985455, 30.300833], "Петроградская, Московско-Петроградская": [59.966389, 30.311293], "Горьковская, Московско-Петроградская": [59.956112, 30.31889], "Невский проспект, Московско-Петроградская": [59.935421, 30.327052], "Сенная площадь, Московско-Петроградская": [59.927135, 30.320316], "Технологический институт 2, Московско-Петроградская": [59.916512, 30.318485], "Фрунзенская, Московско-Петроградская": [59.906273, 30.31745], "Московские ворота, Московско-Петроградская": [59.891788, 30.317873], "Электросила, Московско-Петроградская": [59.879189, 30.318659], "Парк Победы, Московско-Петроградская": [59.866344, 30.321802], "Московская, Московско-Петроградская": [59.848873, 30.321483], "Звёздная, Московско-Петроградская": [59.833241, 30.349428], "Купчино, Московско-Петроградская": [59.829781, 30.375702], "Беговая, Невско-Василеостровская": [59.98723, 30.20247], "Приморская, Невско-Василеостровская": [59.948521, 30.23447], "Василеостровская, Невско-Василеостровская": [59.942577, 30.278254], "Гостиный двор, Невско-Василеостровская": [59.933933, 30.33341], "Маяковская, Невско-Василеостровская": [59.931366, 30.354645], "Площадь Александра Невского 1, Невско-Василеостровская": [59.924369, 30.384989], "Елизаровская, Невско-Василеостровская": [59.89669, 30.423656], "Ломоносовская, Невско-Василеостровская": [59.877342, 30.441715], "Пролетарская, Невско-Василеостровская": [59.865, 30.47], "Обухово, Невско-Василеостровская": [59.848709, 30.457743], "Рыбацкое, Невско-Василеостровская": [59.830986, 30.501259], "Зенит, Невско-Василеостровская": [59.972222, 30.211667], "Спасская, Правобережная": [59.927135, 30.320316], "Достоевская, Правобережная": [59.928234, 30.346029], "Лиговский проспект, Правобережная": [59.920811, 30.355055], "Площадь Александра Невского 2, Правобережная": [59.923563, 30.383421], "Новочеркасская, Правобережная": [59.929092, 30.411915], "Ладожская, Правобережная": [59.93243, 30.439274], "Проспект Большевиков, Правобережная": [59.919838, 30.466757], "Улица Дыбенко, Правобережная": [59.907417, 30.483311], "Комендантский проспект, Фрунзенско-Приморская": [60.008591, 30.258663], "Старая Деревня, Фрунзенско-Приморская": [59.989433, 30.255163], "Крестовский остров, Фрунзенско-Приморская": [59.971821, 30.259436], "Чкаловская, Фрунзенско-Приморская": [59.961033, 30.292006], "Спортивная, Фрунзенско-Приморская": [59.952026, 30.291338], "Адмиралтейская, Фрунзенско-Приморская": [59.935867, 30.31523], "Садовая, Фрунзенско-Приморская": [59.926739, 30.317753], "Звенигородская, Фрунзенско-Приморская": [59.92065, 30.329599], "Обводный Канал, Фрунзенско-Приморская": [59.914686, 30.34815], "Волковская, Фрунзенско-Приморская": [59.896023, 30.35754], "Бухарестская, Фрунзенско-Приморская": [59.883769, 30.368932], "Международная, Фрунзенско-Приморская": [59.870203, 30.379289], "Дунайская, Фрунзенско-Приморская": [59.839889, 30.410667], "Проспект Славы, Фрунзенско-Приморская": [59.856704, 30.395402], "Шушары, Фрунзенско-Приморская": [59.819973, 30.432718], "Проспект Космонавтов, Север-Юг": [56.900393, 60.613878], "Уралмаш, Север-Юг": [56.887674, 60.614165], "Машиностроителей, Север-Юг": [56.878517, 60.61218], "Уральская, Север-Юг": [56.858056, 60.600816], "Динамо, Север-Юг": [56.847818, 60.599406], "Площадь 1905 года, Север-Юг": [56.837982, 60.59734], "Геологическая, Север-Юг": [56.826715, 60.603754], "Чкаловская, Север-Юг": [56.808502, 60.610698], "Ботаническая, Север-Юг": [56.797487, 60.633362], "Авиастроительная , Центральная": [55.828897, 49.081403], "Северный вокзал, Центральная": [55.841519, 49.081778], "Яшьлек (Юность), Центральная": [55.827843, 49.082905], "Козья слобода, Центральная": [55.817608, 49.097646], "Кремлевская, Центральная": [55.795206, 49.105426], "Площадь Тукая, Центральная": [55.787163, 49.122126], "Суконная слобода, Центральная": [55.777094, 49.142275], "Аметьево, Центральная": [55.765346, 49.165083], "Горки, Центральная": [55.760763, 49.189679], "Проспект Победы, Центральная": [55.750109, 49.207735], "Дубравная, Центральная": [55.7425, 49.2197], "Горьковская, Автозаводская": [56.313933, 43.99482], "Московская, Автозаводская": [56.321097, 43.945799], "Чкаловская, Автозаводская": [56.310637, 43.936933], "Ленинская, Автозаводская": [56.297798, 43.937328], "Заречная, Автозаводская": [56.285144, 43.927528], "Двигатель Революции, Автозаводская": [56.277093, 43.922012], "Пролетарская, Автозаводская": [53.88972, 27.585466], "Автозаводская, Автозаводская": [53.868945, 27.648788], "Комсомольская, Автозаводская": [56.252662, 43.889888], "Кировская, Автозаводская": [56.247426, 43.876719], "Парк Культуры, Автозаводская": [56.242034, 43.85816], "Стрелка, Сормовская": [56.3343, 43.9597], "Московская, Сормовская": [56.321097, 43.945799], "Канавинская, Сормовская": [56.320273, 43.927438], "Бурнаковская, Сормовская": [56.325704, 43.911897], "Буревестник, Сормовская": [56.333834, 43.892799], "Заельцовская, Ленинская": [55.059291, 82.912569], "Гагаринская, Ленинская": [55.051071, 82.91477], "Красный проспект, Ленинская": [55.040998, 82.917447], "Площадь Ленина, Ленинская": [55.029941, 82.92069], "Октябрьская, Ленинская": [55.018789, 82.939007], "Речной вокзал, Ленинская": [55.008738, 82.93827], "Студенческая, Ленинская": [54.989089, 82.906631], "Площадь Маркса, Ленинская": [54.982931, 82.89313], "Площадь Гарина-Михайловского, Дзержинская": [55.035947, 82.897783], "Сибирская, Дзержинская": [55.042163, 82.919172], "Маршала Покрышкина, Дзержинская": [55.043634, 82.935566], "Березовая роща, Дзержинская": [55.043242, 82.952913], "Золотая нива, Дзержинская": [55.037928, 82.976044], "Алабинская, Первая": [53.209689, 50.134417], "Российская, Первая": [53.211385, 50.15022], "Московская, Первая": [53.203791, 50.159832], "Гагаринская, Первая": [53.200442, 50.176595], "Спортивная, Первая": [53.201121, 50.199286], "Советская, Первая": [53.201736, 50.220657], "Победа, Первая": [53.207313, 50.236414], "Безымянка, Первая": [53.212997, 50.248891], "Кировская, Первая": [53.211352, 50.269777], "Юнгородок, Первая": [53.212701, 50.282982], "Академгородок, Святошинско-Броварская": [50.464784, 30.355511], "Житомирская, Святошинско-Броварская": [50.455884, 30.36479], "Святошин, Святошинско-Броварская": [50.457685, 30.391776], "Нивки, Святошинско-Броварская": [50.458602, 30.405682], "Берестейская, Святошинско-Броварская": [50.458562, 30.420522], "Шулявская, Святошинско-Броварская": [50.454622, 30.445208], "Политехнический институт, Святошинско-Броварская": [50.450814, 30.466327], "Вокзальная, Святошинско-Броварская": [50.44178, 30.488273], "Университет, Святошинско-Броварская": [50.444401, 30.506006], "Театральная, Святошинско-Броварская": [50.445135, 30.518178], "Крещатик, Святошинско-Броварская": [50.447218, 30.524933], "Арсенальная, Святошинско-Броварская": [50.444332, 30.545379], "Днепр, Святошинско-Броварская": [50.441217, 30.559374], "Гидропарк, Святошинско-Броварская": [50.445956, 30.57699], "Левобережная, Святошинско-Броварская": [50.4518, 30.59811], "Дарница, Святошинско-Броварская": [50.455924, 30.612905], "Черниговская, Святошинско-Броварская": [50.459852, 30.630269], "Лесная, Святошинско-Броварская": [50.464629, 30.645541], "Героев Днепра, Куреневско-Красноармейская": [50.52258, 30.498891], "Минская, Куреневско-Красноармейская": [50.512196, 30.498541], "Оболонь, Куреневско-Красноармейская": [50.501466, 30.498253], "Петровка, Куреневско-Красноармейская": [50.486074, 30.497885], "Тараса Шевченко, Куреневско-Красноармейская": [50.473286, 30.505134], "Контрактовая площадь, Куреневско-Красноармейская": [50.465604, 30.514836], "Почтовая площадь, Куреневско-Красноармейская": [50.458935, 30.524933], "Майдан Независимости, Куреневско-Красноармейская": [50.450028, 30.524196], "Площадь Льва Толстого, Куреневско-Красноармейская": [50.439221, 30.516327], "Олимпийская, Куреневско-Красноармейская": [50.432244, 30.51621], "Дворец \"Украина\", Куреневско-Красноармейская": [50.420641, 30.520738], "Лыбедская, Куреневско-Красноармейская": [50.412714, 30.524879], "Демиевская, Куреневско-Красноармейская": [50.404563, 30.516615], "Голосеевская, Куреневско-Красноармейская": [50.397879, 30.510066], "Васильковская, Куреневско-Красноармейская": [50.392815, 30.485551], "Выставочный центр, Куреневско-Красноармейская": [50.382092, 30.477134], "Ипподром, Куреневско-Красноармейская": [50.376526, 30.468923], "Теремки, Куреневско-Красноармейская": [50.367044, 30.454203], "Сырец, Сырецко-Печерская": [50.476221, 30.430736], "Дорогожичи, Сырецко-Печерская": [50.473452, 30.448406], "Лукьяновская, Сырецко-Печерская": [50.462249, 30.482101], "Золотые ворота, Сырецко-Печерская": [50.448342, 30.513668], "Дворец спорта, Сырецко-Печерская": [50.437838, 30.520684], "Кловская, Сырецко-Печерская": [50.436731, 30.531922], "Печерская, Сырецко-Печерская": [50.427315, 30.538776], "Дружбы народов, Сырецко-Печерская": [50.418001, 30.544462], "Выдубичи, Сырецко-Печерская": [50.401428, 30.560686], "Славутич, Сырецко-Печерская": [50.394164, 30.604452], "Осокорки, Сырецко-Печерская": [50.395537, 30.616148], "Позняки, Сырецко-Печерская": [50.398344, 30.63433], "Харьковская, Сырецко-Печерская": [50.401072, 30.652], "Вырлица, Сырецко-Печерская": [50.403185, 30.665969], "Бориспольская, Сырецко-Печерская": [50.403403, 30.682974], "Красный хутор, Сырецко-Печерская": [50.409505, 30.695918], "Вокзальная, Центрально-Заводская": [48.475457, 35.015926], "Метростроителей, Центрально-Заводская": [48.475218, 34.995731], "Металлургов, Центрально-Заводская": [48.476634, 34.979517], "Заводская, Центрально-Заводская": [48.475821, 34.959422], "Проспект свободы, Центрально-Заводская": [48.479871, 34.943027], "Коммунаровская, Центрально-Заводская": [48.479298, 34.92657], "Холодная гора, Холодногорско-Заводская": [49.982512, 36.181804], "Южный вокзал, Холодногорско-Заводская": [49.989613, 36.205178], "Центральный рынок, Холодногорско-Заводская": [49.99277, 36.219731], "Советская, Холодногорско-Заводская": [49.991084, 36.232568], "Проспект Гагарина, Холодногорско-Заводская": [49.980838, 36.243402], "Спортивная, Холодногорско-Заводская": [49.979494, 36.260532], "Завод имени Малышева, Холодногорско-Заводская": [49.975966, 36.280996], "Московский проспект, Холодногорско-Заводская": [49.972259, 36.301666], "Маршала Жукова, Холодногорско-Заводская": [49.966262, 36.321187], "Советской армии, Холодногорско-Заводская": [49.961852, 36.342926], "Имени А. С. Масельского, Холодногорско-Заводская": [49.958526, 36.359787], "Тракторный завод, Холодногорско-Заводская": [49.952614, 36.37876], "Пролетарская, Холодногорско-Заводская": [49.946562, 36.399062], "Героев труда, Салтовская линия": [50.025398, 36.336287], "Студенческая, Салтовская линия": [50.017683, 36.329972], "Академика Павлова, Салтовская линия": [50.008965, 36.317755], "Академика Барабашова, Салтовская линия": [50.002313, 36.304092], "Киевская, Салтовская линия": [50.001213, 36.270279], "Пушкинская, Салтовская линия": [50.003685, 36.247489], "Университет, Салтовская линия": [50.004501, 36.233781], "Исторический музей, Салтовская линия": [49.992926, 36.231211], "Алексеевская, Алексеевская": [50.0496, 36.20666], "23 Августа, Алексеевская": [50.035524, 36.220279], "Ботанический сад, Алексеевская": [50.026659, 36.222938], "Научная, Алексеевская": [50.013, 36.226962], "Госпром, Алексеевская": [50.004797, 36.231571], "Архитектора Бекетова, Алексеевская": [49.998966, 36.240518], "Площадь Восстания, Алексеевская": [49.988652, 36.264808], "Метростроителей имени Ващенко, Алексеевская": [49.978915, 36.262823], "Уручье, Московская": [53.945348, 27.68782], "Борисовский тракт, Московская": [53.938506, 27.665865], "Восток, Московская": [53.934509, 27.651483], "Московская, Московская": [53.927978, 27.627812], "Парк Челюскинцев, Московская": [53.924214, 27.613646], "Академия наук, Московская": [53.92187, 27.599066], "Площадь Якуба Коласа, Московская": [53.915369, 27.583265], "Площадь Победы, Московская": [53.908644, 27.575054], "Октябрьская, Московская": [53.901562, 27.561068], "Площадь Ленина, Московская": [53.893875, 27.548015], "Институт Культуры, Московская": [53.885899, 27.538852], "Грушевка, Московская": [53.88669, 27.514786], "Михалово, Московская": [53.876664, 27.49691], "Петровщина, Московская": [53.86458, 27.485807], "Малиновка, Московская": [53.849722, 27.474722], "Каменная Горка, Автозаводская": [53.90683, 27.437558], "Кунцевщина, Автозаводская": [53.906236, 27.453916], "Спортивная, Автозаводская": [53.908501, 27.48083], "Пушкинская, Автозаводская": [53.909519, 27.495499], "Молодежная, Автозаводская": [53.906527, 27.521308], "Фрунзенская, Автозаводская": [53.905286, 27.539328], "Немига, Автозаводская": [53.905615, 27.55415], "Купаловская, Автозаводская": [53.901408, 27.561247], "Первомайская, Автозаводская": [53.893763, 27.570167], "Тракторный завод, Автозаводская": [53.890033, 27.614374], "Партизанская, Автозаводская": [53.87582, 27.628998], "Могилевская, Автозаводская": [53.861862, 27.674381], "Вокзальная, Зеленолужская": [53.889722, 27.546944], "Юбилейная площадь, Зеленолужская": [53.904406, 27.539975], "Площадь Франтишка Богушевича, Зеленолужская": [53.896667, 27.538333], "Ковальская Слобода, Зеленолужская": [53.874167, 27.549444], "Райымбек батыра, Первая": [43.271201, 76.9448], "Жибек Жолы, Первая": [43.260199, 76.946103], "Алмалы, Первая": [43.251295, 76.945456], "Абая, Первая": [43.242548, 76.949588], "Байконур, Первая": [43.240401, 76.927696], "Театр имени Ауэзова, Первая": [43.240362, 76.917519], "Алатау, Первая": [43.239041, 76.897612], "Сайран, Первая": [43.2362, 76.8764], "Москва, Первая": [43.23, 76.867], "Сары-Арка, Первая": [43.22, 76.851111], "Бауыржан Момышулы, Первая": [43.216389, 76.838056]}

    def full(self):
        parts = {"city": self.city, "region": self.region, "street": self.street,
                 "body": self.body, "house": self.house, "floor": self.floor, "apartment": self.apartment}
        return ", ".join([f"{value}" for key, value in parts.items() if value])

    def short(self):
        parts = {"city": self.city, "street": self.street, "house": self.house}
        return ", ".join([str(value) for value in parts.values() if value is not None])

    def new(republic, city, region, street, house, floor, apartment):
        address = Address.objects.create(
            republic=republic or None,
            city=city or None,
            region=region or None,
            street=street or None,
            house=house or None,
            floor=floor or None,
            apartment=apartment or None,
        )

        return address

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'

class Comment(models.Model):
    hotel = models.ForeignKey(
        Hotel, on_delete=models.CASCADE, related_name="comments")
    rc = models.ForeignKey(RCategory, on_delete=models.CASCADE,
                           related_name="comments", null=True, blank=True)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="comments", null=True, blank=True)

    # Если нету пользователя для отзыва (Вручную созданый или спарсеный)
    author_name = models.CharField(max_length=100, null=True, blank=True)
    # Если нету комнаты для отзыва (Вручную созданый или спарсеный)
    author_room = models.CharField(max_length=200, null=True, blank=True)

    date = models.DateTimeField()

    location = models.FloatField(default=0)  # Расположение
    price_quality_ratio = models.FloatField(
        default=0)  # Соотношение цена/качество
    purity = models.FloatField(default=0)  # Чистота

    food = models.FloatField(default=0)  # Питание
    service = models.FloatField(default=0)  # Обслуживание
    number_quality = models.FloatField(default=0)  # Номер

    hygiene_products = models.CharField(
        max_length=50, default=0)  # Средства гигиены
    wifi_quality = models.CharField(max_length=50, default=0)  # Качество Wi-Fi

    what_is_good_text = models.TextField(null=True, blank=True)
    what_is_bad_text = models.TextField(null=True, blank=True)

    overall_rating = models.FloatField(default=0)
    reply = models.TextField(null=True, blank=True)

    is_pending = models.BooleanField(default=False)

    # profanity_words = [
    #     "блежни",
    #     "блудилищ",
    #     "бля",
    #     "бляб",
    #     "блябуд",
    #     "бляду",
    #     "блядунь",
    #     "бляд",
    #     "блядюг",
    #     "взьебк",
    #     "волосянк",
    #     "взьебыват",
    #     "вз'ебыват",
    #     "выблядо",
    #     "выбляды",
    #     "выебат",
    #     "выет",
    #     "выпердет",
    #     "высратьс",
    #     "выссатьс",
    #     "говенк",
    #     "говенны",
    #     "говешк",
    #     "говнази",
    #     "говнец",
    #     "говн",
    #     "говное",
    #     "говночис",
    #     "говню",
    #     "говнюх",
    #     "говнядин",
    #     "говня",
    #     "говняны",
    #     "говнят",
    #     "гондо",
    #     "дерм",
    #     "долбое",
    #     "дрисн",
    #     "дрис",
    #     "дристат",
    #     "дристанут",
    #     "дристу",
    #     "дристух",
    #     "дрочен",
    #     "дрочил",
    #     "дрочилк",
    #     "дрочит",
    #     "дрочк",
    #     "ебал",
    #     "ебальни",
    #     "ебанут",
    #     "ебаны",
    #     "ебар",
    #     "ебатори",
    #     "ебат",
    #     "ебатьс",
    #     "ебе",
    #     "ебливы",
    #     "ебл",
    #     "ебнут",
    #     "ебнутьс",
    #     "ебн",
    #     "ебу",
    #     "елд",
    #     "елда",
    #     "елдачит",
    #     "заговнят",
    #     "задристат",
    #     "задрок",
    #     "заеб",
    #     "заебане",
    #     "заебат",
    #     "заебатьс",
    #     "заебыватьс",
    #     "зает",
    #     "залуп",
    #     "залупатьс",
    #     "залупит",
    #     "залупитьс",
    #     "замудохатьс",
    #     "засеру",
    #     "засер",
    #     "засерат",
    #     "засират",
    #     "засране",
    #     "засру",
    #     "захуячит",
    #     "злоебучи",
    #     "изговнят",
    #     "изговнятьс",
    #     "кляпыжитьс",
    #     "курв",
    #     "курвено",
    #     "курви",
    #     "курвяжни",
    #     "курвяжниц",
    #     "курвяжны",
    #     "манд",
    #     "мандавошк",
    #     "манде",
    #     "мандет",
    #     "мандищ",
    #     "мандю",
    #     "мине",
    #     "минетчи",
    #     "минетчиц",
    #     "мокрохвостк",
    #     "мокрощелк",
    #     "муда",
    #     "муд",
    #     "мудет",
    #     "мудил",
    #     "мудисты",
    #     "мудн",
    #     "мудое",
    #     "мудозво",
    #     "муйн",
    #     "набздет",
    #     "наговнят",
    #     "надристат",
    #     "надрочит",
    #     "наебат",
    #     "наебнутьс",
    #     "наебыват",
    #     "нассат",
    #     "нахезат",
    #     "нахуйни",
    #     "насцат",
    #     "обдристатьс",
    #     "обдристатьс",
    #     "обосране",
    #     "обосрат",
    #     "обосцат",
    #     "обосцатьс",
    #     "обсират",
    #     "опизд",
    #     "отпиздячит",
    #     "отпорот",
    #     "отъет",
    #     "охуевательски",
    #     "охуеват",
    #     "охуевающи",
    #     "охует",
    #     "охуительны",
    #     "охуячиват",
    #     "охуячит",
    #     "педри",
    #     "перде",
    #     "пердени",
    #     "пердет",
    #     "пердильни",
    #     "перднут",
    #     "перду",
    #     "пердуне",
    #     "пердунин",
    #     "пердунь",
    #     "пердух",
    #     "перд",
    #     "передо",
    #     "пернут",
    #     "пидо",
    #     "пизд",
    #     "пизданут",
    #     "пизденк",
    #     "пиздет",
    #     "пиздит",
    #     "пиздищ",
    #     "пиздобрати",
    #     "пиздоваты",
    #     "пиздорване",
    #     "пиздорванк",
    #     "пиздострадател",
    #     "пизду",
    #     "пиздюг",
    #     "пиздю",
    #     "пиздячит",
    #     "писят",
    #     "питишк",
    #     "плех",
    #     "подговнят",
    #     "подъебнутьс",
    #     "поебат",
    #     "поет",
    #     "попысат",
    #     "посрат",
    #     "поставит",
    #     "поцоваты",
    #     "презервати",
    #     "пробляд",
    #     "проебат",
    #     "промандет",
    #     "промудет",
    #     "пропиздет",
    #     "пропиздячит",
    #     "пысат",
    #     "разъеб",
    #     "разъеба",
    #     "распизда",
    #     "распиздетьс",
    #     "распиздя",
    #     "распроет",
    #     "растык",
    #     "сговнят",
    #     "секел",
    #     "серу",
    #     "серьк",
    #     "сик",
    #     "сикат",
    #     "сикел",
    #     "сират",
    #     "сирыват",
    #     "скурвитьс",
    #     "скурех",
    #     "скуре",
    #     "скуряг",
    #     "скуряжничат",
    #     "спиздит",
    #     "срак",
    #     "сраны",
    #     "срань",
    #     "срат",
    #     "сру",
    #     "ссак",
    #     "ссак",
    #     "ссат",
    #     "старпе",
    #     "стру",
    #     "суходрочк",
    #     "сцавинь",
    #     "сцак",
    #     "сцак",
    #     "сцани",
    #     "сцат",
    #     "сцих",
    #     "сцул",
    #     "сцых",
    #     "сыку",
    #     "титечк",
    #     "титечны",
    #     "титк",
    #     "титочк",
    #     "титьк",
    #     "трипе",
    #     "триппе",
    #     "ует",
    #     "усратьс",
    #     "усцатьс",
    #     "фи",
    #     "фу",
    #     "хезат",
    #     "хе",
    #     "херн",
    #     "херовин",
    #     "херовы",
    #     "хитрожопы",
    #     "хлюх",
    #     "хуевин",
    #     "хуевы",
    #     "хуе",
    #     "хуепромышленни",
    #     "хуери",
    #     "хуесо",
    #     "хуищ",
    #     "ху",
    #     "хуйн",
    #     "хуйри",
    #     "хуякат",
    #     "хуякнут",
    #     "целк",
    #     "шлюха",
    # ]

    def __str__(self):
        author_room = self.rc.name if self.rc else self.author_room
        author_name = self.user.get_FIO() if self.user else self.author_name
        return 'Отзыв - [%s], %s [%s]' % (author_name, author_room, self.hotel.name)

    def calc_overall_rating(self):
        self.overall_rating = round((self.location + self.price_quality_ratio +
                                     self.purity + self.food + self.service + self.number_quality) / 6, 1)
        self.save()

    def convert_value(type, value):
        hygiene_products = {
            "unused": {"text": "не пользовались", "number": 0},
            "bad": {"text": "плохой набор", "number": 5},
            "ok": {"text": "нормальный набор", "number": 7},
            "good": {"text": "отличный набор", "number": 10},
            "no": {"text": "не окалазось набора", "number": 0},
            "awful": {"text": "ужасный набор", "number": 2},
        }

        wifi_quality = {
            "unused": {"text": "не пользовались", "number": 0},
            "slow": {"text": "медленный", "number": 7},
            "perfect": {"text": "быстрый", "number": 10},
            "downtime": {"text": "с перебоями", "number": 5},
            "missing": {"text": "не было", "number": 0},
        }

        overall_rating = {
            0: {"text": "Хорошо", "number": 0},
            1: {"text": "Хорошо", "number": 1},
            2: {"text": "Хорошо", "number": 2},
            3: {"text": "Хорошо", "number": 3},
            4: {"text": "Хорошо", "number": 4},
            5: {"text": "Хорошо", "number": 5},
            6: {"text": "Хорошо", "number": 6},
            7: {"text": "Превосходно", "number": 7},
            8: {"text": "Превосходно", "number": 8},
            9: {"text": "Превосходно", "number": 9},
            10: {"text": "Великолепно", "number": 10},
        }

        r_hygiene_products = {
            "не пользовались": {"text": "unused", "number": 0},
            "плохой набор": {"text": "bad", "number": 5},
            "нормальный набор": {"text": "ok", "number": 7},
            "отличный набор": {"text": "good", "number": 10},
            "не окалазось набора": {"text": "no", "number": 0},
            "ужасный набор": {"text": "awful", "number": 2},
        }

        r_wifi_quality = {
            "не пользовались": {"text": "unused", "number": 0},
            "медленный": {"text": "slow", "number": 7},
            "быстрый": {"text": "perfect", "number": 10},
            "с перебоями": {"text": "downtime", "number": 5},
            "не было": {"text": "missing", "number": 0},
        }

        result = None

        if type == "hygiene":
            result = hygiene_products.get(value, {"text": "", "number": 0})

        if type == "wifi":
            result = wifi_quality.get(value, {"text": "", "number": 0})

        if type == "overall_rating":
            result = overall_rating.get(value, {"text": "", "number": 0})

        if type == "-hygiene":
            result = r_hygiene_products.get(value, {"text": "", "number": 0})

        if type == "-wifi":
            result = r_wifi_quality.get(value, {"text": "", "number": 0})

        return result

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

class GroupBooking(models.Model):
    bookings = models.ManyToManyField(
        "Booking", related_name="rservice", blank=True)


    class Meta:
        verbose_name = 'Группа бронирований'
        verbose_name_plural = 'Группы бронирований'

class BookingQuerySet(models.QuerySet):
    def is_deleted(self, action="disable"):
        if action == "toggle":
            new_value = models.F('is_delete') ^ True
        elif action == "enable":
            new_value = True
        elif action == "disable":
            new_value = False
        else:
            raise ValueError("Invalid action")

        self.update(is_delete=new_value)

    def change_payment_status(self, new_payment_status: str):
        self.payment_status = new_payment_status
        self.save()

class Booking(models.Model):
    objects = BookingQuerySet.as_manager()

    STATUS_CHOICES = [
        ('new', 'Новое'),  # 54d39c
        ('verified', 'Подтверждено'),  # 60C0FF
        ('settled', 'Заселен'),  # 54d39c
        ('left', 'Выехал'),  # B3BAC4
        ('cancelled', 'Отменен'),  # D34141
        ('close', 'Закрыт'),  # D34141
    ]

    PAYMENT_CHOICES = [
        ('not_paid', 'Не оплачено'),
        ('site_paid', 'Оплачено для сайта'),
        ('full_paid', 'Полная оплата'),
        ('site_refund', 'Возврат оплаты от сайта'),
        ('full_refund', 'Возврат полной оплаты'),
    ]

    id = models.CharField(max_length=20, unique=True, primary_key=True,
                          default=generate_booking_id, verbose_name='ID')
    booked_room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, related_name='rbooking', null=True, verbose_name='Номер')

    booking_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='ubooking', null=True, verbose_name='Заказчик')
    start_date_time = models.DateTimeField(verbose_name='Начала бронирования')
    end_date_time = models.DateTimeField(verbose_name='Окончания бронирования')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name='Статус')
    adults_count = models.SmallIntegerField(verbose_name='Кол-во взрослых')
    children_count = models.SmallIntegerField(verbose_name='Кол-во детей')
    children_ages = models.ManyToManyField(Child, related_name='ages_c_booking', blank=True, verbose_name='Возраст детей')
    companions = models.ManyToManyField(Companion, related_name='companions_booking', blank=True)
    hotel_price = models.PositiveIntegerField(
        verbose_name='Цена гостиницы (руб)')
    site_price = models.PositiveIntegerField(verbose_name='Цена сайта (руб)')
    comment = models.TextField(
        blank=True, null=True, verbose_name='Комментарии')
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, verbose_name='Статус оплаты')
    payment_for_accommodation = models.BooleanField(
        default=False, verbose_name='Оплата за проживание')
    is_stay_bonus = models.BooleanField(
        default=False, verbose_name='Получены - Бонусы за проживание')
    datetime_stay_bonus = models.DateTimeField(
        default=timezone.now, null=True, blank=True, verbose_name='Дата и время получения - Бонусы за проживание')
    is_review_bonus = models.BooleanField(
        default=False, verbose_name='Получены - Бонусы за отзыв')
    is_hotel_bonus = models.BooleanField(
        default=False, verbose_name='Получены - Бонусы за проживание для отеля')
    datetime_hotel_bonus = models.DateTimeField(
        default=timezone.now, null=True, blank=True, verbose_name='Дата и время получения - онусы за проживание для отеля')
    orderId = models.CharField(
        max_length=100, verbose_name='OrderId Сбера', null=True, blank=True)
    response_to_cancellation = models.BooleanField(
        verbose_name='Ответ на отмену', default=False, null=True, blank=True)
    hotel_cancellation = models.BooleanField(
        verbose_name='Отмена брони отелем', default=None, null=True, blank=True)
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name='Дата и время создания')
    is_delete = models.BooleanField(
        default=False, verbose_name='Флаг удаления')
    param = models.JSONField(default=dict, null=True, blank=True)

    def __str__(self):
        return '(%s) Брон - %s' % (self.id, self.get_status_display())

    def copy(self):
        # создаем глубокую копию текущего объекта модели
        copied_object = deepcopy(self)

        # сбрасываем идентификатор объекта
        copied_object.pk = None

        # сохраняем копию объекта модели
        copied_object.save()

        return copied_object

    def get_hotel(self) -> Hotel:
        if self.booked_room is not None and self.booked_room.category is not None:
            return self.booked_room.category.hotel
        return None

    def сancellation_of_the_reservation(self, user_type):
        if self.status == "cancelled":
            return Exception("Уже отменён")

        booking_user = self.booking_user

        # Автоотмена (Если не успел доплатить за бронь за 20 минут с карты)
        if user_type == "site":
            self.status = "cancelled"

            bonus_return = self.param["prices"]["bonus"]["value"]
            balanc_return = self.param["prices"]["balanc"]["value"]
            card_return = self.param["prices"]["card"]["value"]

            Bonus_rubles.add(booking_user, bonus_return)
            booking_user.rbal += balanc_return + card_return

            booking_user.save()

        if self.payment_status in ["site_paid", "full_paid"]:
            days_created_at = (self.created_at - timezone.now()).days
            days_booking = (self.start_date_time - timezone.now()).days

            bonus_return = self.param["prices"]["bonus"]["value"]
            balanc_return = self.param["prices"]["balanc"]["value"]
            card_return = self.param["prices"]["card"]["value"]

            if days_created_at < 1 and days_booking >= 3:
                Bonus_rubles.add(booking_user, bonus_return)
                return_rub_bookig(self, balanc_return+card_return)

            elif days_booking < 30:
                Bonus_rubles.add(booking_user, round(bonus_return * 0.5))
                return_rub_bookig(self, round(
                    (balanc_return+card_return) * 0.5))

            elif days_booking >= 30:
                Bonus_rubles.add(booking_user, bonus_return)
                return_rub_bookig(self, (balanc_return+card_return))

            if user_type == "hotel":
                self.hotel_cancellation = True

            if user_type == "client":
                self.hotel_cancellation = False

            self.status = "cancelled"
            self.save()
        else:
            return Exception("Не оплачено за бронь")

    def change_status(self, new_status: str):
        """
        Изменяет статус объекта на новый статус, переданный в качестве аргумента new_status.

        Аргументы:
        ----------
        new_status: str
            Новый статус объекта. Должен быть одним из значений из списка status_choices.

        Возвращаемое значение:
        ----------------------
        Метод не возвращает никакого значения.
        """
        if new_status == self.status:
            return Exception("Нельзя поменять статус на такой же статус")

        if new_status not in [choice[0] for choice in self.STATUS_CHOICES]:
            return Exception("Недопустимый статус")

        if self.status == "cancelled":
            return Exception("Невозможно изменить статус брони с отмененной")

        if self.status in ["verified", "settled", "left", "cancelled"] and new_status == "new":
            return self.status

        if self.status not in ["cancelled"] and new_status == "cancelled":
            if self.payment_status in ["site_paid", "full_paid"]:
                self.сancellation_of_the_reservation("hotel")

        if new_status == "left":
            if self.is_stay_bonus == False:
                add_bonus_user_booking_left(self)

            if self.is_hotel_bonus == False:
                add_bonus_hotel_booking_left(self)

        self.status = new_status
        self.save()
        return self.status

    def change_payment_status(self, new_payment_status: str):
        self.payment_status = new_payment_status
        self.save()

    def check_can_create(rc: RCategory, dates):
        """Проверка возможности создание брони.

        # Параметры

        - `rc`: объект класса RCategory, представляющий выбранную пользователем категорию номера
        - `user`: объект класса User, представляющий пользователя, который делает бронирование
        - `dates`: список из двух объектов datetime, представляющих начальную и конечную даты бронирования
        - `adult`: целое число, представляющее количество взрослых, останавливающихся в номере
        - `childre`: целое число, представляющее количество детей, останавливающихся в номере
        - `prices`: словарь, содержащий следующие ключи и значения:
            * "site" - целочисленное значение, представляющее цену сайта
            * "room_full" - целочисленное значение, представляющее полную стоимость номера
        - `add_info`: доп параметры которые записываются в бронь (Может быть сколько бонусов потратили на брони и сколько потратили реаль рублей из лк или с карты)
            ...

        # Возвращает

        bool - Возможно ли создать бронирование
        """

        hotel = rc.hotel

        rooms_category = Room.objects.filter(category=rc, is_delete=False)

        # конвертируем datetime.date в datetime.datetime
        start_datetime = datetime.datetime.combine(
            dates[0], hotel.check_in_time)
        end_datetime = datetime.datetime.combine(
            dates[1], hotel.departure_time)

        # создаем новый объект datetime.datetime на основе объекта datetime.combine
        dt_start = datetime.datetime(*start_datetime.timetuple()[:6])
        dt_end = datetime.datetime(*end_datetime.timetuple()[:6])

        # выбираем все бронирования для этих комнат, которые пересекаются с указанными датами
        fillter_booking = {
            "booked_room__in": rooms_category,
            "status__in": ["new", "verified", "settled", "close"],
            "start_date_time__lte": dt_end,
            "end_date_time__gte": dt_start,
        }
        booking_1 = Booking.objects.filter(
            **fillter_booking).values_list("booked_room__id", flat=True)

        # выбираем только те комнаты, которые не заняты на указанные даты
        available_rooms = rooms_category.exclude(id__in=list(booking_1))

        return len(available_rooms) > 0

    def new_check(rc: RCategory, user: User, dates, adult: int, age_c, use_bonus, add_info: dict = None) -> dict:
        """Этот метод предназначен для проверки вомзожности бронирования номеров в отеле на основе различных параметров.

        # Параметры

        - `rc`: объект класса RCategory, представляющий выбранную пользователем категорию номера
        - `user`: объект класса User, представляющий пользователя, который делает бронирование
        - `dates`: список из двух объектов datetime, представляющих начальную и конечную даты бронирования
        - `adult`: целое число, представляющее количество взрослых, останавливающихся в номере
        - `childre`: целое число, представляющее количество детей, останавливающихся в номере
        - `prices`: словарь, содержащий следующие ключи и значения:
            * "site" - целочисленное значение, представляющее цену сайта
            * "room_full" - целочисленное значение, представляющее полную стоимость номера
        - `add_info`: доп параметры которые записываются в бронь (Может быть сколько бонусов потратили на брони и сколько потратили реаль рублей из лк или с карты)
            ...

        # Возвращает

        Словарь, содержащий следующие ключи и значения:

        * "status" - "success" или "error"
        * "error" - либо строка с кодом ошибки, либо пустая строка
        * "booking" - Бронь
        * "chat_url" - Ссылка на чат

        # Список возможных ошибок

        * "no_empty_rooms" - если нет свободных номеров для бронирования
        """

        hotel = rc.hotel

        rooms_1 = Room.objects.filter(category=rc, is_delete=False)

        # конвертируем datetime.date в datetime.datetime
        dt_start_combine = datetime.datetime.combine(
            dates[0], hotel.check_in_time)
        dt_end_combine = datetime.datetime.combine(
            dates[1], hotel.departure_time)

        # создаем новый объект datetime.datetime
        dt_start = datetime.datetime(year=dt_start_combine.year, month=dt_start_combine.month, day=dt_start_combine.day,
                                     hour=dt_start_combine.hour, minute=dt_start_combine.minute, second=dt_start_combine.second)

        dt_end = datetime.datetime(year=dt_end_combine.year, month=dt_end_combine.month, day=dt_end_combine.day,
                                   hour=dt_end_combine.hour, minute=dt_end_combine.minute, second=dt_end_combine.second)

        # выбираем все бронирования для этих комнат, которые пересекаются с указанными датами
        fillter_booking = {
            "booked_room__in": rooms_1,
            "status__in": ["new", "verified", "settled", "close"],
            "start_date_time__lte": dt_end,
            "end_date_time__gte": dt_start,
        }
        booking_1 = Booking.objects.filter(
            **fillter_booking).values_list("booked_room__id", flat=True)

        # выбираем только те комнаты, которые не заняты на указанные даты
        rooms_2 = rooms_1.exclude(id__in=list(booking_1))

        if len(rooms_2) > 0:

            return {"status": "success", "error": ""}
        else:
            return {"status": "error", "error": "no_empty_rooms"}

    def new(rc: RCategory, user: User, dates, adult: int, age_c, use_bonus, add_info: dict = None) -> dict:
        """Этот метод предназначен для бронирования номеров в отеле на основе различных параметров.

        # Параметры

        - `rc`: объект класса RCategory, представляющий выбранную пользователем категорию номера
        - `user`: объект класса User, представляющий пользователя, который делает бронирование
        - `dates`: список из двух объектов datetime, представляющих начальную и конечную даты бронирования
        - `adult`: целое число, представляющее количество взрослых, останавливающихся в номере
        - `childre`: целое число, представляющее количество детей, останавливающихся в номере
        - `prices`: словарь, содержащий следующие ключи и значения:
            * "site" - целочисленное значение, представляющее цену сайта
            * "room_full" - целочисленное значение, представляющее полную стоимость номера
        - `add_info`: доп параметры которые записываются в бронь (Может быть сколько бонусов потратили на брони и сколько потратили реаль рублей из лк или с карты)
            ...

        # Возвращает

        Словарь, содержащий следующие ключи и значения:

        * "status" - "success" или "error"
        * "error" - либо строка с кодом ошибки, либо пустая строка
        * "booking" - Бронь
        * "chat_url" - Ссылка на чат

        # Список возможных ошибок

        * "no_empty_rooms" - если нет свободных номеров для бронирования
        """

        hotel = rc.hotel

        rooms_1 = Room.objects.filter(category=rc, is_delete=False)

        # конвертируем datetime.date в datetime.datetime
        dt_start_combine = datetime.datetime.combine(
            dates[0], hotel.check_in_time)
        dt_end_combine = datetime.datetime.combine(
            dates[1], hotel.departure_time)

        # создаем новый объект datetime.datetime
        dt_start = datetime.datetime(year=dt_start_combine.year, month=dt_start_combine.month, day=dt_start_combine.day,
                                     hour=dt_start_combine.hour, minute=dt_start_combine.minute, second=dt_start_combine.second)

        dt_end = datetime.datetime(year=dt_end_combine.year, month=dt_end_combine.month, day=dt_end_combine.day,
                                   hour=dt_end_combine.hour, minute=dt_end_combine.minute, second=dt_end_combine.second)

        # выбираем все бронирования для этих комнат, которые пересекаются с указанными датами
        fillter_booking = {
            "booked_room__in": rooms_1,
            "status__in": ["new", "verified", "settled", "close"],
            "start_date_time__lte": dt_end,
            "end_date_time__gte": dt_start,
        }
        booking_1 = Booking.objects.filter(
            **fillter_booking).values_list("booked_room__id", flat=True)

        # выбираем только те комнаты, которые не заняты на указанные даты
        rooms_2 = rooms_1.exclude(id__in=list(booking_1))

        if len(rooms_2) > 0:
            booking: Booking = Booking.objects.create(
                booked_room=rooms_2[0],
                booking_user=user,
                start_date_time=dt_start,
                end_date_time=dt_end,
                status="new",
                adults_count=adult,
                children_count=len(age_c),
                hotel_price=0,
                site_price=0,
                payment_status='not_paid',
                datetime_stay_bonus=None,
            )

            for age in age_c:
                child = Child.objects.create(
                    age=age,
                )
                booking.children_ages.add(child)

            booking.param["prepayment_for_the_room_before_checkin"] = rc.additional_info.get(
                "prepayment_for_the_room_before_checkin", 0)

            booking.save()

            if add_info != None:
                booking.param = add_info
                booking.save()

            if use_bonus:
                booking.is_stay_bonus = True

            return {"status": "success", "booking": booking, "error": ""}
        else:
            return {"status": "error", "error": "no_empty_rooms"}

    def get_free_room(rc: RCategory, date: datetime.datetime):
        """Метод для получения списка свободных номеров"""
        # Получить все бронирования на выбранную дату из модели Booking
        rooms = Room.objects.filter(category=rc,  is_delete=False)
        booking_filter = {
            "start_date_time__lte": date,
            "end_date_time__gte": date,
        }
        bookings = Booking.objects.filter(**booking_filter)
        # Сформировать список занятых номеров на эту дату
        occupied_rooms = [
            b.booked_room.id for b in bookings if b.booked_room != None]
        # Получить все номера категории RCategory из модели Room
        # Отфильтровать номера, которые присутствуют в списке занятых - это будут свободные номера
        free_rooms = [r for r in rooms if r.id not in occupied_rooms]
        # Вернуть полученный список свободных номеров
        return free_rooms

    def get_free_rooms(rc: RCategory, date_start: datetime.datetime, date_end: datetime.datetime):
        """Метод для получения списка свободных номеров"""
        # Получить все бронирования на выбранную дату из модели Booking
        rooms = Room.objects.filter(category=rc,  is_delete=False)
        booking_filter = {
            "start_date_time__lte": date_start,
            "end_date_time__gte": date_end,
        }
        bookings = Booking.objects.filter(**booking_filter)
        # Сформировать список занятых номеров на эту дату
        occupied_rooms = [
            b.booked_room.id for b in bookings if b.booked_room != None]
        # Получить все номера категории RCategory из модели Room
        # Отфильтровать номера, которые присутствуют в списке занятых - это будут свободные номера
        free_rooms = [r for r in rooms if r.id not in occupied_rooms]
        # Вернуть полученный список свободных номеров
        return free_rooms

    def calc_price(user: User, rc: RCategory, dates: List[Tuple[datetime.datetime, datetime.datetime]], add_price=0):
        """Метод вычисляет стоимость бронирования в отеле на основе различных параметров.

        # Параметры

        - `user`: объект User, представляющий пользователя, который делает бронирование
        - `rc`: объект RCategory, представляющий выбранную пользователем комнату
        - `dates`: список из двух объектов date, представляющих начальную и конечную даты бронирования

        # Возвращает

        Словарь, содержащий следующие ключи:

        - `site`: Цена, оплаченная сайтом
        - `hotel`: Дополнительная сумма, которую нужно заплатить отелю
        - `bonus`: Словарь, содержащий следующие ключи:
            - `init`: Количество бонусных баллов на изначальных
            - `now`: Количество бонусных баллов после вычета
            - `price`: Стоимость после использования бонусных баллов
            - `discount`: Сколько использовалось бонусов
        - `is_first_booking`: Булевое значение, указывающее, является ли это первым бронированием пользователя
        - `room_full`: Цена за все ночи в номере
        - `hotel_percentage`: Процент от отеля
        - `first_booking_discount`: Скидка первой брони в рублях
        - `cleaning`: Цена за уборку
        - `security_deposit`: Цена за уборку


        # Пример использования

        ```
        result = calc_price(user, rc, dates, use_bonus=True)
        ```
        """

        IS_USER_GUEST = not user.is_authenticated
        HOTEL = rc.hotel
        INIT_BONUS = 0

        now_bonus = 0
        is_first_booking = False

        if not IS_USER_GUEST:
            bonus_points_get = Bonus_rubles.get(user)
            INIT_BONUS = bonus_points_get["sum"]
            now_bonus = INIT_BONUS

        if not IS_USER_GUEST:
            is_first_booking = Booking.objects.filter(
                booking_user=user).count() == 0

        # Цена номера за все ночи
        price_per_night: int = PricePerDay.calculate_total_price(
            dates[0], dates[1], rc) + add_price

        cleaning = None
        try:
            cleaning = int(HOTEL.cleaning_fee)
            if cleaning <= 0:
                cleaning = None
        except:
            pass

        security_deposit = None
        try:
            security_deposit = int(rc.the_amount_of_the_security_deposit)
            if security_deposit <= 0:
                security_deposit = None
        except:
            pass

        # Цена сайта
        site_price: int = price_per_night * (HOTEL.percentage / 100)

        first_booking_discount = None

        # Цена отеля
        hotel_price = price_per_night - site_price

        if site_price != 0:
            # Скидка в 5% при первой брони
            if is_first_booking:
                first_booking_discount = round(price_per_night * 0.05)
                site_price -= first_booking_discount
        else:
            first_booking_discount = 0

        # Цена сайта после бонусов
        max_discount = int(site_price * 0.5)

        if now_bonus <= max_discount:
            discount = now_bonus
        else:
            discount = max_discount

        now_bonus -= discount
        site_price_with_bonus = site_price - discount

        if not isinstance(rc.additional_info, dict):
            rc.additional_info = {}
            rc.save()

        prepayment_for_the_room_before_checkin = round(
            price_per_night * (rc.additional_info.get("prepayment_for_the_room_before_checkin", 0) / 100))

        result_prices = {
            "site": int(site_price),
            "hotel": int(hotel_price),
            "bonus": {"init": int(INIT_BONUS), "now": int(now_bonus), "discount": int(discount), "price": int(site_price_with_bonus)},
            "is_first_booking": is_first_booking,
            "room_full": int(price_per_night),
            "hotel_percentage": HOTEL.percentage,
            "cost_of_accommodation": price_per_night - discount,
            "first_booking_discount": first_booking_discount,
            "cleaning": cleaning,
            "security_deposit": security_deposit,
            "prepayment_for_the_room_before_checkin": prepayment_for_the_room_before_checkin,
        }

        return result_prices

    def calc_price_v2(user: User, rc: RCategory, dates: List[Tuple[datetime.datetime, datetime.datetime]], add_price=0):
        """Метод вычисляет стоимость бронирования в отеле на основе различных параметров.

        # Параметры

        - `user`: объект User, представляющий пользователя, который делает бронирование
        - `rc`: объект RCategory, представляющий выбранную пользователем комнату
        - `dates`: список из двух объектов date, представляющих начальную и конечную даты бронирования

        # Возвращает

        Словарь, содержащий следующие ключи:

        - `site`: Цена, оплаченная сайтом
        - `hotel`: Дополнительная сумма, которую нужно заплатить отелю
        - `bonus`: Словарь, содержащий следующие ключи:
            - `init`: Количество бонусных баллов на изначальных
            - `now`: Количество бонусных баллов после вычета
            - `price`: Стоимость после использования бонусных баллов
            - `discount`: Сколько использовалось бонусов
        - `is_first_booking`: Булевое значение, указывающее, является ли это первым бронированием пользователя
        - `room_full`: Цена за все ночи в номере
        - `hotel_percentage`: Процент от отеля
        - `first_booking_discount`: Скидка первой брони в рублях
        - `cleaning`: Цена за уборку
        - `security_deposit`: Цена за уборку


        # Пример использования

        ```
        result = calc_price(user, rc, dates, use_bonus=True)
        ```
        """

        IS_USER_GUEST = not user.is_authenticated
        HOTEL = rc.hotel
        INIT_BONUS = 0

        now_bonus = 0
        is_first_booking = False

        if not IS_USER_GUEST:
            bonus_points_get = Bonus_rubles.get(user)
            INIT_BONUS = bonus_points_get["sum"]
            now_bonus = INIT_BONUS

        if not IS_USER_GUEST:
            is_first_booking = Booking.objects.filter(
                booking_user=user).count() == 0

        # Цена номера за все ночи
        price_per_night: int = PricePerDay.calculate_total_price_v2(
            dates[0], dates[1], rc) + add_price

        cleaning = None
        try:
            cleaning = int(HOTEL.cleaning_fee)
            if cleaning <= 0:
                cleaning = None
        except:
            pass

        security_deposit = None
        try:
            security_deposit = int(rc.the_amount_of_the_security_deposit)
            if security_deposit <= 0:
                security_deposit = None
        except:
            pass

        # Цена сайта
        site_price: int = price_per_night * (HOTEL.percentage / 100)

        first_booking_discount = None

        # Цена отеля
        hotel_price = price_per_night - site_price

        if site_price != 0:
            # Скидка в 5% при первой брони
            if is_first_booking:
                first_booking_discount = round(price_per_night * 0.05)
                site_price -= first_booking_discount
        else:
            first_booking_discount = 0

        # Цена сайта после бонусов
        max_discount = int(site_price * 0.5)

        if now_bonus <= max_discount:
            discount = now_bonus
        else:
            discount = max_discount

        now_bonus -= discount
        site_price_with_bonus = site_price - discount

        if not isinstance(rc.additional_info, dict):
            rc.additional_info = {}
            rc.save()

        prepayment_for_the_room_before_checkin = round(
            price_per_night * (rc.additional_info.get("prepayment_for_the_room_before_checkin", 0) / 100))

        result_prices = {
            "site": int(site_price),
            "hotel": int(hotel_price),
            "bonus": {"init": int(INIT_BONUS), "now": int(now_bonus), "discount": int(discount), "price": int(site_price_with_bonus)},
            "is_first_booking": is_first_booking,
            "room_full": int(price_per_night),
            "hotel_percentage": HOTEL.percentage,
            "cost_of_accommodation": price_per_night - discount,
            "first_booking_discount": first_booking_discount,
            "cleaning": cleaning,
            "security_deposit": security_deposit,
            "prepayment_for_the_room_before_checkin": prepayment_for_the_room_before_checkin,
        }

        return result_prices

    class Meta:
        verbose_name = 'Брон'
        verbose_name_plural = 'Брони'

def file_path(instance, filename):
    letters = string.ascii_letters + "0123456789"
    rand_string = ''.join(random.choice(letters) for i in range(10))
    name = rand_string + path.splitext(filename)[1]
    return 'file/{0}'.format(name)

class HBoost(models.Model):
    hotel = models.ForeignKey(
        Hotel, on_delete=models.CASCADE, related_name="hotel_boost")
    super = models.BooleanField()  # Буст за балы|реальные денги => false|true
    date = models.DateTimeField()

    class Meta:
        verbose_name = 'Буст отеля'
        verbose_name_plural = 'Бусты отеля'

    def get_value_boost(hotel):
        """
        Метод get_value_boost(hotel) принимает объект отеля и возвращает количество времени буста отеля. Этот метод используется для получения значения буста для отеля в определенный момент времени.

        # Параметры метода

        Метод принимает один параметр:

        - `hotel` - объект отеля (Hotel)

        # Возвращаемое значение

        Метод возвращает кортеж из двух значений:

        - `boost_common` - количество времени буста отеля (int)
        - `boost_super` - количество супер бустов отеля (int)
        """
        current_time = datetime.datetime.now(datetime.timezone.utc)
        boost_super = 0
        boost_common = 0
        hb_super_s = HBoost.objects.filter(
            super=True, hotel=hotel, date__gt=current_time)
        boost_super = hb_super_s.count()

        hb_common = HBoost.objects.filter(
            super=False, hotel=hotel, date__gt=current_time).order_by("-date").first()
        if hb_common != None:
            boost_common = (hb_common.date - current_time).seconds
        else:
            boost_common = 0

        return boost_common, boost_super

class ModerWork(models.Model):
    hotels = models.ManyToManyField(
        Hotel, related_name='moderworks', verbose_name='Отели')
    user = models.ForeignKey(User, on_delete=models.SET_NULL,
                             related_name='moderwork', null=True, verbose_name='Пользователь')
    moder = models.ForeignKey(User, on_delete=models.SET_NULL,
                              related_name='moderworks', null=True, verbose_name='Модератор')
    contacts = models.JSONField(
        default=dict, blank=True, verbose_name='Контактные данные')
    notes = models.JSONField(default=dict, blank=True,
                             verbose_name='Коментарии')
    reminders = models.JSONField(
        default=dict, blank=True, verbose_name='Напоминания')
    status = models.JSONField(default=dict, blank=True, verbose_name='Статусы')
    param = models.JSONField(default=dict, blank=True,
                             verbose_name='Параметры')

    def str_json(self, indent=None):
        obj = model_to_dict(self)
        obj["hotels"] = [str(hotel) for hotel in obj["hotels"]]
        obj_json = json.dumps(obj, ensure_ascii=False, indent=indent)
        return obj_json

    @staticmethod
    def contacts_pattern(name=None, value=None):
        return {
            "date": datetime.datetime.now().timestamp(),
            "name": name,
            "value": value,
            "status": "active"
        }

    @staticmethod
    def notes_pattern(value=None):
        return {
            "date": datetime.datetime.now().timestamp(),
            "value": value,
            "status": "active"
        }

    @staticmethod
    def reminders_pattern(value=None):
        return {
            "date": datetime.datetime.now().timestamp(),
            "value": value,
            "status": "active"
        }

    @staticmethod
    def status_pattern(value=None):
        return {
            "date": datetime.datetime.now().timestamp(),
            "value": value,
        }