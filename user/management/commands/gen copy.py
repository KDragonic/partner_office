from datetime import timedelta
from datetime import datetime as DT
import os
from django.core.files import File
import urllib.request
import random
from django.core.management.base import BaseCommand
from hotel.models import Address, HImg, RImg, RService, HService, Hotel, Room, Booking, RCategory
from user.models import User

list_service_room = [
    "VIP-удобства в номере",
    "Кабельное телевидение",
    "Люкс для новобрачных",
    "Музыкальный центр",
    "Номера для аллергиков",
    "Номера для курящих",
    "Номера для некурящих",
    "Обслуживание номеров",
    "Сейф (в номере)",
    "Семейные номера",
    "Телевизор",
    "Холодильник",
    "Москитная сетка",
    "Номера со звукоизоляцией",
    "Мини-бар",
    "Туалетные принадлежности",
    "Халат",
    "Запирающийся шкафчик",
    "DVD-плеер",
    "Пресс для брюк",
]

list_service_hotel = {
    "Общее": [
        "Дизайн-отель",
        "Индивидуальная регистрация заезда и отъезда",
        "Компьютер",
        "Кондиционер",
        "Круглосуточная стойка регистрации",
        "Лифт",
        "Огнетушитель",
        "Отель для некурящих",
        "Отопление",
        "Поздняя регистрация выезда",
        "Посудомоечная машина",
        "Ранняя регистрация заезда",
        "Стиральная машина",
        "Ускоренная регистрация заезда и выезда",
        "Банкомат",
        "Охрана",
        "Работают лифты для доступа к верхним этажам",
        "Сувенирный магазин",
        "Телевизор в лобби",
        "Места для курения",
        "Ускоренная регистрация заезда",
        "Пресса",
        "Банк",
        "Мебель на улице",
        "Обмен валюты",
        "Продажа билетов",
        "Терраса",
        "Отсутствие лифтов",
        "Сад",
        "Сушилка",
        "Только для взрослых",
        "Курение запрещено на всей территории",
        "Аптека",
        "Винодельческое хозяйство",
        "Дворецкий",
        "Курение разрешено",
        "Магазины",
        "Патио",
        "Часовня",
        "Ускоренная регистрация выезда",
    ],
    "Услуги и удобства": [
        "Гладильные принадлежности",
        "Гладильные услугиоплачивается отдельно",
        "Прачечнаяоплачивается отдельно",
        "Телефон",
        "Услуги консьержа",
        "Утюг",
        "Фен (по запросу)",
        "Химчисткаоплачивается отдельно",
        "Хранение багажа",
        "Чистка обувиоплачивается отдельно",
    ],
    "Питание": [
        "Бесплатный чай/кофе",
        "Возможен полный пансион",
        "Возможен полупансион",
        "Завтрак в номер",
        "Кухня",
        "Микроволновая печь",
        "Ресторан",
        "Бар",
        "Завтрак",
        "Диетическое меню (по запросу)",
        "Упакованные ланчи",
        "Кафе",
        "Ресторан («шведский стол»)",
        "Снэк-бар",
        "Общая кухня",
        "Торговый автомат с закусками/напитками",
    ],

    "Интернет": [
        "Бесплатный Wi-Fi",
        "Бесплатный доступ в интернет",
        "Доступ в интернет",
        "Wi-Fi",
    ],

    "Трансфер": [
        "Трансфероплачивается отдельно",
        "Трансфер от аэропорта",
        "Прокат автомобилейоплачивается отдельно",
    ],

    "Персонал говорит": [
        "на английском",
        "на русском",
        "на испанском",
        "на итальянском",
        "на немецком",
    ],

    "Развлечения": [
        "Подходит для проведения праздничных мероприятий",
        "Пеший туризм",
        "Прокат велосипедов",
        "Развлекательные мероприятия",
        "Терраса для загара",
        "Бесплатный прокат велосипедов",
        "Библиотека",
        "Ночной клуб",
        "Каток",
        "Площадка для барбекю",
        "Удобства для барбекю",
    ],

    "Парковка": [
        "Парковкаоплачивается отдельно",
        "Парковка отсутствует",
        "Парковка (по запросу)",
        "Парковка рядом с отелем",
        "Бесплатная парковка",
        "Парковка",
        "Бесплатная парковка рядом с отелем",
    ],

    "Бизнес": [
        "Конференц-зал",
        "Ксерокс",
        "Организация встреч и банкетов",
        "Прокат видео- и компьютерной техники",
        "Бизнес-центр",
        "Факс и ксерокс",
    ],

    "Спорт": [
        "Тренажерный зал",
        "Настольный теннис",
        "Фитнес-центр",
        "Виндсерфинг",
        "Йога",
        "Катание на велосипеде",
        "Плавание на лодках",
    ],

    "Красота и здоровье": [
        "Аптечка первой помощи",
        "Массажоплачивается отдельно",
        "Салон красотыоплачивается отдельно",
        "Хаммам",
        "Сауна",
        "Баня",
        "Паровая баня",
        "Дежурный врач",
        "Оздоровительный клуб",
        "Солярийоплачивается отдельно",
        "Спа-центроплачивается отдельно",
    ],
    "Дети": [
        "Детские телеканалы",
        "Размещение подходит для семей/детей",
        "Услуги няни и уход за детьми",
        "Детская игровая площадка",
    ],
    "Животные": [
        "Размещение с домашними животными оплачивается отдельно",
        "Размещение с домашними животными не допускается",
        "Размещение с домашними животными",
    ],
    "Санитарные меры": [
        "Индивидуальные средства защиты для гостей",
        "Индивидуальные средства защиты для персонала",
        "Температурный контроль для гостей",
        "Температурный контроль для персонала",
        "Усиленные меры дезинфекции",
        "Бесконтактная регистрация заезда и/или выезда",
        "Питание в индивидуальной упаковке",
    ]
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('type', type=str)
        parser.add_argument('count', type=int)

    def handle(self, *args, **kwargs):
        type = kwargs["type"]
        count = kwargs["count"]
        print(f"type: {type}, count: {count}")
        if type == "rc":
            genRCategory(count)
        if type == "user":
            genUser(count)
        if type == "hotel":
            genHotel(count)
        if type == "room":
            genRoom(count)
        if type == "services":
            getRService()


def getRService():
    for service_room in list_service_room:
            obj = RService.objects.create(
                name=service_room
            )
            obj.save()

    for category in list_service_hotel:
        for item in list_service_hotel[category]:
            obj = HService.objects.create(
                section=category,
                name=item
            )
            obj.save()



img_scrs = [
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTQgUrg7INdhGlg7LRdw5UhV3BSZ0HgiOB3tQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS9D6ZMLxkDuAZxbMLoeu1fXlq4uBw7_XmbOw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQC8utu47tDHZm7rQ0PVh1i64DYAvRYash8vw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTovSXR9dYdE354d1q9oSs6RbC4b-JwsHNaeg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSFmwLR2rr551pgFx-by0qAdLHXdGLDVB3Mcg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRzfOpqngt4eJDqKFzHTTE3Fs3VbH6wfbbnnA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6gGaduiRNtuqtslyHn3Wc5XSvwYQ7L7Zv6g&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgNW5pjgGXe98Q_ghXdi3etrp0eRBqYa_SGQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSPKgySuCVCmyNvOdzDOEmyAryV-CQWO6A0Iw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQylS7_vbzbRCmdQo3DB_j8YoMH8Hf0JWgD8w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTJoBOws3bDcbYcdz5poza0yOutGRITFvpVOA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQOleyzmg8plawxY85tvD_L6K5_hZMPIEy88w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSUOuNgCeSY4Hp7wKtJweRr8AbnZppKmMwCAQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQHWwGvufVN4PBe0yqrakT_JZDGAMWNxfwb7A&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTugNZNJ2cVWsUGfVB89yO2i8epGeYP5qhRkw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRMaQha2roxLxE7xQq0-YqyZtW2AYaxmVOIYQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXkuw5jlcGRbm_bg1-LV3QW-OG17X9xiIPFQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRqi55svv1_VHB2Trqvz8MPcSt0WVTb0zG8iQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQpz6YS0YmJzwsBgDVWQmFBwv-179MH5xwsjg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQy9ztCeT3KM9jqoZAHns22fNFCgDuGEquxZw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQVJF2Xl6G2UenT3S48bRhddafLjtFQ_2ZHqA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ6r8l4rwe0OH4WZXLqqc-hgzImM13j-NAbXQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQkbrez9yEYZFOKkccTP-yjTx_lgdaCXLP7fg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRUMEdaBYtHa68J3zXJLgXso6Rsf_1d8jWvbg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ2BnUcmqkIIyNYz7aILCgbCfnw79Y0AHl9SQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTlEBfetRtgEkNPACUN2n3vU-p6TAOzAiKEfw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_NRsrvj1N7cN0Jt172w4bCtresdYbqLEtaw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRbgxcWwmMmSLmc4jcSi15lyGWhJt_o6uzE9w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQLexjCpFm9W9J3NcAZgVl32m_s5vru3su0Pg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTs5-RtzMz1LpvLzXXAE6w-dPjQ78cmtURemw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQoVvNmBugAxojtjORMHTbe3MIN4GQX02mZ3A&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTs5l2VBSPYoENW-mS2gJhi6u8h1wBl2Jwekw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRGov-Ay6gNhkNZY_MR9RIIUwgBAmUcfL2v6w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRxmGr_GprVWpE4CiqWE5w_TspnH7csA_Kdw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRleAIK5x_Y5nsZ01pstfBCiyuH8NAL7lcF2A&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTmPkl9qDJAdZh3jnqkFpBMqPG3DuAucuLuYQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSxL_qu2aQ5nFlcrOlSjYqitV0ijJLVgUb8Ig&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQyQ87efOm-dRrC5_wXu9poSGIxPke3IRvosQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSwgzADf9PLDBg1cmv7QFzlHgIRElRWSd6OEA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQiWagpehHCuS4eHD7Y8bJdJqzi7dNMu5DKMg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6HOmkzdWjbmVSSYTP6NZnY6br0DQs5yVAgA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQLL0wR0gTVbk11RY7hHzkfRExM1JZsA6j4rg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRFJOfWXPDZVUg8Ast2bKCNt9jEk9tjuWUlBQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRY6R4_qSVOz6XpNpTVOkAuYnEpKTPrugmrXA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ1F_mdyxV05d5J_z4qt0UP0dX5G5gmwNVYzQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTYQcYoh7sqDN2HqbA-ye4jPCS-5-EwMWXNpw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRZrMNcB8M4Mmo1AqkW3LxHQwP33CMqUTnUEw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRqYlagdysYKjoIlO8ayhXr3YhTc8b1Gtc3Kg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQiVhZRw-rr54L6qu85gDuL8kMQCnt-WkTHw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRNUPzu9LPuyqdJ5TvvUwKuDQBw5Jjiz5I4kw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSyS6KrQy4lZ7M6kzUIBUCncmcBVi4FCL6aGg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS3C0kBosVrApsH6S7z1mD_vYNUaYiWECPKNA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR3F4laLSdM6Lju6CtAj_xQuptoubxqUeo1DA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR1pNihQ0dF3Nnc51m9GGi9AMgyl1N6ETYtlQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS0IvTePHYNQMFyxC-eV2noD0RI0doCNe3GIg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS6Z0oi19sXg9qgivtT8bJa1mLNvtUBHKjYUw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-GNsCuZNLHNbzKfLeIyYzIQ8J_GCNOc4eQw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRdHyqr-5dco5kWIDEad7J6WGJQiVC3mqdLqw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgZeT__TKPqKO0kP5F3TF5FpyAOlG7qYp7TQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSNyFPn0Ek-s6GNQQtEHoTWqqrAsA7IvF3kTA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ46kY2OpfM4Xt_3qiFvLFPSod8iKX9k3Ki_Q&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSbRgxaV2j8mQoTpMSkvEVuJLjDlXHv7Co8dw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ4bQ4y5-wcPB81HScWQNkqEAN066gg0JXawQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTCq9BBtvkjgClpH9WRQXeXNevEJL2x-Nv7cQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR4Ykwzp2OePjaTHWlbvpAiTvoLlp6VMyx4fA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcThTyfebtppRNdsdk_eTiAgfL9WjXj81f8Mbw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSB4MljloA3g8e3a-OTJvgIOeXJmQPSCkKV7w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRDlIhYPM_jSrYCi_NFOzTGKRQtCPzyUp1TVg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTryH0IWkUz8FABWgXoJWrq7aT6_J6FCTDyCA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR323TqDgbQgUvHCfc-qUorFy5fpo-EdpWDtg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSwuWo5LBrwrdFSMjeBDIcaRcXMT7JAXD330w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSEyPIEXmh1tQjgnsKLwzMcCaNhkLwV-qYe1w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRIQa_HiGXRaxiwbdiGLtAn9W95S3FZtrgFXQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRjOvTJjDpfBcyQSlOKz0I2q-ae7THnWq0ANQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQau6x4-M4tMHOJrYB2RnuomuO3tpPMvoLPbA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTEjzQ6rgMnBWBrLLnpu-ulWsY0H5Tr4H2aLw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ8OzSWLtZut5AknnkORjkPqP90MKNqHiug5Q&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRWY02zF2uNw22oYWRzR316KmzstslDKFQ0Kg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRzKs7_88HriE0SVCHb4Hic1MMtcDgAJEnH0A&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTOEjqOSMQWJrPHAKnQKyoEyfxI50dRomKisA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGAW3mFdKjkztNNGSNPBX71Fr38O8r98dE-WHBIUmq6f-jTzBgMK8qmlz9SCblQx7yKGg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSm3e3R1NgrjxQgGK2wWsRNRfLuBCJ733F3hxj1O0hXygaQnnxcy5zNUxC0s6z3IbsMrSM&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQA0QSsr1ef3v1pDNr8ODF81PjwEgdsvqtbsd7bTwkpvvvfK6C1RnZwM-vMcVgBMB6ALQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTlVuLQ1IU7iDQW1SnT3d7RlO8sVoIUDg0V6MVO0sf4FqcvS1LTaTaHjCsrvR-JMKXhLps&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRypvtQkWZ0zOHHTSdFYmBg6Z6eYR8tkF8RQiSE_Z0Jas5FnPyQGZ7Sz1DawKayJEibXMs&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTYlxvaHNI9J8Evk5MSRZG1OB8I_49Npq8HT_BNQwDI0gOXUl4lcO9FvZdDlTorebr8H5c&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS59EdBgn241X6AHnqIci0vLOW55sXl3swSDuGeWN2UqW71bVDJBnMLi9OYRXiNFAYa-CM&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSDEdhWg6DK9JMDB30ntied-WHmtc2nd91Xyy3N-rrZInQJAXj1ewmJh2NrYi-8o6-8Lds&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS32aegovK5MyMVoKdTq6zenwxuy4YcFfJhmz1zAk1LcP-Qrl21dK0oH3xE20Fl681h3zA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSLuGsWUN553RqOJzvNkJc23kiXV0sKfQ3C9PN7NTfks3hL3XFi9h34RXyH2PuYxrWo788&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPGKDnGVhiX-KMeLWg8nXNGZSYBcBE9e231jKiZlgeQuz7oYH-1D8NDrYP251m8o2E_4Y&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTSHccTQhSBc7lsIJek-QlFc1KSCoCVKFDLHRvPoDtS-8R69uBx4cqPHPD4_VPHyx3TaWE&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHpLApRWcGmjkLShXmqLJTIMcsYrBZbIG_tnkzLZZVuL0sExIldSTXsuvGCkYHGAb-FPQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSwdFSpIY3-rHhydGmnDjeV5Fl4eVxm5UGN2vRlpvZN-AEdZ5GIjj7LdLT3zlUxc2gw14Y&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQqF7Iv2whbluAb4XXAKKbp4We3NIBkrUYarrEebJyIcxJwtyBFw5Hl1-1pJK2cC2Uq5eo&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSqtOTCWFt2rlXrFv8bgRiSN0xyOsl7mtqVxcAmGIupJRNJuw8jwsWSbpiwsCkcwDz6iAw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ_viVeeKr3lBObNy8suQkfhfgXx-Gma_IcCVaGKXTct-HsVQ4VoWvYAp6NmSxXmVbBgaw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSCQwM09pK5r1zGpvr6UH-wEKzJog5pHdXpzXvpgNU7wOie0QgUDamaCBHgUGNRiqAtWrA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSow10VBA3JqjLZmmnKEll5m0kPQtM-26qPTdb9fl30FEJnSaz7uyotaZS9iGaVKi-gUvU&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR85J-KfrDj5YJ512H53VvZQ5Ll2K1NgZQ7k8LfQFEI2j_XwEOd1W9MZgQ09FCgmf7qYqo&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ5wIbVJJyE3xbh4y2lfpfN3hDJvnnDMkCIAg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSLrwcgx1XCTw9A36LhbkOoF7DGDObH9Usm8w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRcBn2FMtRL7S9NdzmWtiVHYyRu-zEB1O1Eg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSAQGCnWIrLCXSgZX6ngu8lMFUgq4J9bbMYew&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcpaOscuWSjhCHQNxoSbtr9GjDta34jzFHbA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQEVa6grkXq5ry_Zj2CSlQ43s4Xqx2JlvZj4w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQMG9GZDSUb1NsfXEKf-xagLtyHszb_cimsWg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSUjGD3ALCxJIE6ClRQEpNKIqcx3Uj7afTF9w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRitOJy2hhuQa6YvtOAXCSORnaFzaRLUZ15oQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSQLZlnkv4ytx966QmxIYEw3T_aplo_Z7I1WA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSytACVYw0Warcdyp2KANwo-1gy6CR2cMURBQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS571-gvhFUwhyWoS2ILHLlkBq31WDhjwVoMg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRweLos4WdjyT8PTfkC4vK7xDwF3zs_jDAdWw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRAlLT2BEUI1wPTAyXYcKILwmlZqMeBmN7bg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRLgcOOLP0mfOlwlu9cJHPzYPn667h6Z-B7jA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSi_dWUqpI3Jk-txuUMiow7kM7qKEbcAqI10w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS17jr0YWZgzfMURcg6SqQXyIeSSx2M2mFSZw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS6i0zpM3UPpi8-BdbvBwtHiDvsBZfzhKIfqg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-NG11x1U-19wUy_kql2rbpNphYrCkRQaxPQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQBcxyF1YZtw7H8gtsEzYvfrFSZLmfTqikWJw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRIxZbeIsnhNqh5DjZmYi_Ay-UUqOXP8xNFVA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR1b79EIarQ_SW_302ejlykj3VdFLI7blVU6w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTZ9VdVVP2o-N7Zfl4VCN9EaTy9L9w5H_96jg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQkIOA1Uv_qMXw7n0gQY3uJT17WeMdw8-lorA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQMzJ933d-CvtZID7frQbVK-HdLvcWa1XHzig&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS9mTb3og1OvqKvX2WTVpSWBzLUuhukwk12QQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRF2Q-BshH4Z3EluczsMUSFJS2FBVBBkx8E7A&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSuNIxycedt1XlFgh7nB8yddwnTzp7UEag4hA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSCZ8f5Zmamh5i1TSuDjkAVnFjg5g6AbdnTKw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRF7c011H_oaiP4B26uAUdTLFWglaeVVHGVLg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSyq4s5mvZHQcD5uufvM9_fI_iRAPTiss5J0A&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQhlCnh4UnESGu7v2TaNfbqOi8spNuRBMYf0w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSqCMPs7K0vy1KXCHuGLG4bhJmIIWfSpt2lBQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQjS8FFfbHB7JYgT3kORU9UIT3tB3yhfvVGiQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSS0mYBIiebk2xQpFHWN23IBpL9tAenfRuq6Q&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQeGqAbiXJ6Uoay9Dc-FNpWqqB9mK4Mklr-iA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTjyxgJ6H4_PodOnr9GUEw9xrte6ZaKLDeqKw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRhqhWXb_tX_MDKh2VkVyGVYesZZo4sL1WxcA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRnEmN88BVFJN3cJjhDedPpQCx44Qd3PyQhxg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTLxBQMgXcTIdOnFEj6i6UUkAM9g23oPz_Zxg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSGZ-t7vtTTJLRRLyhV8ztk8zLb5-R7FdZTvQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRG7ep3fusI1xo_U5pSFjhNN0hT7D1YWiNAWg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRYGle6S90-Vhct8Jy6TmjpxPKj_1f_HJ0YTw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRvkLuwh8kpRoFEePkIvZohE5rm5SzPtPlrIA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQp6vaD4XiQbThaoUNh_cxsvfpSqhKmJv7sOw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQd9XvKBYbESwDYCd_seno-GnOKwrG9kjRa9A&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQF1ulTUqOOIx0bCXJw-bvN0MZQkY8y49H6sg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQjLO1n2g7-ph4cxjKQUxQ_XT5-zxxZOXZvwg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRuKfEBjxW7FwB_bf4aG6L0T97ugM5gFkCcaA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTVLR1jegSuz7FImQDmIiyHJPKlcotKgX7Tog&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR5b8T2q6QcyZnp7JHyVeWUQZyJDbrrnvnLvw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRGGkYH1utfVFEbDU1li6F57z4dtzz4FXCXFQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ2FN4cUyO1pMn9Ocu-x2dCiFA0GADNTApeWQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSuD1hqpPzwrZCx1piiXkpFwbYvgl6FI8FlGA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSVlh7QHEoViSGcl2UQLqQhytdBYC0HqCYx1w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTX8lQqiVpoQUX7SOBChQpJzRwZP0m3zCvTzw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTaifFMUFKMUQkNpx5ks4MYvSCDYOWzn99Tcg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQqcJnX6FSNGfTHbbtAg8b3OeYjM326aDWsaA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRVLpfHDEURMmqcfAegBmW38VHGzR1as0nEtg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRh7uXrwDDwg-qZUH8skerZVW93XwnmhcI5cw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQycDpBIhrrcLA1qBsjVOD41heKVpD2jgfO1A&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTn813B9hRA_iEqGh8M9ZLHsSfY1NYJUgUeJA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR0OKeiJMJmJ-NTV6kzO3IHKIerEXWPeDbTTA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQrzlP8yUDd0Yj64b9tRpYfA3SyK3W-DO8xvg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSn2All9u-Li4vWtViU3RzSbP0jWONF4ykRUw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTuIpGbbmXETIE54O6SaVZa93oD1kpiHM49w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSun6tq-cz4yTf-aTVSFtHauFe5rW8y_7kYOA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSulMOCCqf2seXzVQfhucZeAi-BUKa9fBEtEw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR7xQe-PlY5FvPltNIDjHg26Aomf8cV39fHlQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQptBuknKqObx2oBDtbxAF2m9q6Sk1xJ6FelQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcROIETr4OoMg881sBCNDboDyxrvFYaQ-v5tdA&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQjPE2Gn-EGvgVd8GFxKty5NC5VzHKkg8Ou1g&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQrQGfVDgG_LjAfVLBK7g-gTtmkecv2ilE43Q&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTqvkipD2UFh9PXcc5-JaCPZwuye7J8G2bUUw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR71fIqpducyF2hckOhkCo1veWSIiI21cHVeQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQXblnUY-A4FCr3tAm9j9EtHtAjgr9M5LCCSw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTBnxMPIVvEhHim3XPVSo3r7YHDh3Ixf8c86A&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRPw1GMUjv8qy2C6hNs6ejo_kNttAs-e5jwvQ&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRjVkVXsOx00xYsmvylGyckDxv4-DdiJBJLEw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQSsqOwbWpbtIGPphudUiiBBEr9ChBoFkzxMg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQx9YulGtKkdLOLNgR2iYsMSTuRvQzNWw5Etjgxo43uYvCRDETd9EOnfJWb7uyp1cXNEJU&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRUh7OqJCkEZ0JRK5C5iA9fRjFJ7c6eEfc9U87N0dWBC1Fchba3LzuuDqOOwH_WVbow8F4&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSiJ_Hp6Zoeq2Qm2aJy7vvZm02IX5gVTxZnWx1JWHRArItfJXg9VKEMNodHtw0X0M4VKeo&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTgjoMJfduAT4Ses-Ewr9Ro61POqHeCFV8g8pfix4hamWowsy2F86ePXwBhITA7fylTdvY&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRd_V0ShZs6iCykPQGiiDeuM68qCOTVm7iG-B_uciho1G4cZyFj-KOisrzTy5s2QA2V_jw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSa_383nDqZ4avzC_7uzzr_L-jDkdp5WgtMdnBfnElpD2oE1oM4uE3_lWd4_AdzwkV0Xeo&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSmutjDR01wmqjcNewc18BktSj2u3zVWIcujiLmpxq-61c1_-OduUWAjgvDbTYJ90el9JI&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTg9_2uOsc5g21DlJoGVq36wOmQzuJywOOpLYeHIu25Yrx5OhVcqY7PAIAfWVVWxS4WtL8&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSr_8eMzc0gdQXttg-hgunFRN3sz_VMvOv5j8P6riRMs1MMiY1yKebFiG4UU903-Q_1Xfw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSBLzjLQcmBY3KU1222PyQAxTKb-9d9qrDA1V2j2OAL6OMVz8tBrCI8HyJFF9ox78o56nM&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTuKAQmE_0lmox8cwAeoyQOsfwMte1lA3iC0PVm9tLIonQ6VTsMNbiD6Tni3omVZ72JKVg&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-dds3wVnsl23nja9ibVzHAvr-vO5L-nFcW1q3E3UkdCY9bUqGd5fXQVQv4l-Jf7MUPf8&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcROCHcNT2bjBz3a2KXr5eRnQtJqYQ3BGp6STjw38YxN8o-Jc-NAFyGTu3FP3_8e7g2GNWw&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS-KLyUQqV4btmRrrNZByIZrtQMA4P1e2maq5JJsM6OgPNsioNXdGmY68pPD937F1VBJJ8&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRy7i_CSS54RNtzE1VLdZI9hySPBG8hCBtdonePPsUFP9ioK60F4rCmqzOPwxDDrw15K4U&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQvv8g6N-Ugl40e5QfjFeX2uto9nh2w9HRdjEINe99SpVveq4C7V42Jt0X7rb2euN0a32w&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQyoOSlHUtdXuzIA0kGz1K21k4ceoxioq6XJ5qKJ-miisWOfg1dPj-iL34HVD1LDZ4UVmk&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTAnxDWwwKwa9lJHtoFlvApea5kWb1atBL1vDS37IqWnlsRU-NZqap9VMy-VsZBz_mP8Os&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_SgrSgH027gzdCOLFqjMvJgHBX2CqU1ztbvFtLZFV1TdnTycx_FS4-lZkh3pNFHyrOIM&usqp=CAU",
]


def genRCategory(count):
    hotels = Hotel.objects.all()

    for index in range(0, count):
        code = str(random.randint(9999999, 99999999))
        rcategory = RCategory.objects.create(
            name=f"Номер №{code}",
            hotel=random.choice(hotels),
            price_per_night=random.randint(2, 500) * 100,
            offer_type=random.choice(RCategory.offer_type_choices)[0],
            square=random.randint(2, 10)*5,
            max_people=random.randint(1, 5),
            count_room=random.randint(1, 5),
            count_bedrooms=random.randint(1, 5),
            beds=random.choice(RCategory.beds_choices)[0],
            description_of_the_room=f"Описания номера №{code}",
        )
        services = random.choices(
            list(RService.objects.all()), k=random.randint(2, 20))
        rcategory.service.set(services)
        try:
            for img_index in range(5):
                rimg = RImg.objects.create(rcategory=rcategory)
                img_file = urllib.request.urlretrieve(random.choice(img_scrs))
                rimg.image.save(
                    os.path.basename("img.png"),
                    File(open(img_file[0], 'rb'))
                )
        except:
            print(f"Ошибка на {code}")
        else:
            print(f"Создано {code} категория номера")
            rcategory.save()


def genRoom(count):
    RCs = RCategory.objects.all()
    for index in range(count):
        rc = random.choice(RCs)
        room = Room.objects.create(
            category=rc, room_number=str(random.randint(99999, 999999)))
        room.save()
        print(f"Создана комната {room.room_number}, типа {rc.name}")


def genUser(count):
    for index in range(count):
        code = random.randint(999999, 9999999)
        username = f"Клон №{code}"
        lastname = f"Клонов №{code}"
        middlename = f"Клонович №{random.randint(999999, 9999999)}"
        login = f"login_{code}"
        password = f"password_{code}"
        phone = f"+7{random.randint(999999999, 9999999999)}"
        gender = random.choice(["Мужской", "Женский"])
        email = f"email{code}@gmail.com"

        user = User.objects.create_user(
            username=username,
            lastname=lastname,
            middlename=middlename,
            login=login,
            password=password,
            phone=phone,
            gender=gender,
            email=email,
        )

        user.save()
        print(f"№{code} - {login} - {password}")


def genHotel(count):
    hotels_id = Hotel.objects.all().values_list("owner", flat=True)
    users = User.objects.exclude(id__in=hotels_id)
    print(f"Пользователей без отеля {len(users)}")
    if len(users) > count:
        users = users[0:count-1]
    for user in users:
        name = f"Отель {user.username}"
        owner = user
        descriptions = f"Тут нету описания"
        type_hotel = random.choice(["1_1", "1_2", "1_3", "1_4", "1_5", "1_6", "1_7", "1_8", "1_9",
                                    "1_10," "1_11," "2_1", "2_2", "2_3", "2_4", "4_3", "4_4", "3_1",
                                    "3_2", "3_3", "3_4", "3_5", "3_6"])

        check_in_time = "12:00"
        departure_time = "14:00"

        stars = random.randint(0, 5)

        breakfast = bool(random.randint(0, 1))
        lunch = bool(random.randint(0, 1))
        dinner = bool(random.randint(0, 1))

        coordinates = ""

        active = True

        percentage = random.randint(14, 30)

        hotel = Hotel.objects.create(
            owner=owner,
            name=name,
            descriptions=descriptions,
            type_hotel=type_hotel,
            check_in_time=check_in_time,
            departure_time=departure_time,
            stars=stars,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            coordinates=coordinates,
            active=active,
            percentage=percentage,
            instant_booking=1,
            allowed_child=0,
            allowed_animal=0,
            allowed_smoking=0,
            allowed_party=1,
            minimum_days_before_arrival=0,
            minimum_days_of_stay=1,
            for_long_term_stays_minimum_days_of_stay=1,
        )

        Address.objects.create(
            hotel=hotel,
            city=random.choice(["Москва", "Анапа", "Владикавказ"]),
            region="Регион",
            street="Улица 1",
            body="",
            house="1",
            floor="3",
            apartment="5",
        )

        for img_index in range(5):
            try:
                rimg = HImg.objects.create(hotel=hotel)
                img_file = urllib.request.urlretrieve(random.choice(img_scrs))
                rimg.image.save(
                    os.path.basename("img.png"),
                    File(open(img_file[0], 'rb'))
                )
            except:
                print(f"Ошибка на {name}")

        print(f"Отель {name} создан")
        hotel.save()


def get_random_date(start, end):
    delta = end - start
    return start + timedelta(random.randint(0, delta.days))


def getBooking():
    rooms = Room.objects.all()
    user = User.objects.get(id=1)
    start_dt = DT.strptime('26.02.2023', '%d.%m.%Y')
    end_dt = DT.strptime('25.03.2023', '%d.%m.%Y')
    for n in range(10):
        room = random.choice(rooms)
        datatime_start = get_random_date(start_dt, end_dt)
        d = datatime_start + timedelta(days=random.randint(3, 9))
        datatime_end = d
        status = random.choice(
            ["not_confirmed", "confirmed", "do_not_live", "live", "cancelled", "completed"])
        people = random.randint(1, room.category.number_of_bed)
        price = room.category.price_per_night * d.day
        print(price)
        Booking.objects.create(
            room=room,
            user=user,
            datatime_start=datatime_start,
            datatime_end=datatime_end,
            status=status,
            people=people,
            price=price,
        )
