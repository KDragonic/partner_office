import datetime
import re
from django import template
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import path, reverse
from brontur.funs import generate_password
from user.models import User

from hotel.models import Booking
from chat.models import Chat
from django.http import Http404



register = template.Library()


@register.simple_tag(takes_context=True)
def get_card(context, type, date):
    user = context.request.user
    result = {
        "cards": []
    }
    if type == 'profile_booking':

        if date == "my":
            bookings = Booking.objects.filter(booking_user=user)
            for booking in bookings:

                booked_room_category_name = "Нет номера"
                try:
                    booked_room_category_name = booking.booked_room.category.name
                except:
                    pass


                end_date_time = booking.end_date_time.date()
                start_date_time = booking.start_date_time.date()

                days = (end_date_time - start_date_time).days

                result["cards"].append(
                    {
                        "user": {
                            "username": f"{booking.booking_user.username} {booking.booking_user.lastname[0:1]}.",
                        },
                        "room": {
                            "name": booked_room_category_name,
                        },
                        "booking": {
                            "id": booking.id,
                            "datetime_start": f"{datetime.datetime.strftime(booking.start_date_time + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "days": f"{days} дней",
                            "datetime_end": f"{datetime.datetime.strftime(booking.end_date_time + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "created_at": f"{datetime.datetime.strftime(booking.created_at + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "created_at_obj": booking.created_at + datetime.timedelta(hours=3),
                            "count_a": f"{booking.adults_count}",
                            "count_c": f"{booking.children_count}",
                            "price": f"{booking.site_price}",
                            "status": booking.get_status_display(),
                            "status_code": booking.status,
                            "url": reverse("profile_booking_full", args=[booking.id]),
                        }
                    }
                )
            result["cards"].reverse()
            result["cards"] = sorted(result["cards"], key=lambda card: card["booking"]['created_at_obj'], reverse=True)

            return render_to_string('template/card_profile_booking.html', result)

        if date == "hotel":
            select_hotel = context.request.session.get('hotel')
            if not select_hotel:
                return Http404("Объект не найден")

            bookings = Booking.objects.filter(booked_room__category__hotel__id=select_hotel)
            for booking in bookings:
                if booking.status == "close":
                    continue

                booked_room_category_name = "Нет номера"
                try:
                    booked_room_category_name = booking.booked_room.category.name
                except:
                    pass

                end_date_time = booking.end_date_time.date()
                start_date_time = booking.start_date_time.date()

                days = (end_date_time - start_date_time).days

                result["cards"].append(
                    {
                        "user": {
                            "username": f"{booking.booking_user.username} {booking.booking_user.lastname[0:1]}.",
                        },
                        "room": {
                            "name": booked_room_category_name,
                        },
                        "booking": {
                            "id": booking.id,
                            "datetime_start": f"{datetime.datetime.strftime(booking.start_date_time + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "days": f"{days} дней",
                            "datetime_end": f"{datetime.datetime.strftime(booking.end_date_time + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "created_at": f"{datetime.datetime.strftime(booking.created_at + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "created_at_obj": booking.created_at + datetime.timedelta(hours=3),
                            "count_a": f"{booking.adults_count}",
                            "count_c": f"{booking.children_count}",
                            "price": f"{booking.site_price}",
                            "status": booking.get_status_display(),
                            "status_code": booking.status,
                            "url": reverse("profile_hotel_booking_full", args=[booking.id]),
                        }
                    }
                )

            result["cards"] = sorted(result["cards"], key=lambda card: card["booking"]['created_at_obj'], reverse=True)

            return render_to_string('template/card_profile_booking.html', result)

    if type == 'list_booking':
        if date == "client":
            bookings = Booking.objects.filter(booking_user=user)
            for booking in bookings:

                booked_room_category_name = "Нет номера"
                try:
                    booked_room_category_name = booking.booked_room.category.name
                except:
                    pass


                end_date_time = booking.end_date_time.date()
                start_date_time = booking.start_date_time.date()

                days = (end_date_time - start_date_time).days

                result["cards"].append(
                    {
                        "user": {
                            "username": f"{booking.booking_user.username} {booking.booking_user.lastname[0:1]}.",
                        },
                        "room": {
                            "name": booked_room_category_name,
                        },
                        "booking": {
                            "id": booking.id,
                            "datetime_start": f"{datetime.datetime.strftime(booking.start_date_time + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "days": f"{days} дней",
                            "datetime_end": f"{datetime.datetime.strftime(booking.end_date_time + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "created_at": f"{datetime.datetime.strftime(booking.created_at + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "created_at_obj": booking.created_at + datetime.timedelta(hours=3),
                            "count_a": f"{booking.adults_count}",
                            "count_c": f"{booking.children_count}",
                            "price": f"{booking.site_price}",
                            "status": booking.get_status_display(),
                            "status_code": booking.status,
                            "url": reverse("profile_v2_booking") + f"?id={booking.id}",
                        }
                    }
                )
            result["cards"].reverse()
            result["cards"] = sorted(result["cards"], key=lambda card: card["booking"]['created_at_obj'], reverse=True)

            return render_to_string('template/card_profile_booking.html', result)

        if date == "hotel":
            select_hotel = context.request.session.get('hotel')
            if not select_hotel:
                return Http404("Объект не найден")

            bookings = Booking.objects.filter(booked_room__category__hotel__id=select_hotel)
            for booking in bookings:
                if booking.status == "close":
                    continue

                booked_room_category_name = "Нет номера"
                try:
                    booked_room_category_name = booking.booked_room.category.name
                except:
                    pass

                end_date_time = booking.end_date_time.date()
                start_date_time = booking.start_date_time.date()

                days = (end_date_time - start_date_time).days

                result["cards"].append(
                    {
                        "user": {
                            "username": f"{booking.booking_user.username} {booking.booking_user.lastname[0:1]}.",
                        },
                        "room": {
                            "name": booked_room_category_name,
                        },
                        "booking": {
                            "id": booking.id,
                            "datetime_start": f"{datetime.datetime.strftime(booking.start_date_time + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "days": f"{days} дней",
                            "datetime_end": f"{datetime.datetime.strftime(booking.end_date_time + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "created_at": f"{datetime.datetime.strftime(booking.created_at + datetime.timedelta(hours=3), '%d.%m.%Y %H:%M')}",
                            "created_at_obj": booking.created_at + datetime.timedelta(hours=3),
                            "count_a": f"{booking.adults_count}",
                            "count_c": f"{booking.children_count}",
                            "price": f"{booking.site_price}",
                            "status": booking.get_status_display(),
                            "status_code": booking.status,
                            "url": reverse("profile_v2_hotel_booking") + f"?id={booking.id}",
                        }
                    }
                )

            result["cards"] = sorted(result["cards"], key=lambda card: card["booking"]['created_at_obj'], reverse=True)

            return render_to_string('template/card_profile_booking.html', result)

def profile_hotel_booking_full(request, id):
    select_hotel = context.request.session.get('hotel')
    if not select_hotel:
        return Http404("Объект не найден")

    bookings = Booking.objects.filter(booked_room__category__hotel__id=select_hotel, id=id)

    if not bookings.exists:
        return render(request, '404.html', status=404)

    booking = bookings.first()

    children_ages = booking.children_ages.all()

    children_ages_text = ""
    if children_ages.count() <= 0:
        children_ages_text = "Без детей"
    else:
        children_ages_list = []
        for child in children_ages:
            children_ages_list.append(str(child.age))

        children_ages_text = ', '.join(children_ages_list)

    booking_data = {
        'id': booking.id,
        'hotel': booking.booked_room.category.hotel.name,
        'room_name': booking.booked_room.category.name,
        'check_in': booking.start_date_time,
        'check_out': booking.end_date_time,
        'days_booked': (booking.end_date_time - booking.start_date_time).days,
        'count_a': booking.adults_count,
        'count_c': booking.children_count,
        'children_ages': children_ages_text,
        'accommodation_cost': getattr(booking.booked_room.category, f"price_{booking.adults_count + booking.children_count}") * (booking.end_date_time - booking.start_date_time).days,
        'amount_paid': booking.site_price,
    }
    booking_data["cost_difference"] = booking_data["accommodation_cost"] - booking_data["amount_paid"]
    context = {'booking_data': booking_data}
    return render(request, 'user/profile_hotel_booking_.html', context)


@register.inclusion_tag('template/telegram_card.html', takes_context=True)
def telegram_card(context):

    user = context.request.user

    if not user.token_telegram:
        user.token_telegram = "auth_code_" + generate_password(10)
        user.save()

    if re.match('auth_code', user.token_telegram):
        telegram_active = False
    else:
        telegram_active = True

    return {
        "auth_telegram": telegram_active,
        "token_telegram": user.token_telegram,
    }
