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


def test_1(request):
    content = {}
    return render(request, 'my_admin/debug/index.html', content)