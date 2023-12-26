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

def access_to_staff(view_func):
    def wrapper(request, *args, **kwargs):
        user: User = User.objects.get(id=request.user.id)
        if user.is_authenticated and user.additional_info.get("permission"):
            if "access_to_staff" in user.additional_info["permission"]:
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


def superuser(view_func):
    def wrapper(request, *args, **kwargs):
        user: User = User.objects.get(id=request.user.id)
        if user.is_authenticated and user.is_superuser:
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


@access_to_staff
def index(request):
    return render(request, 'my_admin/staff/index.html')


type_user_temps = {
    "admin": "Администратор",
    "moder": "Модератор",
    "owner": "Разрабочик",
}

@access_to_staff
def api_get_list(request):
    users = [
        {
            "id": user.id,
            "fio": user.get_FIO(),
            "type": user.user_type,
            "type_text": type_user_temps[user.user_type],
        }
        for user in User.objects.filter(user_type__in=["admin", "moder"])
    ]
    content = {
        "users": users
    }
    return JsonResponse(content)

def get_moderwork_last_param(obj: list):
    if isinstance(obj, list):
        if len(obj) > 0:
            return obj[-1]["value"]
    return None

@access_to_staff
def api_moderwork_last_param(obj: list):
    if isinstance(obj, list):
        if len(obj) > 0:
            return obj[-1]["value"]
    return None

@access_to_staff
def api_get_user(request):

    get_user_id = request.GET.get("user_id")

    user = User.objects.filter(id=get_user_id).first()
    if not user:
        return JsonResponse({
            "status": "success",
            "popup": {
                "title": "Ошибка",
                "text": f"Пользователь [ID] {get_user_id} не найден",
                "type": "error",
            }
        }, status=404)

    if not user.additional_info.get("permission"):
        user.additional_info["permission"] = []

    if not user.additional_info.get("staff_information"):
        user.additional_info["staff_information"] = """
ФИО:
Дата рождения:
Проживает:
Поступил на работу:
Уволился:
Должность:
Статус:
Примечании:
        """
        user.save()

    exclude = [
        "access_token",
        "access_token_key",
        "active_code_email",
        "active_code_phone",
        "active_code_phone_2",
        "active_email",
        "active_phone",
        "active_phone_2",
        "groups",
        "is_active",
        "is_admin",
        "is_staff",
        "is_superuser",
        "phone_2",
        "token_google",
        "token_telegram",
        "token_vk",
        "uid",
        "password",
    ]

    moderworks: QuerySet[ModerWork] = user.moderworks.all()
    chats_message: QuerySet[Message] = user.chat_message.all()

    content = {
        "user": model_to_dict(user, exclude=exclude),
    }
    if moderworks.exists():
        content["moderworks"] = []

        for work in moderworks:
            try:
                obj = {
                    "user": work.user.email,
                    "hotels": [hotel.name for hotel in work.hotels.all()],
                }
                if (work.status):
                    obj["status"] = get_moderwork_last_param(work.status)

                content["moderworks"].append(obj)
            except:
                pass


    if chats_message.exists():
        content["chats_messages"] = [
            {
                "chat": mess.chat.id if hasattr(mess.chat, "id") else None,
                "datetime": mess.datetime.strftime("%d.%m.%Y %H:%M:%S"),
                "text": mess.text,
            }
            for mess in chats_message.order_by("-datetime")
        ]

    return JsonResponse(content)

@superuser
def api_edit_user(request):
    param: dict = json.loads(request.body.decode('utf-8'))

    user_id = param["user"]["id"]

    user = User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({
            "status": "error",
            "popup": {
                "title": "Ошибка",
                "text": f"Пользователь [ID] {user_id} не найден",
                "type": "error",
            }
        }, status=404)

    # Изменение типа пользователя
    user.user_type = param["user"]["user_type"]


    # Изменение разрешений
    permission = param["user"]["additional_info"].get("permission")
    if permission and isinstance(permission, str):
        words = permission.split(",") if permission else []
        clean_words = [word.strip() for word in words]
        user.additional_info["permission"] = clean_words


    # Изменить основную информацию
    staff_information = param["user"]["additional_info"].get("staff_information")
    if staff_information and isinstance(staff_information, str):
        user.additional_info["staff_information"] = staff_information

    user.save()

    return JsonResponse({
        "status": "success",
        "popup": {
            "title": "Успех",
            "text": f"Данные у пользователя [ID] {user_id} успешно сохранены",
            "type": "success",
        }
    }, status=200)
