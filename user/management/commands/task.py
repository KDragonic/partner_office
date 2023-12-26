import datetime
import time
from django.core.management.base import BaseCommand
import pytz
from utils.models import Constant
from user.models import Notification, User, Bonus_rubles as Bonus_user, FinancialOperation
from hotel.models import Bonus as Bonus_hotel, HBoost, Booking, Hotel, ModerWork
from chat.models import Chat, Message
import asyncio
from django.db.models import Q, Func, F, IntegerField
from brontur.funs import add_months


class Command(BaseCommand):
    def minute_operations(self):
        """
        Функция minute_operations выполняет различные операции, связанные с бонусами, бронированиями и
        отменами, с некоторыми уведомлениями и удалениями на основе определенных временных порогов.
        """
        tz = datetime.timezone(datetime.timedelta(hours=3))
        print(f"Запуск - Обновление данных: {datetime.datetime.now(tz)}")
        while True:
            today = datetime.datetime.now(tz)
            print(f"Обновление данных: {today}")
            delite_date = today - datetime.timedelta(days=6*30)

            # Уведомления о бонусах в чат 7 штук (Клиент)
            bonus_user_days_left_list = Bonus_user.objects.all()

            for bonus in bonus_user_days_left_list:
                days_left = bonus.days_left()
                user : User = bonus.user

                send_result = None

                bonus_value = bonus.value
                send_days_left = None

                print(f"Бонус {bonus} ({days_left}):")
                thresholds = [("2_d",2), ("7_d",7), ("1_m",30), ("2_m",60), ("3_m",90), ("4_m",120), ("5_m",150)]

                for threshold in thresholds:
                    if not bonus.notification_marks[threshold[0]] and days_left < threshold[1]:
                        send_days_left = threshold[1]
                        bonus.notification_marks[threshold[0]] = True

                if send_days_left:
                    bonus.save()
                    send_result = user.send_telegram(f"Внимание! У вас есть бонус на сумму {bonus.value}, который будет удален через {send_days_left} дней.")

                print(send_result)

            # Уведомления о бонусах в чат 7 штук (Отель)
            bonus_hotel_days_left_list = Bonus_hotel.objects.all()

            for bonus in bonus_hotel_days_left_list:
                days_left = bonus.days_left()
                user : User = bonus.hotel.owner

                send_result = None

                bonus_value = bonus.value
                send_days_left = None

                print(f"Бонус {bonus} ({days_left}):")
                thresholds = [("2_d",2), ("7_d",7), ("1_m",30), ("2_m",60), ("3_m",90), ("4_m",120), ("5_m",150)]

                for threshold in thresholds:
                    if not bonus.notification_marks[threshold[0]] and days_left < threshold[1]:
                        send_days_left = threshold[1]
                        bonus.notification_marks[threshold[0]] = True

                if send_days_left:
                    bonus.save()
                    send_result = user.send_telegram(f"Внимание! У отеля есть бонус на сумму {bonus.value}, который будет удален через {send_days_left} дней.")

                print(send_result)




            print(f"Максимальная дата удаления: {delite_date}")
            # Бонусы пользователя
            bonus_user = Bonus_user.objects.filter(date__lte=delite_date)
            print(f"Бонусы пользователя ({bonus_user.count()} из {Bonus_user.objects.all().count()}):")

            bonus_user.delete()

            # Бонусы отеля
            bonus_hotel = Bonus_hotel.objects.filter(date__lte=delite_date)
            print(f"Бонусы отеля ({bonus_hotel.count()} из {Bonus_hotel.objects.all().count()}):")

            bonus_hotel.delete()

            # Бусты отеля
            delite_date = today - datetime.timedelta(days=1)
            hboosts = HBoost.objects.filter(date__lte=delite_date)
            hboosts.delete()

            # Бонусы за проживание для клиента
            bookings_datetime_stay_bonus = Booking.objects.filter(
                datetime_stay_bonus__lte=today, is_stay_bonus=False, status="left")

            for booking in bookings_datetime_stay_bonus:
                chat: Chat = Chat.objects.filter(
                    Q(data__booking=booking.id)).first()
                if chat:
                    chat.add_info_message("user.add.bonus.booking_left", {
                                          "count": int(booking.site_price) * 0.2})

                Bonus_user.add(booking.booking_user,
                               int(booking.site_price) * 0.2)

                Notification.new(booking.booking_user, "Бонусы за бронь",
                                 f"Выдано бонусов {int(booking.site_price) * 0.2} за бронь {booking.id}")
                FinancialOperation.new(booking.booking_user, int(booking.site_price) * 0.2, True,
                                       "booking", f"Выдано бонусов {int(booking.site_price) * 0.2} за бронь {booking.id}")

                booking.is_stay_bonus = True
                booking.save()
                print(
                    f"Получены бонусы за бронь (Клиент) {booking.id} - {int(booking.site_price) * 0.2}")

            # Бонусы за проживание для отеля
            bookings_datetime_hotel_bonus = Booking.objects.filter(
                datetime_hotel_bonus__lte=today, is_hotel_bonus=False, status="left")


            # Проход по отелям
            for booking in bookings_datetime_hotel_bonus:
                hotel: Hotel = booking.get_hotel()
                if hotel:

                    # Дать бонусы
                    result_calc = Constant.cashback_calculation(hotel.type_hotel, "to_hotel", booking.site_price, booking.calc_price(booking.booked_room.category, [booking.start_date_time, booking.end_date_time])["room_full"])
                    Bonus_hotel.objects.create(
                        user=user,
                        value=result_calc["value"],
                        text="Получено за отзыв",
                        lifespan=result_calc["lifetime"]
                    )

                    booking.is_hotel_bonus = True
                    Notification.new(hotel.owner, "Бонусы за бронь клиента", f"Выдано бонусов {result_calc['value']} за бронь {booking.id}")
                    FinancialOperation.new(hotel.owner, result_calc['value'], True, "booking",f"Выдано бонусов {result_calc['value']} за бронь {booking.id}")
                    print(f"Получены бонусы за бронь (Отель) {booking.id} - {result_calc['value']}")
                    booking.save()

            unpaid_bookings_datetime = today.astimezone(pytz.timezone('Etc/GMT+0')) - datetime.timedelta(minutes=20)

            # Брони которое не оплатили за 20 минут
            unpaid_bookings = Booking.objects.filter(created_at__lte=unpaid_bookings_datetime, payment_status="not_paid", status="new")

            unpaid_bookings_datetime_str = unpaid_bookings_datetime.strftime('%H:%M:%S')

            print(f"Удаления не оплаченых бронь ({unpaid_bookings_datetime_str}), len {len(unpaid_bookings)}")

            for booking in unpaid_bookings:
                try:
                    created_at_str = booking.created_at.astimezone(tz).strftime('%H:%M:%S')
                    created_at_20m_str = (booking.created_at + datetime.timedelta(minutes=20)).astimezone(tz).strftime('%H:%M:%S')
                    print(f"id {booking.id}, created_at ({created_at_str} -> created_at_20m_str {created_at_20m_str})")

                    booking: Booking
                    user: User = booking.booking_user
                    hotel: Hotel = booking.get_hotel()
                    if hotel:
                        if booking.payment_status == "not_paid":
                            booking.сancellation_of_the_reservation("site")
                            Notification.new(
                                user, "Бронь отменилась", f"Бронь {booking.id} отменилась, за 20 минут не было оплачено картой")
                            booking.save()
                except:
                    pass

            moder_work = ModerWork.objects.all()

            current_time = round(datetime.datetime.now().timestamp())
            for work in moder_work:
                work : ModerWork

                reminders = work.reminders

                if isinstance(reminders, list):
                    if len(reminders) > 0:
                        for index, item in enumerate(reminders):
                            if item["datetime"] <= current_time and not item.get("send", False):
                                text = item["value"] if len(item["value"]) > 0 else "В рабочем листе"
                                reminders[index]["send"] = True
                                Notification.new(work.moder, "Напоминание", text, "", True, True, False, True)
                                print(f"Напоминание отправлено -> {text}")

                work.reminders = reminders
                work.save()

            print(f"Ожидание 5 минут")
            time.sleep(60*5)

    def handle(self, *args, **kwargs):
        self.minute_operations()
