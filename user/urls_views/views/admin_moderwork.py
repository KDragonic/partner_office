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


def superuser(view_func):
    def wrapper(request, *args, **kwargs):
        user: User = User.objects.get(id=request.user.id)
        if user.is_authenticated and user.is_superuser:
                return view_func(request, *args, **kwargs)

        return render(request, 'error_page.html', {'message': None, "status": 403}, status=403)
    return wrapper

def access_to_moderwork(view_func):
    def wrapper(request, *args, **kwargs):
        user: User = User.objects.get(id=request.user.id)
        if user.is_authenticated and user.additional_info.get("permission"):
            if "access_to_moderwork" in user.additional_info["permission"]:
                return view_func(request, *args, **kwargs)

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


@access_to_moderwork
def index(request):

    content = {
            "places": Place.get_list_mini(),
    }

    content["users_staff"] = []

    for user in User.objects.filter(user_type__in=["owner", "admin", "moder"]):

        content["users_staff"].append({
            "id": user.id,
            "name": str(user),

        })


    return render(request, 'my_admin/moderwork/index.html', content)


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

    obj["staff"] = {
        "id": moderwork.moder.id,
        "name": moderwork.moder.get_FIO(),
    }

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

    if hotel_parser_owner:
        hotel_user_login = hotel_parser_owner.additional_info["user"].get(
            "login") if hotel_parser_owner.additional_info.get("user") else None
        hotel_user_password = hotel_parser_owner.additional_info["user"].get(
            "password") if hotel_parser_owner.additional_info.get("user") else None

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

@access_to_moderwork
def api_get_list(request):
    content = {}

    content["moder_works"] = {}
    for work in ModerWork.objects.all():
        obj = moderworks_to_dict(work)

        content["moder_works"][obj["id"]] = obj

    return JsonResponse(content)

@access_to_moderwork
def api_move_item(request):
    param: dict = json.loads(request.body.decode('utf-8'))

    moderworks_qs = ModerWork.objects.filter(id__in=param["ids"])
    moder_new = User.objects.filter(id=param["user_id"]).first()

    moderworks = [{"id": work.id, 'user': str(work.user), "moder": str(work.moder)} for work in moderworks_qs]

    moderworks_qs.update(moder=moder_new)

    moderworks_new = [{"id": work.id, 'user': str(work.user), "moder": str(work.moder)} for work in moderworks_qs]



    content = {
        "param": param,
        "result": {
            "moderworks_old": moderworks,
            "moderworks_new": moderworks_new,
            "moder": str(moder_new),
        }
    }

    return JsonResponse(content)
