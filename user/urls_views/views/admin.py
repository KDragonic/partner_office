import datetime
import json
import math
import os
import re
from collections import Counter
import sys
import time
import traceback

import pytz
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q, QuerySet
from django.db.models.functions import Lower
from django.forms import model_to_dict
from django.http import (Http404, HttpRequest, HttpResponse,
                         HttpResponseNotAllowed, HttpResponseNotModified,
                         HttpResponseRedirect, JsonResponse)
from django.shortcuts import redirect, render
from django.template import Context, RequestContext
from django.template.loader import get_template
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

import concurrent.futures

from brontur.funs import *
from chat.models import Chat, Message
from hotel.models import (Address, Booking, Hotel, HService, RCategory, Room,
                          RService, Comment, ModerWork)
from user.models import (Bonus_rubles, FinancialOperation, Notification,
                         PermissionsMixin, User)
from utils.models import AdminLog, Constant, Img, Place


def moder_admin_owner_required(view_func):
    def wrapper(request, *args, **kwargs):
        user: User = User.objects.get(id=request.user.id)
        if user.is_authenticated and user.user_type in ["moder", "admin", "owner"]:
            return view_func(request, *args, **kwargs)
        else:
            return render(request, 'error_page.html', {'message': None, "status": 403}, status=403)
    return wrapper


def supermoderator(view_func):
    def wrapper(request, *args, **kwargs):
        user: User = User.objects.get(id=request.user.id)
        if user.is_authenticated and user.additional_info.get("permission"):
            if "supermoderator" in user.additional_info["permission"]:
                return view_func(request, *args, **kwargs)

        return render(request, 'error_page.html', {'message': None, "status": 403}, status=403)
    return wrapper


def supermoderator_or_owner(view_func):
    def wrapper(request, *args, **kwargs):
        user: User = User.objects.get(id=request.user.id)
        if user.is_authenticated and user.additional_info.get("permission"):
            if "supermoderator" in user.additional_info["permission"]:
                return view_func(request, *args, **kwargs)
        elif user.user_type in ["moder", "admin", "owner"]:
            return view_func(request, *args, **kwargs)

        return render(request, 'error_page.html', {'message': None, "status": 403}, status=403)
    return wrapper


def user_owner(view_func):
    def wrapper(request, *args, **kwargs):
        user: User = User.objects.get(id=request.user.id)
        if user.is_authenticated and user.user_type == "owner":
            return view_func(request, *args, **kwargs)

        return render(request, 'error_page.html', {'message': None, "status": 403}, status=403)
    return wrapper


@moder_admin_owner_required
def page_site_management(request):
    content = {
        "hotel_type": Hotel.type_hotel_choices,
    }
    return render(request, 'my_admin/site_management.html', content)


@moder_admin_owner_required
def ajax_site_management_settings_options_get(request):

    settings_options_obj = Constant.get("settings_options", "json")

    if settings_options_obj:
        settings_options = settings_options_obj
    else:
        settings_options = {
            "cashback_table": {}
        }

        for code, name in Hotel.type_hotel_choices:
            settings_options["cashback_table"][code] = {
                "booking": {
                    "lifetime": random.choice([5, 15, 30, 60, 90, 120]),
                    "type": random.choice(["accommodation", "site_price"]),
                    "value": round(random.randint(0, 5)) * 10,
                },
                "review": {
                    "lifetime": random.choice([5, 15, 30, 60, 90, 120]),
                    "type": random.choice(["accommodation", "site_price"]),
                    "value": round(random.randint(0, 5)) * 10,
                },
                "to_hotel": {
                    "lifetime": random.choice([5, 15, 30, 60, 90, 120]),
                    "type": random.choice(["accommodation", "site_price"]),
                    "value": round(random.randint(0, 5)) * 10,
                },
            }

    content = {
        "settings_options": settings_options,
    }

    return JsonResponse(content)


@moder_admin_owner_required
def ajax_site_management_settings_options_save(request: HttpRequest):

    param = json.loads(request.body)

    Constant.set("settings_options", param, "json")

    content = {
        "success": True,
    }

    return JsonResponse(content)


@moder_admin_owner_required
def page_ts_chat(request):
    full_chat = None
    user_full_chat = None
    chat_id = request.GET.get("chat")
    chats = []
    if chat_id:
        chat_qs = Chat.objects.filter(id=chat_id)
        if chat_qs.exists():
            full_chat: Chat = chat_qs.first()
            user_full_chat_obj = full_chat.users.filter(
                user_type__in=["client", "hotel", "user"]).first()

            if user_full_chat_obj:
                user_full_chat = model_to_dict(user_full_chat_obj)
                user_full_chat["fio"] = user_full_chat_obj.get_FIO()

                hotel_user_full_chat = Hotel.objects.filter(
                    owner__id=user_full_chat["id"]).first()
                if hotel_user_full_chat:
                    user_full_chat["hotel"] = hotel_user_full_chat.name

    chats_qs = Chat.objects.filter(data__type="ts")

    for chat_item in chats_qs:
        item = {}
        try:
            data = chat_item.data
            title: str = data.get("title")
            user_chat: User = chat_item.users.all().first()
            FIO = user_chat.get_FIO()
            item["username"] = FIO if FIO != "" else "Без ФИО"
            item["title"] = title if title else "Без темы"
            item["url"] = f"/admin/page/ts/chat/?chat={chat_item.id}"
            item["id"] = chat_item.id
            item["unread_count"] = Chat.get_the_number_of_unread(
                chat_item, request.user)
            chats.append(item)
        except:
            continue

    chats.reverse()

    content = {"full_chat": full_chat.id if full_chat else None,
               "user_full_chat": user_full_chat if user_full_chat else None, "chats": chats}
    content = add_meta(content, title="Чаты техподдержки")
    return render(request, 'my_admin/ts_chat.html', content)


@permission_required('tech_support_requests')
def page_client_hotel_chat(request):
    full_chat = None
    chat_id = request.GET.get("chat")
    chats = []
    if chat_id:
        chat_qs = Chat.objects.filter(id=chat_id)
        if chat_qs.exists():
            full_chat = chat_qs.first().id

    user: User = User.normal(request.user.id)

    chats_qs = Chat.objects.filter(Q(data__has_key='booking'))

    for chat_item in chats_qs:
        try:
            booking: Booking = Booking.objects.get(
                id=chat_item.data["booking"])
            rc: RCategory = booking.booked_room.category
            hotel = rc.hotel
            buff_item = {}
            buff_item["id"] = chat_item.id
            buff_item["hotel_name"] = booking.booked_room.category.hotel.name
            buff_item["img"] = Img.get_url(
                "hotel.hotel", hotel.id, 0)[0]["url"]
            buff_item["url"] = f"/admin/client_hotel/chat/?chat={chat_item.id}"
            buff_item["url_booking_text"] = f"Бронирование - {booking.id}"
            buff_item["status"] = booking.get_status_display()
            buff_item["start"] = booking.start_date_time.strftime("%d.%m.%Y")
            buff_item["end"] = booking.end_date_time.strftime("%d.%m.%Y")
            buff_item["name"] = rc.name
            chats.append(buff_item)
        except:
            continue

    chats.reverse()

    content = {"full_chat": full_chat, "chats": chats}

    return render(request, 'my_admin/client_hotel_chat.html', content)


@moder_admin_owner_required
def page_list_moderation_hotel(request):
    content = {
    }
    return render(request, 'my_admin/moderation_hotel.html', content)


