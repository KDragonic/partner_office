import datetime
import json
import os
import random
import string
from io import BytesIO
import time
from typing import List, Tuple

from PIL import Image
from os import path
from django.db import models
from django.utils import timezone

from brontur.funs import *
from user.models import User
from hotel.models import Booking, Hotel, HService
from django.forms.models import model_to_dict
from django.db.models import Q, QuerySet, Prefetch
from django.core.signing import Signer, BadSignature


class Partner(models.Model):
    owner = models.OneToOneField(User, blank=True, null=True, on_delete=models.CASCADE, related_name="partner", verbose_name='Пользователь')

    # Кто пригласив из парнеров партнёра
    invited_by = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='partners', verbose_name='Пригласивший партнер')
    api_key = models.CharField(max_length=255, verbose_name='API ключ')  # Название

    # Флаги
    enable = models.BooleanField(default=True, verbose_name='Включен')
    is_delete = models.BooleanField(default=False, verbose_name='Флаг удаления')

    # Дата и время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Дополнителные параметры
    option = models.JSONField(default=dict, blank=True,
                              verbose_name='параметры')

    def __str__(self):
        return '[Партнер] %s (%s)' % (self.owner.get_FIO(), self.enable)

    @staticmethod
    def decrypt_belongpartner(cookie_value):
        signer = Signer()
        obj = signer.unsign_object(cookie_value)
        return obj

    @staticmethod
    def link_user_to_partner(request):
        """
        Если пользователь авторезован и имеет [Cookie] "belongpartner" этот пользователь будет привязан парнёру один раз, повторно нечего не произойдёт
        """

        if not request.user.is_authenticated:
            return False

        user : User = request.user

        # Расшифровка "belongpartner" cookie
        decrypted_data = Partner.decrypt_belongpartner(request.COOKIES.get('belongpartner'))

        # Получение данных из расшифрованного объекта
        partner_id = decrypted_data.get('p')

        # Если не удалось найти парнёра
        partner = Partner.objects.filter(id=partner_id).first()
        if not partner:
            return False


        # Связанть двух стороней связу клиента и партнёра
        partner.option.get("linked_user", {})
        # Если клиент уже находится в списке звазаных клиентов то заменить его данные.
        # Это нужно чтобы дубликатов если он например через виджет сначало потом регестрация и потом через промокод
        # Двух связный нужен чтоб потом удалить из другова парнёра связаного клиента если его собрал другой парнёр
        partner.option["linked_user"][user.id] = {
            "id": user.id,
            # Тут хранится { "p": 1, "type": "widget", "key": "zStAl4S5Zb" } то есть по type и key можно понять
            # откуда пришёл пользователь, и если он использовал после виджета ещё что то например промокод от этого
            # же парнёра то запись с виджета удалится и поменяется на промокод, нужно же это чтоб правильно сделать
            # статистику или иначе будет запись что и виджет и промокод принесли доход.
            "param": decrypted_data,
            "status": "normal",
            "created_at": int(time.time()), # Нужно чтобы определить когда клиент был связан с парнёром
        }
        partner.save()


        # Тут проверяется есть ли уже ссылка на парнёра
        if user.additional_info.get("linked_partner"):
            #Если есть то проверит это ссылка на того же парнёра
            if user.additional_info["linked_partner"] == partner.id:
                # Если да то нечего для клиента не делать, нужные данные уже установлены
                return True
            else:
                # Если это другой парнёр то:
                other_partner = Partner.objects.filter(id=user.additional_info["linked_partner"]).first()
                if other_partner:
                    # Если парнёр есть то ставится значение что клиент от него ушёл (Который уже зарегерирован)

                    # NOTE Потом нужно будет написать польный список всех состояний, скорей всего будут ещё состояния
                    # такие как пользователь удалён, время истекло (Если зарегестрировался, но не забронировал).
                    other_partner.option["linked_user"][user.id]["status"] = "gone"
                    other_partner.save()

                return True
        else:
            # Если у пользователя нет ещё ссылки на парнёра (То есть это новый пользователь)
            user.additional_info["linked_partner"] = partner.id

        user.save()

        return True


    class Meta:
        verbose_name = 'Партнер'
        verbose_name_plural = 'Партнер'

