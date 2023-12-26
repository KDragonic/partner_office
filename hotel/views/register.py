import datetime
import json
import locale
import math
from geopy.distance import geodesic
from time import strptime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.urls import reverse
import requests
from brontur.funs import add_meta, generate_password
from chat.models import Chat
from user.models import MyUserManager
# from hotel.models import Address, HImg, Hotel, RCategory, Room, Comment, RImg, RService, HService, Booking

from hotel.models import Address
from hotel.models import Hotel
from hotel.models import RCategory
from hotel.models import Room
from hotel.models import Comment
from hotel.models import RService
from hotel.models import HService
from hotel.models import Booking
from hotel.models import GroupBooking
from hotel.models import Favourite
from django.forms.models import model_to_dict

from django.db.models import Q

from user.models import User, Notification, Companion, Bonus_rubles, FinancialOperation
from user.mail import send as send_mail
from django.db.models import Count

from django.http import HttpResponse, JsonResponse

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.core.management import call_command

from django.http import Http404

from utils.models import Img, Place


@login_required
def hotel_register(request):

    content = {
        "types_hotel": [{"code": type_hotel[0], "name": type_hotel[1]} for type_hotel in Hotel.type_hotel_choices]
    }

    return render(request, 'hotel/register.html', content)


@login_required
def page_register_placement_object(request):


    if request.user.user_type in ["admin", "moder"]:
        return redirect("/admin/")

    content = {
        "types_hotel": [{"code": type_hotel[0], "name": type_hotel[1]} for type_hotel in Hotel.type_hotel_choices]
    }

    choices = {}

    choices["offer_type"] = []
    for item in RCategory.offer_type_choices:
        choices["offer_type"].append([item[0], item[1]])

    choices["rservice"] = []
    service_qs = RService.objects.all()
    for item in service_qs:
        choices["rservice"].append([item.id, item.name])

    choices["offer_type"] = json.dumps(choices["offer_type"])
    choices["rservice"] = json.dumps(choices["rservice"])

    content["choices"] = choices

    all_moder = User.objects.filter(user_type__in=["moder"  ])

    content["managers"] = [[obj.id, obj.get_FIO()] for obj in all_moder],

    return render(request, 'hotel/register_new.html', content)