@moder_admin_owner_required
@cache_page(60 * 5)
def ajax_list_moderation_hotel(request: HttpRequest):
    params = request.POST.dict()

    hotel_type = params.get('hotel_type', 'all')
    hotel_status = params.get('hotel_status', 'on_moderation')
    search_value = params.get('search[value]', '')

    order_by_field = 'id'
    if params.get('order[0][dir]') == 'desc':
        order_by_field = '-' + params.get('order[0][name]', 'id')
    else:
        order_by_field = params.get('order[0][name]', 'id')

    valid_hotels = Hotel.objects.filter(is_delete=False)
    recordsTotal = len(valid_hotels)

    if hotel_type == "full":
        valid_hotels = valid_hotels.filter(
            Q(additional_info__created_by_parser=False))

    if hotel_type == "parser_hotel_with_owner":
        valid_hotels = valid_hotels.filter(
            Q(additional_info__created_by_parser=True, additional_info__given_to_man=True))

    if hotel_type == "parser_hotel_without_owner":
        valid_hotels = valid_hotels.filter(
            Q(additional_info__created_by_parser=True, additional_info__given_to_man=False))

    if hotel_status == 'active':
        valid_hotels = valid_hotels.filter(
            enable=True, is_pending=False, is_delete=False)
    elif hotel_status == 'banned':
        valid_hotels = valid_hotels.filter(Q(enable=True) & Q(is_pending=True) & Q(
            is_delete=False) & Q(additional_info__has_key="banned"))
    elif hotel_status == 'on_moderation':
        valid_hotels = valid_hotels.filter(
            enable=True, is_pending=True, is_delete=False)

    if search_value:
        valid_hotels = valid_hotels.filter(Q(id__startswith=search_value) |
                                           Q(name__icontains=search_value) |
                                           Q(owner__email__icontains=search_value) |
                                           Q(owner__phone__icontains=search_value))

    order_by_field_dict = {
        "user_email": "owner__email",
        "user_phone": "owner__phone",
        "id": "id",
        "name": "name",
        "user_fio": "user_fio",
        "type_hotel": "hotel_type",
        "stars": "stars",
        "rating": "rating_stat",
        "percentage": "percentage",
        "created_at": "created_at",
        "updated_at": "updated_at"
    }

    # Преобразуем поле сортировки, если оно есть в списке соответствия
    if order_by_field_dict.get(order_by_field):
        order_by_field = order_by_field_dict[order_by_field]

    if order_by_field == "user_fio":
        valid_hotels = valid_hotels.annotate(
            owner_fio=Lower(F('owner__get_FIO'))).order_by('owner_fio')
    else:
        valid_hotels = valid_hotels.order_by(order_by_field)

    hotels = valid_hotels.select_related('owner').prefetch_related('service')

    content = {
        "draw": params.get("draw", 1),
        "recordsTotal": recordsTotal,
        "recordsFiltered": valid_hotels.count(),
        "data": [],
    }

    page_number = int(params.get('start', 0))
    page_length = int(params.get('length', 10))

    all_data = []

    for hotel in hotels[page_number:page_number+page_length]:
        owner = hotel.owner

        owner_fio = owner.get_FIO() if owner else ""
        owner_id = owner.id if owner else None

        if not hasattr(owner, "additional_info"):
            continue

        representative_fio = owner.additional_info.get("representative_fio")
        representative_phone = owner.additional_info.get(
            "representative_phone")
        channel_manager = owner.additional_info.get("channel_manager")
        moderation_user = ""

        is_report = False
        additional_info = hotel.additional_info
        if additional_info.get("report_from_moder"):
            if additional_info["report_from_moder"].get("moderation") and additional_info["report_from_moder"]["moderation"]["user"] != None:
                is_report = True

            if additional_info["report_from_moder"].get("registration") and additional_info["report_from_moder"]["registration"]["user"] != None:
                is_report = True

            if additional_info["report_from_moder"].get("transfer") and additional_info["report_from_moder"]["transfer"]["user"] != None:
                is_report = True

        if additional_info.get("moderation_user") and hotel.get_status()["code"] in ["is_pending", "active"]:
            moderation_user = User.objects.get(
                id=additional_info.get("moderation_user")).get_FIO()
            moderation_user = f"({moderation_user})"

        moder_fio = ""
        moderworks_first: ModerWork = hotel.moderworks.all().first()
        if moderworks_first:
            moder_fio = moderworks_first.moder.get_FIO()

        hotel_dict = model_to_dict(hotel)

        docs = additional_info.get("docs", {})

        data_hotel = {
            "DT_RowAttr": {
                "data-user-id": owner_id,
                "data-user-representative_fio": representative_fio,
                "data-user-representative_phone": representative_phone,
                "data-user-channel_manager": channel_manager,
                "data-hotel-id": hotel.id,
                "data-given_to_man": hotel.additional_info.get("given_to_man"),
                "data-is_report": is_report,
                "data-created_by_parser": hotel.additional_info.get("created_by_parser"),
                "data-address": hotel.adrress_hotel.short() if hasattr(hotel, "adrress_hotel") else "",
                "data-coordinates": hotel.adrress_hotel.coordinates if hasattr(hotel, "adrress_hotel") else "",
                "data-hotel_name": hotel.name,
                "data-hotel_enable": hotel.enable,
            },
            "user_email": owner.email if owner else "",
            "user_phone": owner.phone if owner else "",
            "id": hotel.id,
            "name": {
                "id": hotel.id,
                "text": hotel.name,
                "status_text": hotel.get_status()['text'],
                "status_color": hotel.get_status()['color'],
                "city": hotel.adrress_hotel.city if hasattr(hotel, "adrress_hotel") else "",
                "moderation_user": moderation_user
            },
            "user": {
                "fio": owner_fio,
                "color": "#0fdd34" if hotel.additional_info.get("given_to_man") else "#ff0e0e",
                "phone": {
                    "value": owner.phone,
                    "active": owner.active_phone,
                },
                "email": {
                    "value": owner.email,
                    "active": owner.active_email,
                },
                "moder_fio": f"В работе ({moder_fio})" if len(moder_fio) > 0 else "",
            },
            "type_hotel": hotel.get_hotel_type(),
            "stars": hotel.stars,
            "service": [service.name for service in hotel.service.all()],
            "meal": {
                "breakfast": hotel.breakfast,
                "lunch": hotel.lunch,
                "dinner": hotel.dinner,
            },
            "rating": {
                "stat": hotel.rating_stat,
                "amount": hotel.rating_amount,
            },
            "percentage": hotel.percentage,
            "booking": {
                "instant_booking": "Да" if hotel.instant_booking else "Нет",
                "date_when_you_start_receiving_guests": hotel.date_when_you_start_receiving_guests,
                "minimum_days_before_arrival": hotel.minimum_days_before_arrival,
                "minimum_days_of_stay": hotel.minimum_days_of_stay,
            },
            "permissions": {
                "allowed_child": hotel.allowed_child,
                "allowed_animal": hotel.allowed_animal,
                "allowed_smoking": hotel.allowed_smoking,
                "allowed_party": hotel.allowed_party,
            },
            "updated_at": (hotel.updated_at + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M:%S"),
            "created_at": (hotel.created_at + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M:%S"),
            "docs": docs,
        }

        if hotel.additional_info.get("given_to_man") == False:
            if hotel.additional_info.get("user"):
                data_hotel["DT_RowAttr"]["data-user-login"] = hotel.additional_info["user"]["login"]
                data_hotel["DT_RowAttr"]["data-user-password"] = hotel.additional_info["user"]["password"]

        all_data.append(data_hotel)

    content["data"] = all_data

    return JsonResponse(content)


@moder_admin_owner_required
def ajax_moderation_hotel_disallow(request):
    comment = request.POST.get("comment")
    hotel_id = request.POST.get("hotel_id")

    hotel = Hotel.objects.get(id=hotel_id)

    owner = hotel.owner

    hotel.is_pending = True
    hotel.additional_info["banned"] = comment
    hotel.additional_info["moderation_user"] = request.user.id
    hotel.save()

    chat = Chat.get_personal_chat(owner)

    chat.add_info_message("moderation.status", {
        "success": False,
        "comment": comment,
    })

    Notification.new(owner, "Отель не одобрен", comment,
                     f"/chats/?chat={chat.id}chat_type=techsupport", True, True)

    return JsonResponse({"status": "Ok", "hotel_name": hotel.name})


@moder_admin_owner_required
def ajax_moderation_hotel_allow(request):
    comment = request.POST.get("comment")
    hotel_id = request.POST.get("hotel_id")

    hotel = Hotel.objects.get(id=hotel_id)
    hotel.additional_info["moderation_is_pending_user"] = request.user.id
    hotel.additional_info["moderation_is_pending_date"] = datetime.datetime.now(
    ).strftime("%d.%m.%Y %H:%M")
    hotel.additional_info["moderation_user"] = request.user.id

    owner = hotel.owner

    if hotel.additional_info.get("banned"):
        del hotel.additional_info["banned"]

    chat = Chat.get_personal_chat(owner)

    chat.add_info_message("moderation.status", {
        "success": True,
        "comment": comment,
    })

    Notification.new(owner, "Отель одобрен", comment,
                     f"/chats/?chat={chat.id}chat_type=techsupport", True, True)

    hotel.is_pending = False
    hotel.save()

    return JsonResponse({"status": "Ok", "hotel_name": hotel.name})


@moder_admin_owner_required
def ajax_moderation_hotel_document_allow(request):
    doc_id = request.POST.get("doc_id")
    hotel_id = request.POST.get("hotel_id")

    hotel = Hotel.objects.get(id=hotel_id)

    distribution_rules = {
        "doc_1_1": ["doc_1", 0],
        "doc_1_2": ["doc_1", 1],
        "doc_1_3": ["doc_1", 2],
        "doc_2_1": ["doc_2", 0],
        "doc_2_2": ["doc_2", 1],
        "doc_2_3": ["doc_2", 2],
        "doc_3_1": ["doc_3", 0],
        "doc_3_2": ["doc_3", 1],
    }

    doc_code, doc_index = distribution_rules[doc_id]

    hotel.additional_info["docs"][doc_code][doc_index]["checked"] = {
        "date": datetime.datetime.now().timestamp(),
        "user": request.user.id,
        "note": None,
        "status": True,
    }
    hotel.save()

    return JsonResponse({"status": "Ok"})


def dict_to_html(data, indent_level=0):
    indent = "  " * indent_level
    html = f"{indent}<ul>\\n"
    for key, value in data.items():
        html += f"{indent}  <li>{key}: "
        if isinstance(value, dict):
            html += "\\n" + dict_to_html(value, indent_level+1) + indent
        else:
            html += f"{value}"
        html += "</li>\\n"
    html += f"{indent}</ul>\\n"
    return html


@moder_admin_owner_required
def page_list_users(request):
    return render(request, 'my_admin/list_user.html')


@moder_admin_owner_required
def ajax_list_user(request):
    params = request.POST.dict()

    user_type = params.get('type', 'all')
    search_value: str = params.get('search[value]', '')

    search_value = search_value.strip()

    order_by_field = 'id'
    if params.get('order[0][dir]') == 'desc':
        order_by_field = '-' + params.get('order[0][name]', 'id')
    else:
        order_by_field = params.get('order[0][name]', 'id')

    user_admin: User = request.user

    list_type_user = ["hotel", "client"]
    if user_admin.user_type == "owner":
        list_type_user = ["hotel", "client", "moder", "admin", "owner"]
    elif user_admin.additional_info.get("permission"):
        if "login_to_moderators" in user_admin.additional_info.get("permission", []):
            list_type_user = ["hotel", "client", "moder"]

    recordsTotal = len(User.objects.filter(user_type__in=list_type_user))

    if user_type == "client":
        valid_user = User.objects.filter(user_type="client")

    elif user_type == "hotel":
        valid_user = User.objects.filter(user_type="hotel")

    else:
        valid_user = User.objects.filter(user_type__in=list_type_user)

    if search_value:
        valid_user = valid_user.filter(Q(id__icontains=search_value) | Q(email__icontains=search_value) | Q(username__icontains=search_value) | Q(
            lastname__icontains=search_value) | Q(middlename__icontains=search_value) | Q(phone__icontains=search_value) | Q(hotels__name__icontains=search_value))

    order_by_field_dict = {
        "id": "date_joined",
        "at": "date_joined",
    }

    # Преобразуем поле сортировки, если оно есть в списке соответствия
    if order_by_field_dict.get(order_by_field):
        order_by_field = order_by_field_dict[order_by_field]

    if order_by_field == "fio":
        valid_user = valid_user.annotate(
            owner_fio=Lower(F('get_FIO'))).order_by('fio')
    else:
        valid_user = valid_user.order_by(order_by_field)

    users = valid_user

    users = users.distinct()

    page_number = int(params.get('start', 0))
    page_length = int(params.get('length', 10))

    all_data = []

    content = {
        "draw": params.get("draw", 1),
        "recordsTotal": recordsTotal,
        "recordsFiltered": len(users),
        "data": [],
    }

    if page_length > 0:
        users = users[page_number:page_number+page_length]

    for user in users:
        user: User
        hotels = Hotel.objects.filter(owner=user, is_delete=False)

        hotels_param = []
        for hotel in hotels:
            hotel: Hotel
            data_hotel = {}
            data_hotel = model_to_dict(hotel, exclude=["service"])
            if hotel.descriptions:
                data_hotel["descriptions"] = hotel.descriptions if len(
                    hotel.descriptions) <= 60 else hotel.descriptions[0:60] + "..."
            data_hotel["type_hotel"] = hotel.get_type_hotel_display()
            data_hotel["address"] = hotel.adrress_hotel.short(
            ) if hasattr(hotel, "adrress_hotel") else ""
            data_hotel["coordinates"] = hotel.adrress_hotel.coordinates if hasattr(
                hotel, "adrress_hotel") else ""

            if hotel.additional_info.get("user"):
                data_hotel["access"] = hotel.additional_info["user"]

            if hotel.is_delete:
                data_hotel["status_hotel"] = "Удалён"

            elif hotel.is_pending:
                data_hotel["status_hotel"] = "На модерации"

            elif not hotel.enable:
                data_hotel["status_hotel"] = "Выключен"

            else:
                data_hotel["status_hotel"] = "Активен"

            hotels_param.append(data_hotel)

        data_user = {
            "DT_RowAttr": {
                "data-user-id": user.id,
            },
            "id": {
                "id": user.id,
                "uid": user.uid,
            },
            "user_type": user.get_user_type_display(),
            "fio": user.get_FIO(),
            "phone": {
                "phone_1": {
                    "value": user.phone,
                    "active": user.active_phone,
                },
                "phone_2": {
                    "value": user.phone_2,
                    "active": user.active_phone_2,
                }
            },
            "email": {
                "value": user.email,
                "active": user.active_email,
            },
            "hotels": hotels_param,
            "at": {
                "create": (user.date_joined + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M:%S"),
                "last_login": (user.last_login + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M:%S"),
            },
        }

        if data_user["phone"]["phone_1"]["value"] == data_user["phone"]["phone_2"]["value"]:
            data_user["phone"]["phone_2"] = {
                "value": "",
                "active": "",
            }

        all_data.append(data_user)

    content["data"] = all_data

    return JsonResponse(content)


@moder_admin_owner_required
def page_list_admin(request):
    return render(request, 'my_admin/list_admin.html')


@moder_admin_owner_required
def ajax_list_admin(request):
    params = request.POST.dict()

    user_type = params.get('type', 'all')
    search_value: str = params.get('search[value]', '')

    search_value = search_value.strip()

    order_by_field = 'id'
    if params.get('order[0][dir]') == 'desc':
        order_by_field = '-' + params.get('order[0][name]', 'id')
    else:
        order_by_field = params.get('order[0][name]', 'id')

    user_admin: User = request.user

    list_type_user = ["admin", "moder"]
    if user_admin.user_type == "owner":
        list_type_user = ["moder", "admin", "owner"]

    users = User.objects.filter(user_type__in=list_type_user)

    users = users.distinct()

    page_number = int(params.get('start', 0))
    page_length = int(params.get('length', 10))

    all_data = []

    content = {
        "draw": params.get("draw", 1),
        "recordsTotal": len(users),
        "recordsFiltered": len(users),
        "data": [],
    }

    if page_length > 0:
        users = users[page_number:page_number+page_length]

    for user in users:
        user: User

        data_user = {
            "DT_RowAttr": {
                "data-user-id": user.id,
            },
            "id": {
                "id": user.id,
                "uid": user.uid,
            },
            "user_type": user.get_user_type_display(),
            "fio": user.get_FIO(),
            "moder_works":
                [
                    {
                        "id": obj.id,
                        "user": {
                            "id": obj.user.id,
                            "fio": obj.user.get_FIO(),
                        }
                    }
                    for obj in user.moderworks.all()
            ]
        }

        all_data.append(data_user)

    content["data"] = all_data

    return JsonResponse(content)


def ajax_auth_user(request):
    user_id = request.GET.get("user_id")
    access_token = request.COOKIES.get('access_token')

    try:
        if user_id:
            user: User = User.objects.get(id=user_id)
        else:
            if access_token:
                all_user_admin = User.objects.filter(
                    user_type__in=["admin", "moder", "owner"])

                for user in all_user_admin:
                    # Проверяется что это админ
                    if user.check_access_token(access_token):
                        logout(request)
                        login(request, user)

                        response = HttpResponseRedirect(
                            reverse("admin.page.list.user"))
                        response.delete_cookie('access_token')
                        return response
                else:
                    response = HttpResponseRedirect(reverse("profile_v2"))
                    return response

        if user:
            if request.user.is_admin or request.user.user_type in ["admin", "moder", "owner"]:
                new_access_token = request.user.get_access_token()

                if user.user_type in ["owner"]:
                    response = HttpResponseRedirect(
                        reverse("admin.page.list.user"))
                    return response

                valid = True

                if user.user_type in ["admin", "moder"]:
                    if request.user.additional_info.get("permission"):
                        if not("supermoderator" in request.user.additional_info["permission"]):
                            valid = False
                    else:
                        valid = False

                if not valid:
                    response = HttpResponseRedirect(
                        reverse("admin.page.list.user"))
                    return response

                logout(request)
                login(request, user)

                response = HttpResponseRedirect(reverse("profile_v2"))
                response.set_cookie(
                    'access_token', new_access_token, max_age=3600)
                return response

            else:
                response = HttpResponseRedirect(reverse("profile_v2"))
                return response

        else:
            response = HttpResponseRedirect(reverse("profile_v2"))
            return response
    except:
        response = HttpResponseRedirect(reverse("profile_v2"))
        return response


@moder_admin_owner_required
def redirect_open_user_chat(request):
    user_id = request.GET.get("user_id")
    user = User.objects.get(id=user_id)

    chat = Chat.get_personal_chat(user)

    return redirect(f"/admin/page/ts/chat/?chat={chat.id}")


def page_user_financial_transactions(request):
    user_id = request.GET.get("user_id")
    user = User.objects.get(id=user_id)

    content = {
        "FOs": FinancialOperation.objects.filter(user=user)
    }

    return render(request, 'my_admin/user_financial_transactions.html', content)


@moder_admin_owner_required
def ajax_bonus_add(request):
    user_id = request.POST.get("user_id")
    count = request.POST.get("count")

    user = User.objects.get(id=user_id)

    Bonus_rubles.add(user, int(count))
    FinancialOperation.new(user, int(count), True, "admin", f"Админ")

    return HttpResponse("OK", status=200)


@moder_admin_owner_required
def ajax_bonus_deny(request):
    user_id = request.POST.get("user_id")
    count = request.POST.get("count")

    user = User.objects.get(id=user_id)

    Bonus_rubles.deny(user, int(count))
    FinancialOperation.new(user, -int(count), True, "admin", f"Админ")

    return HttpResponse("OK", status=200)


@moder_admin_owner_required
def ajax_get_access_token(request):
    user: User = request.user.normal()

    e_access_token = user.get_access_token()

    content = {
        "e_access_token": e_access_token,
        "access_token": user.access_token,
        "key": user.access_token_key.decode(),
    }

    return JsonResponse(content)


@moder_admin_owner_required
def ajax_list_bookings(request: HttpRequest):
    params = dict(request.POST.items())

    # Фильтер на Статус брони
    booking_status = params["booking_status"]
    if booking_status == "all":
        booking_jq = Booking.objects.filter(~Q(status="close"))
    else:
        booking_jq = Booking.objects.filter(status=booking_status)

    all_data = []

    for booking in booking_jq:
        booking: Booking
        user: User = booking.booking_user
        if not user:
            continue

        if booking.booked_room == None or booking.booked_room.category == None or booking.booked_room.category.hotel == None:
            continue

        hotel: Hotel = booking.booked_room.category.hotel

        # Фильтер на Статус отмены
        booking_cancellation_status = params["booking_cancellation_status"]

        if booking.hotel_cancellation == None:
            if booking.param.get("cancelled_admin"):
                hotel_cancellation = User.objects.filter(
                    id=booking.param.get("cancelled_admin")).first().get_FIO()
            else:
                hotel_cancellation = "API"
        else:
            hotel_cancellation = "Отель" if booking.hotel_cancellation == True else "Клиент"

        if booking_status == "cancelled":
            if booking_cancellation_status == "general":
                if not(hotel_cancellation in ["Отель", "Клиент"]):
                    continue

            elif booking_cancellation_status == "auto":
                if not(hotel_cancellation in ["API"]):
                    continue

        # Фильтер на Тип отеля
        hotel_type = params["hotel_type"]
        created_by_parser = hotel.additional_info.get("created_by_parser")
        given_to_man = hotel.additional_info.get("given_to_man")

        if created_by_parser == None:
            created_by_parser = False

        valid = False

        if hotel_type == "all":
            valid = True

        if hotel_type == "full":
            if not created_by_parser:
                valid = True

        if hotel_type == "parser_hotel_with_owner":
            if created_by_parser == True and given_to_man == True:
                valid = True

        if hotel_type == "parser_hotel_without_owner":
            if created_by_parser == True and given_to_man == False:
                valid = True

        if not valid:
            continue

        # Фильтер на Статус отеля
        hotel_status = params["hotel_status"]
        hotel_enable = hotel.enable
        hotel_is_pending = hotel.is_pending
        hotel_is_delete = hotel.is_delete

        if hotel_status == "active":
            if not (hotel_enable and not hotel_is_pending and not hotel_is_delete):
                continue

        elif hotel_status == "on_moderation":
            if not (hotel_enable and hotel_is_pending and not hotel_is_delete):
                continue

        children_ages = list(
            map(str, list(booking.children_ages.all().values_list("age", flat=True))))

        status_text = booking.get_status_display()

        if booking.status == "cancelled":
            status_text = booking.get_status_display() + \
                f" ({hotel_cancellation})"

        hotel_user_login = hotel.additional_info["user"].get(
            "login") if hotel.additional_info.get("user") else None
        hotel_user_password = hotel.additional_info["user"].get(
            "password") if hotel.additional_info.get("user") else None


        data_user = {
            "DT_RowAttr": {
                "data-user-id": user.id,
                "data-user-hotel-id": hotel.owner.id,
                "data-response-to-cancellation": "Имеет ответ" if booking.response_to_cancellation else "Не отвечено",
                "data-hotel-cancellation": booking.hotel_cancellation,
                "data-hotel-cancellation-text": hotel_cancellation,
                "data-hotel-given_to_man": given_to_man,
                "data-booking-payment_status": booking.payment_status,
                "data-booking-id": booking.id,
                "data-hotel-id": hotel.id,
                "data-hotel-address": hotel.adrress_hotel.short() if hasattr(hotel, "adrress_hotel") else "",
                "data-hotel-owner-login": hotel_user_login,
                "data-hotel-owner-password": hotel_user_password,
            },
            "additional_info": hotel.additional_info,
            "created_at": (booking.created_at + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M"),
            "created_at_obj": booking.created_at,
            "id": {
                "id": booking.id,
                "full_booking_html": f"""
                ID: {booking.id},<br>
                Категория: {booking.booked_room.category.name},<br>
                Номер: {booking.booked_room.room_number},<br>
                Отель: {hotel.name},<br>
                Начало бронирования: {(booking.start_date_time + datetime.timedelta(hours=3)).strftime('%d.%m.%Y')},<br>
                Окончание бронирования: {(booking.end_date_time + datetime.timedelta(hours=3)).strftime('%d.%m.%Y')},<br>
                Количество взрослых: {booking.adults_count},<br>
                Количество детей: {len(booking.children_ages.all())},<br>
                За бронь: {booking.site_price},<br>
                За проживание: {booking.hotel_price},<br>
                Возраст детей: {", ".join(children_ages) if len(children_ages) > 0 else "Нет"},<br>
                Статус: {booking.get_status_display()},<br>
                Статус оплаты: {booking.get_payment_status_display()},<br>
                Дата и время создания брони: {(booking.created_at + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")},<br>
                """
            },
            "user_fio": user.get_FIO(),
            "hotel": hotel.name,
            "status": status_text,
            "days": (booking.end_date_time.date() - booking.start_date_time.date()).days,
            "start": (booking.start_date_time + datetime.timedelta(hours=3)).strftime('%d.%m.%Y'),
            "start_obj": booking.start_date_time + datetime.timedelta(hours=3),
            "end": (booking.end_date_time + datetime.timedelta(hours=3)).strftime('%d.%m.%Y'),
            "end_obj": booking.end_date_time + datetime.timedelta(hours=3),
            "price_site": booking.site_price,
            "price_hotel": booking.param.get("prices", {}).get("room_full", "(Нет)"),
        }

        data_user["id"]["full_booking_html"]

        all_data.append(data_user)

    start_booking_id = int(params["start"])
    length_booking_list = int(params["length"])

    if params.get("search[value]") != "":
        keys_dict = {
            "full": [],
            "start": ["hotel", "id__id", "user_fio"],
            "substr": []
        }
        all_data = list(filter(lambda obj: search_values(
            obj, keys_dict, params["search[value]"]), all_data))

    # Сортировка (Она должна быть перед вырезом так как нужно сортировать весь список и так можно через свойства которые передаются это делать)

    order_id = None
    order_dir = None
    order_name = None

    order_id = params["order[0][column]"]
    order_dir = params["order[0][dir]"]

    for key, value in params.items():
        if key == f"columns[{order_id}][name]":
            order_name = value

    if order_name:
        dir_order = False if order_dir == "asc" else True

        if order_name in ["user_fio", "hotel"]:
            all_data = sorted(all_data, key=lambda obj: filter_alphabet(
                obj[order_name]), reverse=dir_order)

        if order_name in ["days", "price_site", "price_hotel"]:
            all_data = sorted(
                all_data, key=lambda obj: obj[order_name], reverse=dir_order)

        # Сортировка по дате
        if order_name in ["start"]:
            all_data = sorted(
                all_data, key=lambda obj: obj["start_obj"], reverse=dir_order)

        if order_name in ["end"]:
            all_data = sorted(
                all_data, key=lambda obj: obj["end_obj"], reverse=dir_order)

        if order_name in ["created_at"]:
            all_data = sorted(
                all_data, key=lambda obj: obj["created_at_obj"], reverse=dir_order)

        if order_name in ["id"]:
            all_data = sorted(
                all_data, key=lambda obj: obj["created_at_obj"], reverse=not dir_order)

    bookings = all_data[start_booking_id:start_booking_id+length_booking_list]

    content = {
        "draw": params["draw"],
        "recordsTotal": len(all_data),
        "recordsFiltered": len(all_data),
        "data": bookings,
    }

    # формируем JsonResponse с параметрами форматирования
    return JsonResponse(content)


alphabet = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяabcdefghijklmnopqrstuvwxyz"


def filter_alphabet(obj: str):
    text = obj.lower()
    text = re.sub(r'[^a-zа-яё]', '', text)
    result = [alphabet.index(s) for s in text]
    return result


@moder_admin_owner_required
def page_list_bookings(request):

    content = {
    }

    # формируем JsonResponse с параметрами форматирования
    return render(request, 'my_admin/list_booking.html', content)


@moder_admin_owner_required
def ajax_booking_cancellation(request):
    booking_id = request.POST.get("booking_id")
    percent = int(request.POST.get("percent"))
    percent /= 100
    booking: Booking = Booking.objects.get(id=booking_id)

    user = booking.booking_user

    bonus_return = booking.param["prices"]["bonus"]["value"]
    balanc_return = booking.param["prices"]["balanc"]["value"]
    card_return = booking.param["prices"]["card"]["value"]

    Bonus_rubles.add(user, round(bonus_return * percent),
                     text="Отмена администратором")

    add_rbal = round(balanc_return * percent)
    add_rbal += round(card_return * percent)

    user.rbal = add_rbal
    user.save()

    FinancialOperation.new(user, round(bonus_return * percent),
                           True, "admin", "Отмена администратором")
    FinancialOperation.new(user, add_rbal, False,
                           "admin", "Отмена администратором")

    booking.status = "cancelled"
    booking.param["cancelled_admin"] = request.user.id
    booking.save()

    return JsonResponse({"status": "Ok"})


@moder_admin_owner_required
def ajax_booking_mark_as_answered(request):
    booking_id = request.POST.get("booking_id")

    booking: Booking = Booking.objects.get(id=booking_id)
    booking.response_to_cancellation = True
    booking.save()

    return JsonResponse({"status": "Ok"})


@moder_admin_owner_required
def page_statistics(request):
    all_booking = Booking.objects.filter(~Q(status="close"))

    # Создаем список дат
    dates = {}
    start_date = datetime.datetime.now()
    for i in range(365):
        # замена даты на месяц и год в русском формате
        month_str = start_date.strftime('%m.%Y')
        dates[month_str] = {'sum': 0, 'count': 0}
        start_date += datetime.timedelta(days=-1)

    # Итерируемся по всем объектам броней и обновляем значения в словаре 'dates'
    for booking in all_booking:
        booking: Booking
        date_str = booking.created_at.strftime('%m.%Y')
        dates[date_str]['sum'] += booking.site_price
        dates[date_str]['count'] += 1

    dates = dict(reversed(list(dates.items())))

    content = {
        "total_spent": sum(all_booking.filter(Q(payment_status="site_paid")).values_list("site_price", flat=True)),
        "len_booking": all_booking.count(),
        "len_hotel": Hotel.objects.filter(enable=True, is_delete=False).count(),
        "bookings": {
            "Новое": all_booking.filter(status="new").count(),
            "Подтверждено": all_booking.filter(status="verified").count(),
            "Заселено": all_booking.filter(status="settled").count(),
            "Оставлено": all_booking.filter(status="left").count(),
            "Отменено": all_booking.filter(status="cancelled").count(),
        },
        "bookings_and_price": dates,
    }

    return render(request, 'my_admin/statistics_site.html', content)


@moder_admin_owner_required
def page_user_new(request):

    return render(request, 'my_admin/user_new.html')


@moder_admin_owner_required
def ajax_user_new(request):
    admin: User = request.user.normal()
    user_type = request.GET.get("type")

    content = {}

    if user_type == "hotel_user":
        r_login = "h" + str(random.randint(100000000, 999999999))
        r_password = generate_password(15)
        r_email = f"{r_login}@gmail.ru"

        content = {
            "user":
            {
                "login": r_login,
                "password": r_password,
                "email": r_email
            }
        }

        user: User = User.objects.create_user(
            username=r_login,
            lastname=r_login,
            middlename=r_login,
            email=r_email,
            login=r_login,
            password=r_password,
            gender="Мужской",
            phone="+12345",
        )

        user.lastname = ""
        user.middlename = ""
        user.phone = ""
        user.user_type = "hotel"
        user.save()

        chat = Chat.get_personal_chat(user)

        Notification.new(user,
                         "Добро пожаловать партнер, на сайт turgorodok.ru",
                         "За объяснениями устройства сайта вы можете зайти в чат техподдержки или нажат на это уведомление",
                        f"/chats/?chat={chat.id}chat_type=techsupport", True, True)

    return JsonResponse(content)


@moder_admin_owner_required
def page_hotel_add(request):
    return render(request, 'my_admin/hotel_add.html')


@moder_admin_owner_required
def page_hotel_add_multi(request):
    return render(request, 'my_admin/hotel_add_multi.html')


@moder_admin_owner_required
def page_list_ownerless_hotel(request):

    hotels = Hotel.objects.filter(Q(additional_info__created_by_parser=True))

    content = {
        "hotels": hotels,
    }

    hotels_list = hotels.values_list()

    return render(request, 'my_admin/ownerless_hotel.html', content)


@moder_admin_owner_required
def page_moving_hotel(request):

    user_select_id = request.GET.get("user")

    if not user_select_id:
        raise ValueError("Неправильные параметры")

    user_select = User.objects.get(id=user_select_id)

    content = {
        "user_select": model_to_dict(user_select),
        "places": Place.get_list_mini(),
    }

    return render(request, 'my_admin/moving_the_hotel.html', content)


@moder_admin_owner_required
@supermoderator_or_owner
def ajax_moving_hotel_run(request: HttpRequest):
    user_id = request.POST.get("user")
    hotel_ids = request.POST.getlist("hotels[]")

    user = User.objects.get(id=user_id)

    if user.user_type in ["admin", "moder", "owner"]:
        return render(request, 'error_page.html', {'message': "Недостаточно прав, чтобы передать этому пользователю объекты размещения", "status": 403}, status=403)

    login = user.login
    pawword = user.additional_info.get("password", None)

    hotels = Hotel.objects.filter(id__in=hotel_ids)
    for hotel in hotels:

        if not pawword:
            if hotel.additional_info.get("user") and hotel.additional_info["user"].get("pawword"):
                pawword = hotel.additional_info["user"]["pawword"]

        hotel.owner = user

        if (pawword):
            hotel.additional_info["user"]["pawword"] = pawword
            user.additional_info["password"] = user.additional_info.get(
                "password")

        user.save()

        hotel.save()

    content = {
        "result": "ok",
        "request": {
            "user_id": user_id,
            "hotel_ids": hotel_ids,
        }
    }

    return JsonResponse(content)


@moder_admin_owner_required
def page_moderator_office(request):

    content = {
        "places": Place.get_list_mini(),
    }

    return render(request, 'my_admin/moderator_office.html', content)


@moder_admin_owner_required
def ajax_add_an_entry_moder_work(request):

    user_id = request.POST.get("user_id")
    user = User.objects.get(id=user_id)
    if ModerWork.objects.filter(user=user).exclude():
        return JsonResponse({
            "status": "error",
            "error_text": "Пользователь занят другим модератором"
        })

    else:
        mw = ModerWork.objects.create(
            user=user,
            moder=request.user,
        )

        for hotel in user.hotels.all():
            mw.hotels.add(hotel)

        mw.param = {"note": "", "status": "at_work"}
        mw.status = [{"value": "Взял в работу", "status": "active",
                      "datetime": round(datetime.datetime.now().timestamp())}]
        mw.save()

        return JsonResponse({
            "status": "ok",
            "url": "/admin/page/moderator_office/"
        })


def moderworks_to_dict(moderwork: ModerWork):
    obj = model_to_dict(moderwork)

    obj["contacts"] = [] if isinstance(
        obj["contacts"], dict) else obj["contacts"]
    obj["notes"] = [] if isinstance(obj["notes"], dict) else obj["notes"]
    obj["reminders"] = [] if isinstance(
        obj["reminders"], dict) else obj["reminders"]
    obj["status"] = [] if isinstance(obj["status"], dict) else obj["status"]
    obj["param"] = {"note": "", "status": "at_work"} if len(
        obj["param"].keys()) == 0 else obj["param"]

    user = User.objects.get(id=obj["user"])

    hotels = user.hotels.all()
    obj["hotels"] = []

    hotel_parser_owner = hotels.filter(
        Q(additional_info__created_by_parser=True)).first()

    obj["user"] = {
        "fio": {
            "full": user.get_FIO(),
            "username": user.username,
            "lastname": user.lastname,
            "middlename": user.middlename,
        },
        "phone": {
            "value": user.phone,
            "status": user.active_phone,
        },
        "email": {
            "value": user.email,
            "status": user.active_email,
        },
        "id": user.id,
    }

    # user_buff = User.objects.get(login="h642978360")
    # if user_buff.login == "h642978360":
    #     hotel_user_login = user_buff.login
    #     hotel_user_password = "FbWXvpuOsB33NLD"
    #     user_buff.additional_info["password"] = "FbWXvpuOsB33NLD"
    #     user_buff.set_password(hotel_user_password)
    #     user_buff.save()

    #     for hotel in user_buff.hotels.all():
    #         hotel.additional_info["user"]["login"] = hotel_user_login
    #         hotel.additional_info["user"]["password"] = hotel_user_password
    #         hotel.save()

    #     obj["user"]["login"] = hotel_user_login
    #     obj["user"]["password"] = hotel_user_password

    if hotel_parser_owner:
        hotel_user_login = hotel_parser_owner.additional_info["user"].get(
            "login") if hotel_parser_owner.additional_info.get("user") else None
        hotel_user_password = hotel_parser_owner.additional_info["user"].get(
            "password") if hotel_parser_owner.additional_info.get("user") else None

        # if user.login.find("h") == 0 and hotel_user_login != user.login:
        # hotel_user_login = user.login
        # hotel_user_password = generate_password(10)
        # user.set_password(hotel_user_password)
        # user.save()

        # for hotel in user.hotels.all():
        # hotel.additional_info["user"]["login"] = hotel_user_login
        # hotel.additional_info["user"]["password"] = hotel_user_password
        # hotel.save()

        obj["user"]["login"] = hotel_user_login
        obj["user"]["password"] = hotel_user_password

    for hotel in hotels:
        hotel: Hotel
        adrress: Address = hotel.adrress_hotel if hasattr(
            hotel, "adrress_hotel") else None
        hotel_obj = {
            "id": hotel.id,
            "name": hotel.name,
            "status": hotel.get_status(),
            "city": adrress.city if adrress else None,
            "enable": hotel.enable,
            "type": hotel.type_hotel,
            "address": model_to_dict(adrress, exclude=["hotel", "id"]) if adrress else {},
        }

        hotel_obj["address"]["short"] = adrress.short() if adrress else None

        obj["hotels"].append(hotel_obj)

    return obj


@moder_admin_owner_required
def ajax_moderator_office_get(request):

    content = {

    }
    content["moder_works"] = {}

    for work in [work for work in request.user.moderworks.all()]:
        obj = moderworks_to_dict(work)

        content["moder_works"][obj["id"]] = obj

    return JsonResponse(content)


@moder_admin_owner_required
def ajax_moderator_office_save(request):

    param = json.loads(request.body)

    moder_work = ModerWork.objects.get(id=param['id'])

    if moder_work.moder != request.user:
        return render(request, 'error_page.html', {'message': "Вы не имеете доступа к изменению этой записи", "status": 403}, status=403)

    # Обработчка записей

    current_time = round(datetime.datetime.now().timestamp())

    for obj in param["contacts"]:
        if "datetime" not in obj:
            obj["datetime"] = current_time
            obj["status"] = "active"

    for obj in param["notes"]:
        if "datetime" not in obj:
            obj["datetime"] = current_time
            obj["status"] = "active"

    for index_obj, obj in enumerate(param["reminders"]):
        if "date" in obj and "time" in obj:
            date = datetime.datetime.strptime(obj["date"], "%Y-%m-%d")
            time = datetime.datetime.strptime(obj["time"], "%H:%M")
            value = str(param['id']) + " - " + obj["value"]

            param["reminders"][index_obj] = {
                "value": value,
                "status": "active",
                "datetime": datetime.datetime.combine(date.date(), time.time()).timestamp()
            }

    for obj in param["status"]:
        if "datetime" not in obj:
            obj["datetime"] = current_time
            obj["status"] = "active"

    moder_work.param = param["param"]

    user = moder_work.user

    if param["user"].get("username"):
        user.username = param["user"]["username"]
        user.lastname = param["user"]["lastname"]
        user.middlename = param["user"]["middlename"]
        user.phone = param["user"]["phone"]
        user.email = param["user"]["email"]
        user.save()

    # Сохранение

    moder_work.contacts = param["contacts"]
    moder_work.notes = param["notes"]
    moder_work.reminders = param["reminders"]
    moder_work.status = param["status"]

    moder_work.save()

    # Получение для возрата

    obj = moderworks_to_dict(moder_work)

    content = {
        "status": 200,
        "obj": obj,
    }

    return JsonResponse(content)


@moder_admin_owner_required
def ajax_hotel_add(request):
    content = {}

    admin = request.user.normal()

    file = request.FILES['file']

    ph = json.loads(file.read())

    fun_add_hotel(ph, admin)

    return JsonResponse(content)


def read_json_files(directory):
    dates = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.json'):
                filepath = os.path.join(root, filename)
                with open(filepath) as json_file:
                    data = json.load(json_file)
                    dates.append(data)

    return dates


def hotel_add_multi():
    """
cd /var/www/www-root/data/www/turgorodok.ru/venv/
source bin/activate
python manage.py shell

from user.urls_views.views.admin import hotel_add_multi
hotel_add_multi()
    """

    # admin = request.user.normal()

    admin = User.objects.get(id=1)

    dates = read_json_files(
        "/var/www/www-root/data/www/turgorodok.ru/venv/static/hotels/")

    count_hotel = len(dates)
    print(f"Отелей: {count_hotel}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(fun_add_hotel, date, admin)
                   for date in dates]

    index = 0
    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
            print(f"[{index + 1} / {count_hotel}] {result['name_hotel']}")
        except Exception as e:
            tb_str = traceback.format_exception(type(e), e, e.__traceback__)
            print(f"[{index + 1} / {count_hotel}] Ошибка - {str(e)} - {''.join(tb_str)}")
            index += 1


def fun_add_hotel(ph, admin=None):
    other_content = {}

    type_hotel_list = [
        'Апарт-отель',
        'Апартаменты',
        'База отдыха',
        'Гостиница',
        'Бунгало',
        'Бутик-отель',
        'Вилла',
        'Глэмпинг',
        'Гостевой дом',
        'Жилое помещение',
        'Замок',
        'Кемпинг',
        'Курортный отель',
        'Меблированные комнаты',
        'Мини-отель',
        'Ночлег и завтрак (B&B)',
        'Отель',
        'Санаторий',
        'Ферма',
        'Хостел',
        'Частный дом',
        'Шале',
    ]

    hotel_name: str = ph["name_hotel"]
    hotel_title: str = ph["title"]
    hotel_type = None

    if Hotel.objects.filter(name=hotel_name).exists():
        print(f'[Уже есть] {ph["name_hotel"]}')
        return None

    for hotel_type_elem in Hotel.type_hotel_choices:
        if hotel_name.find(hotel_type_elem[1]) != -1:
            hotel_type = hotel_type_elem[0]
            break

    if hotel_type == None:
        for hotel_type_elem in Hotel.type_hotel_choices:
            if hotel_title.find(hotel_type_elem[1]) > -1:
                hotel_type = hotel_type_elem[0]
                break

    if hotel_type == None:
        hotel_type = "hotel"

    street: str = ph["address"]["street"]

    coordinates = f"{ph['coordinates']['latitude']}, {ph['coordinates']['longitude']}"

    address_param = {
        "city": ph["address"]["city"],
        "street": street.replace("улица", "").strip(),
        "house": ph["address"]["house"],
        "floor": None,
        "apartment": None,
        "coordinates": coordinates,
    }

    hotel_param = {
        "name": hotel_name,
        "descriptions": ph["description"],
        "type_hotel": hotel_type,
        "check_in_time": "12:00",
        "departure_time": "14:00",
        "stars": ph["stars_count"],
        "instant_booking": True,
        "date_when_you_start_receiving_guests": datetime.datetime.now(),
        "allowed_child": False,
        "allowed_animal": False,
        "allowed_smoking": False,
        "allowed_party": False,
        "minimum_days_before_arrival": 1,
        "minimum_days_of_stay": 1,
        "for_long_term_stays": 0,
        "for_long_term_stays_minimum_days_of_stay": 1,
        "cleaning_fee": 0,
        "additional_info": {
            "created_by_parser": True,
            "given_to_man": False,
        }
    }

    # Проверка на то что нету отеля с таким же названием, если есть использовать этот отель
    hotel = Hotel.objects.filter(name=ph["name_hotel"]).first()
    if not hotel:
        hotel = Hotel.objects.create(**hotel_param)

        address_param["hotel"] = hotel
        Address.objects.create(**address_param)

    ph_services = ph["services"]

    services_flat = []
    for category in ph_services:
        for service in ph_services[category]:
            services_flat.append(service)

    # Используйте итератор, чтобы создать список фильтров для каждой услуги
    filters = [Q(name__icontains=service) for service in services_flat]

    # Используйте оператор OR для объединения всех фильтров
    query = filters.pop()
    for f in filters:
        query |= f

    # Используйте фильтр, чтобы найти все объекты HService, которые соответствуют списку услуг, независимо от регистра
    services = HService.objects.filter(query)

    ph_imgs_hotel = ph["images"]

    for ph_img in ph_imgs_hotel:
        img = Img.new("hotel.hotel", hotel.id, None)
        is_save = img.save_image_from_url(ph_img["url"])
        if not is_save:
            img.delete()

    hotel.service.set(services)
    hotel.save()

    a_room_data_content = []

    ph_rcs = ph["rooms"]
    for index, ph_rc in enumerate(ph_rcs):
        type_rc_list = [
            (r"number", r"Номер"),
            (r"place_in_the_room", r"Место в номере"),
            (r"atelier", r"Студия"),
            (r"flat", r"Квартира"),
            (r"apartments", r"Апартаменты"),
            (r"house", r"Дом"),
            (r"cottage", r"Коттедж"),
            (r"villa", r"Вилла"),
        ]

        regex_bed = "(дву|одно|трех)спальная кровать|[0-9]+ (двуы|одно|трех)спальная кровать|отдельные кровати|[0-9]+ отдельные кровати"
        regex_capacity = "(одно|двух|трёх|четырёх|пяти)мест"

        # Название комнаты
        room_name = re.sub(r'\\b[a-zA-Z]+\\b', '*', ph_rc["name"]).lower()

        # Название кровати
        bed_name = re.search(regex_bed, room_name, flags=re.IGNORECASE)
        bed_name = bed_name.group() if bed_name else None

        beds_type = {
            "bed_1": 0,
            "bed_2": 0,
            "bed_1.5": 0
        }

        if bed_name:
            if bed_name.find("односпальная") != -1 or bed_name.find("отдельны"):
                count = 1
                try:
                    count = int(bed_name.split()[0])
                except ValueError:
                    pass

                beds_type["bed_1"] = count

            if bed_name.find("двуспальная") != -1:
                count = 1
                try:
                    count = int(bed_name.split()[0])
                except ValueError:
                    pass

                beds_type["bed_2"] = count

        type_rc = "number"

        for type_rc_list_elem in type_rc_list:
            if ph_rc["name"].find(type_rc_list_elem[1]) != -1:
                type_rc = type_rc_list_elem[0]
                break

        if ph_rc["price"] == 0:
            most_frequent_price = 4321
        else:
            prices = ph_rc["price"]

            prices_normal_list = [price["price"] /
                                  price["days"] for price in prices]

            counted_numbers = Counter(prices_normal_list)
            most_frequent_price = counted_numbers.most_common(1)[0][0]

        guests = ph_rc["visibility_area"]["guests"]["max"]

        if guests == None or guests == "null":
            guests = ph_rc["visibility_area"]["guests"]["min"]

        # Вместимость комнаты
        capacity_name = re.search(
            regex_capacity, room_name, flags=re.IGNORECASE)
        capacity_name = capacity_name.group() if capacity_name else None

        if capacity_name:
            if capacity_name == "одномест":
                guests = 1
            if capacity_name == "двухмест":
                guests = 2
            if capacity_name == "трёхмест":
                guests = 3
            if capacity_name == "четырёхмест":
                guests = 4
            if capacity_name == "пятимест":
                guests = 5

        room_param = {
            "offer_type": type_rc,
            "hotel": hotel,
            "square": round(float(ph_rc["size"])) if ph_rc.get("size") else 0,
            "name": ph_rc["name"],
            "price_base": most_frequent_price,
            "min_days": 1,
            "the_amount_of_the_security_deposit": "0",
            "count_room": math.ceil(guests / 2),
            "count_bedrooms": math.ceil(guests / 2),
            "max_adults": guests,
            "beds": beds_type,
            "enable": True,
        }

        a_room_data_content.append({"room_param": room_param, "ph_rc": ph_rc})

        rc = RCategory.objects.create(**room_param)
        Room.objects.create(category=rc, room_number="1")

        # Изображение номера
        ph_imgs = ph_rc["imgs"]

        for ph_img in ph_imgs:
            img = Img.new("hotel.rc", rc.id, None)
            is_save = img.save_image_from_url(ph_img["url"])
            if not is_save:
                img.delete()

        # Услуги номера
        ph_amenitie: list[str] = ph_rc["amenitie"]

        for amenitie in ph_amenitie:
            if amenitie.startswith(str(room_param['square'])):
                continue

            amenitie_obj = RService.objects.filter(name=amenitie).first()
            if amenitie_obj:
                rc.service.add(amenitie_obj)


    user = User.objects.get(id=ph["user"])

    hotel.additional_info["user"] = {
        "login": user.login,
        "password": user.additional_info.get("password", ""),
    }

    hotel.owner = user
    hotel.save()

    user.user_type = "hotel"
    user.save()

    print(f'{ph["name_hotel"]}')

    return {"name_hotel": ph["name_hotel"]}


def flatten_places(data, level=0):
    result = []
    if isinstance(data, dict):
        data = [data]

    for item in data:
        place: Place = item['place']
        auto_created = item['place'].auto_created
        active = item['place'].active

        type = item['place'].get_place_type_display()
        coordinates = item['place'].coordinates
        children = item['children']
        result.append({
            "id": place.id,
            'name': place.name,
            'slug': place.get_slug(),
            'type': type,
            'hotels': place.hotels,
            'count_hotels': place.hotels.all().count(),
            'coordinates': coordinates,
            'level': level,
            "auto_created": auto_created,
            "active": active,
        })
        if children:
            result.extend(flatten_places(children, level+1))
    return result


@moder_admin_owner_required
def page_list_place(request):
    places = Place.get_all_objects()

    places = flatten_places(places)

    no_place_hotels = Hotel.objects.filter(places__isnull=True)

    unknown_places = {}

    count_hotels = sum([place["count_hotels"] for place in places])

    for hotel in no_place_hotels:
        if hasattr(hotel, 'adrress_hotel'):
            city = hotel.adrress_hotel.city
        else:
            city = "Не указан"

        if city not in unknown_places:
            unknown_places[city] = {
                'name': city,
                "count_hotels": 0,
                "coords": [],
            }

        unknown_places[city]["count_hotels"] += 1
        if hasattr(hotel, "adrress_hotel") and hotel.adrress_hotel.coordinates:
            try:
                coordinates: str = hotel.adrress_hotel.coordinates.split(",")
                coord_1 = float(coordinates[0])
                coord_2 = float(coordinates[1])
                unknown_places[city]["coords"].append([coord_1, coord_2])
            except:
                pass

    for city in unknown_places.keys():
        place = unknown_places[city]
        place["coord_center"] = [0, 0]

        if len(place["coords"]) > 0:
            place["coord_center"] = [
                round(sum([cord[0] for cord in place["coords"]]) /
                      len(place["coords"]), 5),
                round(sum([cord[1] for cord in place["coords"]]) /
                      len(place["coords"]), 5),
            ]

    unknown_places = list(unknown_places.values())

    content = {
        "count_hotels_all": Hotel.objects.all().count(),
        "count_hotels": count_hotels,
        "count_hotels_no_place": Hotel.objects.all().count() - count_hotels,
        "places": places,
        "unknown_places": unknown_places,
    }

    # Place.process_unknown_places(unknown_places)

    return render(request, 'my_admin/list_place.html', content)


@moder_admin_owner_required
def ajax_list_place_add(request):
    params = request.POST.dict()

    name = params.get('name')
    name_en = params.get('name_en')
    coordinates = params.get('coordinates')
    slug = params.get('slug')
    parent = params.get('parent')

    if parent:
        parents = Place.objects.filter(name=parent)
        if len(parents) > 1:
            parents_str = ", ".join([place.id for place in parents])
            return JsonResponse({
                "error": f"Найдено больше одного родителя<br>{parents_str}"
            })

        if len(parents) > 0:
            parent = parents.first()

        if len(parents) == 0:
            return JsonResponse({
                "error": f"Не найден родитель"
            })
    else:
        parent = None

    place = Place.objects.create(
        name=name,
        en_name=name_en,
        slug=slug,
        coordinates=coordinates,
        place_type="other",
        parent=parent,
    )

    return JsonResponse({
        "success": f"Успешно создано новое место: {place.id}",
    })


@moder_admin_owner_required
def page_list_services(request):
    services_rooms_QS = RService.objects.all()
    services_rooms = []
    for service__rooms_qs in services_rooms_QS:
        name = service__rooms_qs.name
        count_room = RCategory.objects.filter(
            service=service__rooms_qs).count()
        count_hotel = Hotel.objects.filter(
            rcategory_hotel__service=service__rooms_qs).distinct().count()
        services_rooms.append({
            "name": name,
            "count": count_hotel,
            "count_2": count_room,
        })
    services_rooms = sorted(
        services_rooms, key=lambda item: item["count"], reverse=True)

    services_hotels_QS = HService.objects.all()
    services_hotels = []
    for service__hotel_qs in services_hotels_QS:
        name = service__hotel_qs.name
        count_hotel = Hotel.objects.filter(service=service__hotel_qs).count()
        services_hotels.append({
            "name": name,
            "count": count_hotel,
        })
    services_hotels = sorted(
        services_hotels, key=lambda item: item["count"], reverse=True)

    content = {
        "services_rooms": services_rooms,
        "services_hotels": services_hotels,
    }

    # Place.process_unknown_places(unknown_places)

    return render(request, 'my_admin/list_services.html', content)


@moder_admin_owner_required
def page_list_hotel(request):
    content = {
        "places": Place.get_list_mini(),
    }

    return render(request, 'my_admin/list_hotel.html', content)


def search_values(dict, keys_dict, search_string):
    for search_type in keys_dict.keys():
        keys_list = keys_dict[search_type]
        for key in keys_list:
            if "__" in key:
                nested_keys = key.split("__")
                nested_dict = dict.copy()
                for nested_key in nested_keys:
                    if nested_key in nested_dict:
                        nested_dict = nested_dict[nested_key]
                    else:
                        break
                if isinstance(nested_dict, str):
                    value = nested_dict
                elif isinstance(nested_dict, dict):
                    continue
                else:
                    value = str(nested_dict)
            elif key in dict.keys():
                value = dict[key]
            else:
                continue

            if isinstance(value, (int, float)):
                value = str(value)

            if search_type == "full":
                if search_string.lower() == value.lower():
                    return True
            elif search_type == "start":
                if value.lower().startswith(search_string.lower()):
                    return True
            elif search_type == "substr":
                if search_string.lower() in value.lower():
                    return True
    return False


@moder_admin_owner_required
@cache_page(60 * 5)
def ajax_list_hotel(request: HttpRequest):
    params = request.POST.dict()

    hotel_type = params.get('hotel_type', 'all')
    hotel_status = params.get('hotel_status', 'active')
    hotel_place_id = params.get('hotel_place', 'all')

    place_name = None

    if hotel_place_id not in ["all", "city"]:
        place = Place.objects.filter(id=hotel_place_id).first()
        if place:
            place_name = Place.objects.filter(id=hotel_place_id).first().name

    search_value = params.get('search[value]', '').strip()

    order_by_field = 'id'
    if params.get('order[0][dir]') == 'desc':
        order_by_field = '-' + params.get('order[0][name]', 'id')
    else:
        order_by_field = params.get('order[0][name]', 'id')

    valid_hotels = Hotel.objects.filter(is_delete=False)
    recordsTotal = len(valid_hotels)

    if hotel_type == "full":
        valid_hotels = valid_hotels.filter(
            Q(additional_info__created_by_parser=False))

    if hotel_type == "parser_hotel_with_owner":
        valid_hotels = valid_hotels.filter(
            Q(additional_info__created_by_parser=True, additional_info__given_to_man=True))

    if hotel_type == "parser_hotel_without_owner":
        valid_hotels = valid_hotels.filter(
            Q(additional_info__created_by_parser=True, additional_info__given_to_man=False))

    if hotel_status == 'active':
        valid_hotels = valid_hotels.filter(
            enable=True, is_pending=False, is_delete=False)
    elif hotel_status == 'on_moderation':
        valid_hotels = valid_hotels.filter(
            enable=True, is_pending=True, is_delete=False)
    elif hotel_status == 'on':
        valid_hotels = valid_hotels.filter(enable=True)
    elif hotel_status == 'off':
        valid_hotels = valid_hotels.filter(enable=False)

    if place_name:
        valid_hotels = valid_hotels.filter(
            enable=True, is_delete=False, adrress_hotel__city__icontains=place_name)

    if search_value:
        valid_hotels = valid_hotels.filter(Q(id__startswith=search_value) |
                                           Q(name__icontains=search_value) |
                                           Q(owner__email__icontains=search_value) |
                                           Q(owner__phone__icontains=search_value) |
                                           Q(owner__username__icontains=search_value) |
                                           Q(owner__lastname__icontains=search_value) |
                                           Q(owner__middlename__icontains=search_value)
                                           )

    order_by_field_dict = {
        "user_email": "owner__email",
        "user_phone": "owner__phone",
        "id": "id",
        "name": "name",
        "user_fio": "user_fio",
        "type_hotel": "hotel_type",
        "stars": "stars",
        "rating": "rating_stat",
        "percentage": "percentage",
        "at": "created_at"
    }

    # Преобразуем поле сортировки, если оно есть в списке соответствия
    if order_by_field_dict.get(order_by_field):
        order_by_field = order_by_field_dict[order_by_field]

    if order_by_field == "user_fio":
        valid_hotels = valid_hotels.annotate(
            owner_fio=Lower(F('owner__get_FIO'))).order_by('owner_fio')
    else:
        valid_hotels = valid_hotels.order_by(order_by_field)

    hotels = valid_hotels.select_related('owner').prefetch_related('service')

    content = {
        "draw": params.get("draw", 1),
        "recordsTotal": recordsTotal,
        "recordsFiltered": valid_hotels.count(),
        "place_name": place_name,
        "data": [],
    }

    page_number = int(params.get('start', 0))
    page_length = int(params.get('length', 10))

    all_data = []

    user_paser_login_parsord = {}

    for hotel in hotels[page_number:page_number+page_length]:
        owner = hotel.owner

        owner_fio = owner.get_FIO() if owner else ""
        owner_id = owner.id if owner else None

        if not hasattr(owner, "additional_info"):
            continue

        representative_fio = owner.additional_info.get("representative_fio")
        representative_phone = owner.additional_info.get(
            "representative_phone")
        channel_manager = owner.additional_info.get("channel_manager")

        is_report = False
        additional_info = hotel.additional_info
        if additional_info.get("report_from_moder"):
            if additional_info["report_from_moder"].get("moderation") and additional_info["report_from_moder"]["moderation"]["user"] != None:
                is_report = True

            if additional_info["report_from_moder"].get("registration") and additional_info["report_from_moder"]["registration"]["user"] != None:
                is_report = True

            if additional_info["report_from_moder"].get("transfer") and additional_info["report_from_moder"]["transfer"]["user"] != None:
                is_report = True

        hotel_dict = model_to_dict(hotel)

        status_code = ""
        status_text = ""

        if hotel.is_delete:
            status_text = "Удалён"
            status_code = "delete"
        elif hotel.is_pending:
            status_text = "На модерации"
            status_code = "is_pending"
        elif not hotel.enable:
            status_text = "Выключен"
            status_code = "not_enable"
        else:
            status_text = "Активен"
            status_code = "active"

        moder_fio = ""
        moderworks_first: ModerWork = hotel.moderworks.all().first()
        if moderworks_first:
            moder_fio = moderworks_first.moder.get_FIO()

        data_hotel = {
            "DT_RowAttr": {
                "data-user-id": owner_id,
                "data-user-representative_fio": representative_fio,
                "data-user-representative_phone": representative_phone,
                "data-user-channel_manager": channel_manager,
                "data-hotel-id": hotel.id,
                "data-given_to_man": hotel.additional_info.get("given_to_man"),
                "data-is_report": is_report,
                "data-created_by_parser": hotel.additional_info.get("created_by_parser"),
                "data-address": hotel.adrress_hotel.short() if hasattr(hotel, "adrress_hotel") else "",
                "data-coordinates": hotel.adrress_hotel.coordinates if hasattr(hotel, "adrress_hotel") else "",
                "data-hotel_name": hotel.name,
                "data-hotel_enable": hotel.enable,
            },
            "user_email": owner.email if owner else "",
            "user_phone": owner.phone if owner else "",
            "id": hotel.id,
            "name": {
                "id": hotel.id,
                "text": hotel.name,
            },
            "user_fio": {
                "fio": owner_fio,
                "color": "#0fdd34" if hotel.additional_info.get("given_to_man") else "#ff0e0e",
            },
            "type_hotel": hotel.get_hotel_type(),
            "status": {
                "code": status_code,
                "text": status_text,
            },
            "meal": {
                "breakfast": hotel.breakfast,
                "lunch": hotel.lunch,
                "dinner": hotel.dinner,
            },
            "rating": {
                "stat": hotel.rating_stat,
                "amount": hotel.rating_amount,
            },
            "percentage": hotel.percentage,
            "moder": moder_fio,
            "permissions": {
                "allowed_child": hotel.allowed_child,
                "allowed_animal": hotel.allowed_animal,
                "allowed_smoking": hotel.allowed_smoking,
                "allowed_party": hotel.allowed_party,
            },
            "at": {
                "updated_at":  (hotel.updated_at + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M:%S"),
                "created_at": (hotel.created_at + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M:%S"),
            }
        }

        if hotel.additional_info.get("given_to_man") == False:
            if hotel.additional_info.get("user"):

                data_hotel["DT_RowAttr"]["data-user-login"] = hotel.additional_info["user"]["login"]
                data_hotel["DT_RowAttr"]["data-user-password"] = hotel.additional_info["user"]["password"]

        all_data.append(data_hotel)

    content["data"] = all_data

    return JsonResponse(content)


@moder_admin_owner_required
def ajax_hotel_add_to_report(request: HttpRequest):
    params = dict(request.POST.items())

    hotel = Hotel.objects.get(id=params["hotel_id"])
    type = params["type"]

    now = datetime.datetime.now()
    date_time_str = now.strftime("%d.%m.%Y %H:%M:%S")

    if not hotel.additional_info.get("report_from_moder"):
        hotel.additional_info["report_from_moder"] = {
            "moderation": {
                "user": None,
                "create_at": None,
            },
            "registration": {
                "user": None,
                "create_at": None,
            },
            "transfer": {
                "user": None,
                "create_at": None,
            },
        }
        hotel.save()

    if hotel.additional_info["report_from_moder"]["moderation"]["user"] == None:
        if type == "moderation":
            hotel.additional_info["report_from_moder"]["moderation"]["user"] = request.user.id
            hotel.additional_info["report_from_moder"]["moderation"]["create_at"] = date_time_str

    if hotel.additional_info["report_from_moder"]["registration"]["user"] == None:
        if type == "registration":
            hotel.additional_info["report_from_moder"]["registration"]["user"] = request.user.id
            hotel.additional_info["report_from_moder"]["registration"]["create_at"] = date_time_str

    if hotel.additional_info["report_from_moder"]["transfer"]["user"] == None:
        if type == "transfer":
            hotel.additional_info["report_from_moder"]["transfer"]["user"] = request.user.id
            hotel.additional_info["report_from_moder"]["transfer"]["create_at"] = date_time_str
            hotel.additional_info["given_to_man"] = True

    hotel.save()

    content = {
        "status": "success",
    }

    # формируем JsonResponse с параметрами форматирования
    return JsonResponse(content)


@moder_admin_owner_required
def ajax_hotel_set_enable(request: HttpRequest):
    params = dict(request.POST.items())

    hotel = Hotel.objects.get(id=params["hotel_id"])
    type_enable = params["type_enable"]

    if type_enable == "enable_on":
        hotel.enable = True

    elif type_enable == "enable_off":
        hotel.enable = False

    hotel.save()

    content = {
        "status": "success",
        "type_enable": type_enable,
    }

    # формируем JsonResponse с параметрами форматирования
    return JsonResponse(content)


@moder_admin_owner_required
def page_list_moderator(request):
    content = {}

    return render(request, 'my_admin/list_moderator.html', content)


@moder_admin_owner_required
@supermoderator
def page_list_moderator(request):
    content = {}

    return render(request, 'my_admin/list_moderator.html', content)


@moder_admin_owner_required
@supermoderator
def page_list_moderator_detal_list(request):
    content = {}

    return render(request, 'my_admin/list_moderator_detal.html', content)


@moder_admin_owner_required
@supermoderator
def ajax_list_moderator(request):
    params = dict(request.POST.items())

    moder_jq = User.objects.filter(user_type__in=["moder", "admin", "owner"])

    all_data = []

    for moder in moder_jq:
        moderation_list = Hotel.objects.filter(
            Q(additional_info__report_from_moder__moderation__user=moder.id))
        registration_list = Hotel.objects.filter(
            Q(additional_info__report_from_moder__registration__user=moder.id))
        transfer_list = Hotel.objects.filter(
            Q(additional_info__report_from_moder__transfer__user=moder.id))

        moder: User
        fio = moder.get_FIO()
        id = moder.id

        data_hotel = {
            "DT_RowAttr": {
                "data-user-id": id,
            },
            "id": id,
            "fio": fio,
            "moderation_list": {
                "count": len(moderation_list),
                "url": reverse("admin.page.list.moderator_reports") + f"?moder_id={id}"
            },
            "registration_list": {
                "count": len(registration_list),
                "url": reverse("admin.page.list.moderator_reports") + f"?moder_id={id}"
            },
            "transfer_list": {
                "count": len(transfer_list),
                "url": reverse("admin.page.list.moderator_reports") + f"?moder_id={id}"
            },
        }

        all_data.append(data_hotel)

    if params.get("search[value]") != "":
        keys_dict = {
            "full": [],
            "start": ["fio", "id"],
            "substr": []
        }
        all_data = list(filter(lambda obj: search_values(
            obj, keys_dict, params["search[value]"]), all_data))

    start_hotel_id = int(params["start"])
    length_hotel_list = int(params["length"])

    moders = all_data[start_hotel_id:start_hotel_id+length_hotel_list]

    content = {
        "draw": params["draw"],
        "recordsTotal": len(all_data),
        "recordsFiltered": len(all_data),
        "data": moders,
    }

    # формируем JsonResponse с параметрами форматирования
    return JsonResponse(content)


@moder_admin_owner_required
def page_list_moderator_reports(request: HttpRequest):
    params = dict(request.GET.items())

    content = {
        "text_category": "Отчёты"
    }

    if params.get("moder_id"):
        user: User = request.user
        if user.is_authenticated and user.additional_info.get("permission"):
            if "supermoderator" in user.additional_info["permission"]:
                content["supermoderator"] = True
                content["moder_id"] = params.get("moder_id")
                user_moder: User = User.objects.filter(
                    id=params.get("moder_id")).first()
                if user_moder:
                    content["text_category"] = user_moder.get_FIO()

    return render(request, 'my_admin/list_moderator_reports.html', content)


@moder_admin_owner_required
def ajax_list_moderator_reports(request: HttpRequest):
    params = dict(request.POST.items())

    if params.get("moder_id"):
        supermoderator: User = request.user
        if supermoderator.is_authenticated and supermoderator.additional_info.get("permission"):
            if "supermoderator" in supermoderator.additional_info["permission"]:
                moder = User.objects.get(id=params.get("moder_id"))
    else:
        moder = request.user.normal()

    hotels_jq = Hotel.objects.filter(
        Q(additional_info__report_from_moder__moderation__user=moder.id) |
        Q(additional_info__report_from_moder__registration__user=moder.id) |
        Q(additional_info__report_from_moder__transfer__user=moder.id)
    )

    all_data = []

    for hotel in hotels_jq:
        hotel: Hotel
        owner = hotel.owner

        owner_fio = owner.get_FIO() if owner else ""
        owner_id = owner.id if owner else None

        moderation_date = hotel.additional_info["report_from_moder"]["moderation"]["create_at"]
        registration_date = hotel.additional_info["report_from_moder"]["registration"]["create_at"]
        transfer_date = hotel.additional_info["report_from_moder"]["transfer"]["create_at"]

        data_hotel = {
            "DT_RowAttr": {
                "data-user-id": owner_id,
                "data-hotel-id": hotel.id,
            },
            "id": hotel.id,
            "name": hotel.name,
            "fio": owner_fio,
            "moderation_date": moderation_date,
            "registration_date": registration_date,
            "transfer_date": transfer_date,
        }

        all_data.append(data_hotel)

    if params.get("search[value]") != "":
        keys_dict = {
            "full": [],
            "start": ["name", "id", "fio"],
            "substr": []
        }
        all_data = list(filter(lambda obj: search_values(
            obj, keys_dict, params["search[value]"]), all_data))

    start_hotel_id = int(params["start"])
    length_hotel_list = int(params["length"])

    moders = all_data[start_hotel_id:start_hotel_id+length_hotel_list]

    content = {
        "draw": params["draw"],
        "recordsTotal": len(all_data),
        "recordsFiltered": len(all_data),
        "data": moders,
    }

    return JsonResponse(content)


@moder_admin_owner_required
@supermoderator_or_owner
def page_list_actions_admin(request: HttpRequest):
    params = dict(request.GET.items())

    users = User.objects.filter(user_type__in=["moder", "admin", "owner"])

    content = {
        "admins": [{"id": user.id, "fio": user.get_FIO()} for user in users]
    }

    return render(request, 'my_admin/list_actions_admin.html', content)


@moder_admin_owner_required
@supermoderator_or_owner
def ajax_list_actions_admin(request: HttpRequest):
    params = dict(request.POST.items())

    if params.get("admin") != None and params.get("admin") != "all":
        users_jq = User.objects.filter(id=params.get("admin"))
    else:
        users_jq = User.objects.filter(
            user_type__in=["moder", "admin", "owner"])

    all_data = []

    admin_logs_jq = AdminLog.objects.filter(user__in=users_jq)

    for admin_log in admin_logs_jq:
        user_fio = admin_log.user.get_FIO() if admin_log.user else ""
        user_id = admin_log.user.id if admin_log.user else None

        data_hotel = {
            "DT_RowAttr": {
                "data-user-id": user_id,
            },
            "id": user_id,
            "fio": user_fio,
            "action": admin_log.action,
            "date": admin_log.timestamp.strftime("%d.%m.%Y %H:%M:%S"),
        }

        all_data.append(data_hotel)

    if params.get("search[value]") != "":
        keys_dict = {
            "full": [],
            "start": ["fio", "id"],
            "substr": ["action"]
        }
        all_data = list(filter(lambda obj: search_values(
            obj, keys_dict, params["search[value]"]), all_data))

    start_hotel_id = int(params["start"])
    length_hotel_list = int(params["length"])

    moders = all_data[start_hotel_id:start_hotel_id+length_hotel_list]

    content = {
        "draw": params["draw"],
        "recordsTotal": len(all_data),
        "recordsFiltered": len(all_data),
        "data": moders,
    }

    return JsonResponse(content)


@moder_admin_owner_required
@supermoderator_or_owner
def page_list_real_work_moderators(request: HttpRequest):
    params = dict(request.GET.items())

    users = User.objects.filter(user_type__in=["moder", "admin", "owner"])

    content = {
        "admins": [{"id": user.id, "fio": user.get_FIO()} for user in users],
    }

    return render(request, 'my_admin/list_real_work_moderators.html', content)


@moder_admin_owner_required
@supermoderator_or_owner
def ajax_list_real_work_moderators(request: HttpRequest):
    params = dict(request.POST.items())

    all_data = []

    hotels_all = Hotel.objects.filter(Q(additional_info__moderation_is_pending_user__isnull=False) | Q(
        additional_info__client_chosen_moderator__isnull=False))

    all_admin_user = {obj.id: {"name": obj.get_FIO()} for obj in User.objects.filter(
        user_type__in=["moder", "admin", "owner"])}

    for hotel in hotels_all:
        hotel: Hotel

        moderation_is_pending = None
        client_chosen_moderator = None

        if hotel.additional_info.get("moderation_is_pending_user"):
            moderation_is_pending = {
                "user": all_admin_user[hotel.additional_info["moderation_is_pending_user"]]["name"] if hotel.additional_info["moderation_is_pending_user"] in all_admin_user else "",
                "date": hotel.additional_info["moderation_is_pending_date"],
            }

        if hotel.additional_info.get("client_chosen_moderator"):
            client_chosen_moderator = {
                "user": all_admin_user[hotel.additional_info["client_chosen_moderator"]]["name"]  if hotel.additional_info["client_chosen_moderator"] in all_admin_user else "",
                "date": hotel.created_at.strftime("%d.%m.%Y %H:%M"),
            }

        data_hotel = {
            "DT_RowAttr": {},
            "id": hotel.id,
            "name": hotel.name,
            "moderation_list": moderation_is_pending,
            "registration_list": client_chosen_moderator,
        }

        all_data.append(data_hotel)

    if params.get("search[value]") != "":
        keys_dict = {
            "full": [],
            "start": ["fio", "id"],
            "substr": []
        }
        all_data = list(filter(lambda obj: search_values(
            obj, keys_dict, params["search[value]"]), all_data))

    start_hotel_id = int(params["start"])
    length_hotel_list = int(params["length"])

    hotels = all_data[start_hotel_id:start_hotel_id+length_hotel_list]

    content = {
        "draw": params["draw"],
        "recordsTotal": len(all_data),
        "recordsFiltered": len(all_data),
        "data": hotels,
    }

    # формируем JsonResponse с параметрами форматирования
    return JsonResponse(content)


@supermoderator
def set_debug_mode(request):
    request.session['debug'] = True
    request.session.save()
    return redirect('/')


@moder_admin_owner_required
def page_review_moderation(request: HttpRequest):
    return render(request, 'my_admin/review_moderation.html')


def ajax_get_reviews(request: HttpRequest):
    # Получение списка отзывов из базы данных с помощью ORM
    reviews_qs = Comment.objects.filter(is_pending=True).order_by("-date")

    # Формирование списка отзывов для возврата в ответе
    results = []
    for review in reviews_qs:
        review: Comment

        imgs = Img.get_url_list("hotel.comment", review.id)

        results.append({
            "id": review.id,
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
            "imgs": list(imgs),
            "reply": review.reply,
        })

    # Формирование ответа в формате JSON
    response = {
        'results': results,
    }

    return JsonResponse(response)


def ajax_update_reviews(request: HttpRequest):
    if request.method == 'POST':
        update_reviews: dict = json.loads(request.body.decode('utf-8'))

        update_reviews_count = 0

        for id, review_param in update_reviews.items():
            review_obj = Comment.objects.filter(id=id).first()
            if review_obj:

                update_reviews_count += 1

                if review_param["action"] == "remove":
                    review_obj.delete()
                    continue

                if review_param["what_is_good_text"]:
                    review_obj.what_is_good_text = review_param["what_is_good_text"]

                if review_param["what_is_bad_text"]:
                    review_obj.what_is_bad_text = review_param["what_is_bad_text"]

                if review_param["action"] == "allow":
                    review_obj.is_pending = False

                review_obj.save()

        return JsonResponse({"update_reviews_count": update_reviews_count})
    else:
        return JsonResponse({"success": False, "error": "Invalid request method."})


@moder_admin_owner_required
def ajax_user_statistics(request):
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    # Получение активных сессий
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())

    # Получение уникальных пользователей
    active_users_ids = set([s.get_decoded().get('_auth_user_id')
                            for s in active_sessions])

    active_users = []

    # Собираем информацию о пользователях в словарь
    for session in active_sessions:
        session: Session
        param = session.get_decoded()

        user = User.objects.get(id=param.get("_auth_user_id"))

        active_users.append({"param": str(
            user), "expire_date": session.expire_date.strftime("%d/%m/%Y, %H:%M:%S")})

    # Собираем информацию о пользователях в словарь
    user_statistics = {
        'all_count_user': Session.objects.all().count(),
        'active_users_count': len(active_users),
        'active_users': active_users,
    }

    # Преобразуем данные в JSON и добавим поддержку русского языка и оформления
    json_data = json.dumps(user_statistics, ensure_ascii=False, indent=4)

    # Возвращаем данные в формате JSON
    return HttpResponse(json_data, content_type='application/json')



types_parser_item = {
    "not_download": "Не скачено",
    "download": "Скачено",
    "error": "Ошибка",
    "materialize_a_hotel_request": "Перенос на сайт...",
    "materialize_a_hotel": "На сайте"
}

@moder_admin_owner_required
def page_parser_hotel(request):
    content = {
        "random": 123,
        # "random": ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    }
    return render(request, 'my_admin/parser/hotel/index.html', content)


@moder_admin_owner_required
def api_parser_hotel_add(request: HttpRequest):

    link = request.POST.get("link")

    if not link:
        return JsonResponse({
            "status": "error",
            "popup": {
                "title": "Ошибка",
                "text": "Вы не вели ссылку",
                "type": "error",
            }
        })

    if link.find("?") >= 5:
        link = link.split("?")[0]

    pattern = r"https:\/\/ostrovok\.ru\/hotel\/(\w+)\/(\w+)\/mid(\w+)\/(\w+)"
    match = re.match(pattern, link)
    if not match:
        return JsonResponse({
            "status": "error",
            "popup": {
                "title": "Ошибка",
                "text": "Ссылка некорректна",
                "type": "error",
            }
        })

    parser_data = Constant.get("parser", "json")

    if not parser_data:
        parser_data = {
            "hotel": {
                "items": []
            }
        }

    id_hotel = match.group(4)

    for item in parser_data['hotel']['items']:
        if item["id"] == id_hotel:
            return JsonResponse({
                "status": "error",
                "popup": {
                    "title": "Ошибка",
                    "text": f"Отель уже есть в списке: Статус: {types_parser_item[item['type']]} ({item['type']})",
                    "type": "error",
                }
            })

    new_obj = {
        "status": "not_download",
        "parser": "ostrovok.hotel",
        "id": id_hotel,
    }

    parser_data['hotel']['items'].append(new_obj)

    Constant.set("parser", parser_data, "json")

    return JsonResponse({
        "status": "success",
        "popup": {
            "title": "Успех",
            "text": f"Отель добавлен в список.<br>Статус: {types_parser_item[new_obj['status']]} ({new_obj['status']})",
            "type": "success",
        }
    })

@moder_admin_owner_required
def api_parser_hotel_get(request: HttpRequest):
    parser_data = Constant.get("parser", "json")

    if not parser_data:
        parser_data = {
            "hotel": {
                "items": []
            }
        }

    hotel_list = []
    for item in parser_data["hotel"]["items"]:
        obj = item
        if obj.get("param") and obj["param"].get("images") and len(obj["param"]["images"]) > 0:
            obj["img"] = obj["param"]["images"][0]["url"]
            obj["name"] = obj["param"]["name_hotel"]

        if obj.get("param") and obj["param"].get("error"):
            obj["status"] = "error"

        obj["status_text"] = types_parser_item[obj["status"]]

        hotel_list.append(item)

    return JsonResponse({
        "status": "success",
        "list": hotel_list,
    })


@moder_admin_owner_required
def api_parser_hotel_materialize_a_hotel(request: HttpRequest):
    parser_data = Constant.get("parser", "json")
    parser_data_hotel = parser_data["hotel"]["items"]

    param : dict = json.loads(request.body.decode('utf-8'))

    valid_hotels = []

    user_obj = {}


    if param["form_type"] == "new_user":
        user = User.objects.filter(
            username=param["user"]["username"],
            lastname=param["user"]["lastname"],
            email=param["user"]["email"],
        ).first()

    if param["form_type"] == "existing_user":
        user = User.objects.filter(
            id=param["user"]["id"],
            email=param["user"]["email"],
        ).first()

    if user:
        user_obj["status"] = "exist"
        user_obj["id"] = user.id


    for param_hotel_index, param_hotel_id in param["hotels"].items():
        for parser_hotel_index, parser_hotel_obj in enumerate(parser_data["hotel"]["items"]):
            if parser_hotel_obj["status"] == "download":
                if parser_hotel_obj["id"] == param_hotel_id:
                    valid_hotels.append(parser_hotel_obj)

                    if not user:
                        user: User = User.objects.create_user(
                            username=param["user"]["username"],
                            lastname=param["user"]["lastname"],
                            middlename=param["user"]["middlename"],
                            email=param["user"]["email"],
                            login=param["user"]["login"],
                            password=param["user"]["password"],
                            phone=param["user"]["phone"],
                            gender="Мужской",
                        )

                        user.additional_info["password"] = param["user"]["password"]

                        user_obj["status"] = "created"
                        user_obj["id"] = user.id

                    parser_data["hotel"]["items"][parser_hotel_index]["param"]["user"] = user.id
                    parser_data["hotel"]["items"][parser_hotel_index]["status"] = "materialize_a_hotel_request"

    Constant.set("parser", parser_data, "json")



    return JsonResponse({
        "valid_hotels": valid_hotels,
        "user": user_obj,
    })




@moder_admin_owner_required
def page_site_management(request):
    content = {
        "hotel_type": Hotel.type_hotel_choices,
    }
    return render(request, 'my_admin/site_management.html', content)