class Channel(models.Model):
    # Множества ссылок нужно для того чтоб он отправлял эти ссылки на в разные места и понимал
    partner = models.ForeignKey(Partner, blank=True, null=True, on_delete=models.CASCADE, related_name="channels", verbose_name='Партнер')
    name = models.CharField(max_length=255, verbose_name='Название')  # Название
    url = models.CharField(max_length=255, verbose_name='URL')

    # Флаги
    enable = models.BooleanField(default=True, verbose_name='Включен')
    is_delete = models.BooleanField(default=False, verbose_name='Флаг удаления')

    # Дата и время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Дополнителные параметры
    option = models.JSONField(default=dict, blank=True, verbose_name='Параметры')


    def get_absolute_url(self):
        return reverse("model_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"[Канал] {self.name} от {self.partner.owner.get_FIO()} ({self.partner.id})"

    class Meta:
        verbose_name = 'Канал продаж'
        verbose_name_plural = 'Каналы продаж'


class PromoCode(models.Model):
    CONDITIONS_OPTIONS = { "hotel_type": { "show": True, "label": "Тип объекта размещения", "help": f"<b>Возможные значения:</b> {', '.join(sorted([hotel_type_label for hotel_type_code, hotel_type_label in Hotel.type_hotel_choices]))}", "methods": ["==", "in"], }, "days_of_stay": { "show": True, "label": "Дней   проживания", "help": "<b>Возможные значения:</b> Любое положительное число от 0", "methods": ["==", ">", "<", "range", "in"], }, "check_in_date": { "show": True, "label": "Дата заезда", "help": "<b>Возможные значения:</b> Дата в формате дд.мм.гггг", "methods": ["==", ">", "<", "range", "in"], }, "check_out_date": { "show": True, "label": "Дата выезда", "help": "<b>Возможные значения:</b> Дата в формате дд.мм.гггг", "methods": ["==", ">", "<", "range", "in"], }, "room_size": { "show": True, "label": "Размер комнаты", "help": "<b>Возможные значения:</b> Любое положительное число от 0", "methods": ["==", ">", "<", "range", "in"], }, "price_per_night": { "show": True, "label": "Цена за ночь", "help": "<b>Возможные значения:</b> Любое положительное число от 0", "methods": ["==", ">", "<", "range", "in"], }, "amenities": { "show": True, "label": "Удобства", "help": f"<b>Возможные значения:</b>", "methods": ["==", "in"], }, "rating": { "show": True, "label": "Рейтинг", "help": "<b>Возможные значения:</b> Любое положительное число от 0 до 5", "methods": ["==", ">", "<", "range", "in"], }, "location": { "show": True, "label": "Местоположение", "help": "<b>Возможные значения:</b> Город или страна", "methods": ["==", "in"], }, "discount_percent": { "show": True, "label": "Процент скидки", "help": "<b>Возможные значения:</b> Любое положительное число от 0 до 100", "methods": ["==", ">", "<", "range", "in"], } }

    partner = models.ForeignKey(Partner, blank=True, null=True, on_delete=models.CASCADE,related_name="promocedes", verbose_name='Партнер')
    channel = models.ForeignKey(Channel, blank=True, null=True, on_delete=models.CASCADE,related_name="promocedes", verbose_name='Канал')

    # Системные
    name = models.CharField(max_length=255, verbose_name='Название')  # Название
    description = models.TextField(verbose_name='Описание')  # Описание
    hotel_type = models.CharField(max_length=255, verbose_name='Название')  # Тип обекта размещения
    cashback = models.FloatField(verbose_name='Кешбек')  # Кешбек
    code = models.CharField(max_length=255, verbose_name='Промокод')  # Промокод
    promo_code_term = models.DateField(null=True, blank=True, verbose_name='Срок промокода')  # Срок промокода



    # Флаги
    enable = models.BooleanField(default=True, verbose_name='Включен')
    is_delete = models.BooleanField(default=False, verbose_name='Флаг удаления')

    # Дата и время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Дополнителные параметры
    option = models.JSONField(default=dict, blank=True,
                              verbose_name='Параметры')

    def __str__(self):
        return f"[Промокод] {self.code} - '{self.name}' от {self.partner.owner.get_FIO()} ({self.partner.id})"

    def add_usage(self, user: User, booking: Booking, datetime: datetime.datetime):
        """
        Метод `add_usage` используется для добавления информации об использовании промокода.
        ### Параметры:

        - `user`: Пользователь, который использует промокод.
        - `booking`: Бронирование, для которого используется промокод.
        - `datetime`: Дата и время использования промокода.

        ### Описание:

        Метод получает текущие параметры промокода из поля `options`. Затем добавляет информацию об использовании промокода в параметры.

        ### Пример использования:
        ```
        PromoCode.objects.get(code='PROMO').add_usage(user, booking, datetime)

        ======================================================================

        promocode = PromoCode.objects.get(code='PROMOCODE')
        promocode.add_usage(user, booking, datetime)

        ======================================================================

        promocode = PromoCode.objects.get(code=`Код промокода`)
        current_booking = Booking.objects.get(id=`ID брони`)
        current_datetime = datetime.fromtimestamp(`Время`)

        promocode.add_usage(request.user, current_booking, current_datetime)
        ```
        """

        # Добавить информацию об использовании в параметры
        usage_info = {'user': user.id,
                      'booking': booking.id, 'datetime': str(datetime)}
        self.options.setdefault('usages', []).append(usage_info)

        # Сохранить обновленные параметры
        self.save()

    def add_condition(self, conditions_new: dict[str, dict]):
        """
        Метод `add_condition` используется для добавления условий применения промокода.

        ### Параметры:
        - `conditions`: Условие применения промокода.

        ### Описание:
        Метод получает текущие параметры промокода из поля `options` и добавляет условие применения промокода в параметры.

        ### Пример использования:

        ```python
        promocode = PromoCode.objects.get(code='PROMO')
        promocode.add_condition(conditions)
        ```
        """

        conditions: dict[str, list] = {}

        for contition_key, contition_obj in conditions_new.items():
            if contition_key not in conditions:
                conditions[contition_key] = []

            conditions[contition_key].append(contition_obj)

        self.option["conditions"] = conditions
        self.save()

    @staticmethod
    def generate_promocode_code(length=8):
        adjectives = ['Great', 'Amazing', 'Awesome', 'Excellent', 'Wonderful']
        nouns = ['Hotel', 'Resort', 'Stay', 'Vacation', 'Trip']
        promo_code = random.choice(adjectives) + random.choice(nouns) + str(random.randint(10, 99))
        return promo_code

    def generate_promo_code_object():
        # Генерация случайных значений для полей модели
        partner = random.choice(Partner.objects.all())  # Случайный партнер из базы данных

        # Генерация случайного осмысленного названия и описания на русском языке
        name = random.choice( ['Великолепный', 'Удивительный', 'Превосходный', 'Изумительный', 'Замечательный']) + ' ' + random.choice(['Отель', 'Курорт', 'Гостиница', 'Пансионат', 'Усадьба'])
        description = 'Приятный отдых в нашем ' + name

        # Получение случайного типа объекта размещения из списка допустимых значений
        hotel_type = random.choice(Hotel.type_hotel_choices)[0]

        cashback = random.uniform(0, 100)  # Случайный кешбек от 0 до 100
        code = PromoCode.generate_promocode_code()  # Случайный промокод
        promo_code_term = random.choice([None, '2022-01-01', '2022-02-01'])  # Случайный срок промокода

        channel = random.choice(Channel.objects.all())  # Случайный канал продаж из базы данных

        promo_code = PromoCode.objects.create(
            partner=partner,
            name=name,
            description=description,
            hotel_type=hotel_type,
            cashback=cashback,
            code=code,
            promo_code_term=promo_code_term,
            channel=channel,
        )


    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокод'

class PartnerLink(models.Model):
    # Множества ссылок нужно для того чтоб он отправлял эти ссылки на в разные места и понимал
    partner = models.ForeignKey(Partner, blank=True, null=True, on_delete=models.CASCADE, related_name="links", verbose_name='Партнер')
    name = models.CharField(max_length=255, verbose_name='Название')  # Название
    code = models.CharField(max_length=30, verbose_name='Код')  # Случайный код из букв и цифр, нужен будет для того чтоб определить что имено по этой ссылке перешли

    # Флаги
    enable = models.BooleanField(default=True, verbose_name='Включен')
    is_delete = models.BooleanField(default=False, verbose_name='Флаг удаления')

    # Дата и время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Дополнителные параметры
    option = models.JSONField(default=dict, blank=True, verbose_name='Параметры')


    def get_absolute_url(self):
        return reverse("model_detail", kwargs={"pk": self.pk})


    class Meta:
        verbose_name = 'Партнерская ссылка'
        verbose_name_plural = 'Партнерские ссылки'

class Referral(models.Model):
    # Множества ссылок нужно для того чтоб он отправлял эти ссылки на в разные места и понимал
    partner = models.ForeignKey(Partner, blank=True, null=True, on_delete=models.CASCADE, related_name="referrals", verbose_name='Партнер')
    name = models.CharField(max_length=255, verbose_name='Название')  # Название
    code = models.CharField(max_length=30, verbose_name='Код')  # Случайный код из букв и цифр, нужен будет для того чтоб определить что имено по этой ссылке перешли


    # Дата и время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Дополнителные параметры
    option = models.JSONField(default=dict, blank=True, verbose_name='Параметры')

    class Meta:
        verbose_name = 'Рефарал'
        verbose_name_plural = 'Рефералы'


class Widget(models.Model):
    partner = models.ForeignKey(Partner, blank=True, null=True, on_delete=models.CASCADE, related_name="widgets", verbose_name='Партнер')

    # Флаги
    enable = models.BooleanField(default=True, verbose_name='Включен')
    is_delete = models.BooleanField(default=False, verbose_name='Флаг удаления')

    # Дата и время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Дополнителные параметры
    option = models.JSONField(default=dict, blank=True, verbose_name='Параметры')

    class Meta:
        verbose_name = 'Виджет'
        verbose_name_plural = 'Виджеты'


class Banner(models.Model):
    partner = models.ForeignKey(Partner, blank=True, null=True, on_delete=models.CASCADE, related_name="banners", verbose_name='Партнер')

    # Флаги
    enable = models.BooleanField(default=True, verbose_name='Включен')
    is_delete = models.BooleanField(default=False, verbose_name='Флаг удаления')

    # Дата и время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Дополнителные параметры
    option = models.JSONField(default=dict, blank=True, verbose_name='Параметры')

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'