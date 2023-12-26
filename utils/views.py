import datetime
import json
import os
import random
import re
import string
import time
import uuid
from django import http
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile, File
from PIL import Image
from io import BytesIO
from django.core.signing import Signer, BadSignature

from partner.models import Partner
from user.models import Notice
from .models import Img, Place, Doc, ShortLink, DocumentationPage
from django.db.models import Q

def add_not_linked_img(request):
    if request.method == 'POST':
        files : UploadedFile = request.FILES.getlist('file[]')
        id_list = []
        for file in files:
            img = Img.not_linked_new()
            img.image.save("", file)
            id_list.append({"id": img.id, "url": img.image.url})

        return JsonResponse({'id_list': id_list})
    else:
        return JsonResponse({'error': 'Only POST requests are allowed.'})


def add_not_linked_doc(request):
    if request.method == 'POST':
        files : UploadedFile = request.FILES.getlist('file[]')
        id_list = []
        for file in files:
            if file.name.lower().endswith('.heic'):
                random_filename = str(uuid.uuid4()).replace("-", "")[:10]
                heic_image = pyheif.read(file)

                # Преобразуйте HEIC-изображение в формат JPG
                heic_image = Image.frombytes(heic_image.mode, heic_image.size, heic_image.data, "raw", heic_image.mode, heic_image.stride)

                jpg_image_abs = os.path.abspath("media/doc/" + random_filename + '.jpg')

                heic_image.save(jpg_image_abs, 'JPEG')

                # Сохраните путь к файлу JPG в базе данных
                doc = Doc.not_linked_new()
                doc.file.name = "doc/" + random_filename + '.jpg'
                doc.save()
                id_list.append({"id": doc.id, "url": doc.file.url})
            else:
                doc = Doc.not_linked_new()
                doc.file.save(file.name, file)
                id_list.append({"id": doc.id, "url": doc.file.url})

        return JsonResponse({'id_list': id_list})
    else:
        return JsonResponse({'error': 'Only POST requests are allowed.'})

def ajax_search_place(request):
    if request.method == 'GET' and request.GET.get("q"):
        search = request.GET.get("q")
        places_QS = Place.objects.filter(Q(name__istartswith=search) | Q(name__istartswith=Place.convert_layout(search)))

        results = []


        for place in places_QS[:10]:
            place : Place
            parents = place.get_parents()

            results.append({
                "id": place.id,
                "label": place.name,
                "additional_address": parents[0].name if len(parents) > 0 else place.name,
                "slug": place.get_slug(),
            })

        popular_name_list = [
            "Москва",
            "Санкт-Петербург",
            "Сочи",
            "Казань",
        ]

        places_all_QS = Place.objects.filter(name__in=popular_name_list)

        popular = []

        for place in places_all_QS:
            place : Place
            parents = place.get_parents()
            popular.append({
                "label": place.name,
                "additional_address": parents[0].name,
                "slug": place.get_slug(),
            })

        content = {
            'results': results,
            'popular': popular,
        }

        return JsonResponse(content, safe=False)
    else:
        return JsonResponse({'error': 'Only GET requests are allowed.'})

def ajax_get_missing_images_paths(request):

    paths = Img.get_missing_images_paths()

    return JsonResponse({"count": len(paths), 'list': paths})

def shortlink_redirect(request, short_code):
    short_link = get_object_or_404(ShortLink, short_code=short_code)
    return redirect(short_link.original_url)


def extract_user_agent_details(user_agent):
    # Образец регулярного выражения для анализа User-Agent
    pattern = r'\((.*?)\)|\/(.*?) '

    # Извлечение информации с помощью регулярного выражения
    matches = re.findall(pattern, user_agent)

    # Проверка наличия совпадений и извлечение местоположения и типа устройства
    device_type = None


    if matches:
        for match in matches:
            details = match[0] if match[0] else match[1]
            if 'Mobile' in details:
                device_type = 'Mobile'
            elif 'Tablet' in details:
                device_type = 'Tablet'
            elif 'Windows' in details:
                device_type = 'Windows'
            elif 'Mac' in details:
                device_type = 'Mac'
            elif 'Linux' in details:
                device_type = 'Linux'
            elif 'Android' in details:
                device_type = 'Android'
            elif 'iPhone' in details:
                device_type = 'iPhone'
            elif 'iPad' in details:
                device_type = 'iPad'

    return {"device_type": device_type}

def widget_redirect(request):
    api_key = request.GET.get('api')
    type_widget = request.GET.get('type')
    site = request.GET.get('site')
    next_url = request.GET.get('next', '/')
    partner = Partner.objects.get(api_key=api_key)

    # Генерация случайного ключа записи статистики виджета
    random_key = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    # Создание записи статистики виджета в виде словаря
    widget_stat = {
        "site": site,
        "next": next_url,
        "type": type_widget,
        "user_agent": extract_user_agent_details(request.META.get('HTTP_USER_AGENT')),
        "ip_address": request.META.get('REMOTE_ADDR'),
        "created_at": int(time.time()),
    }

    # Добавление записи статистики в словарь partner.option["stat"]["widget"]
    partner.option.setdefault("stat", {}).setdefault("widget", {})
    partner.option["stat"]["widget"][random_key] = widget_stat

    # Установить cookie с информацией о переходе

    partner.save()

    response = redirect(next_url)

    signer = Signer()
    signed_obj = signer.sign_object({"p": partner.id, "type": "widget", "key": random_key})

    response.set_cookie('belongpartner', signed_obj, expires=24*60*60*30)
    return response



def benner_redirect(request):
    api_key = request.GET.get('api')
    type_banner = request.GET.get('type')
    site = request.GET.get('site')
    next_url = request.GET.get('next', '/')
    partner = Partner.objects.get(api_key=api_key)

    # Генерация случайного ключа записи статистики виджета
    random_key = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    # Создание записи статистики виджета в виде словаря
    banner_stat = {
        "site": site,
        "next": next_url,
        "type": type_banner,
        "user_agent": extract_user_agent_details(request.META.get('HTTP_USER_AGENT')),
        "ip_address": request.META.get('REMOTE_ADDR'),
        "created_at": int(time.time()),
    }

    # Добавление записи статистики в словарь partner.option["stat"]["banner"]
    partner.option.setdefault("stat", {}).setdefault("banner", {})
    partner.option["stat"]["banner"][random_key] = banner_stat

    # Установить cookie с информацией о переходе

    partner.save()

    response = redirect(next_url)

    signer = Signer()
    signed_obj = signer.sign_object({"p": partner.id, "type": "banner", "key": random_key})

    response.set_cookie('belongpartner', signed_obj, expires=24*60*60*30)
    return response

def get_stats(request):
    belongpartner_cookie = request.COOKIES.get('belongpartner')

    # Расшифровка "belongpartner" cookie
    decrypted_data = Partner.decrypt_belongpartner(belongpartner_cookie)

    # Получение данных из расшифрованного объекта
    partner_id = decrypted_data.get('p')

    # Поиск партнера по идентификатору
    try:
        partner = Partner.objects.get(id=partner_id)
    except Partner.DoesNotExist:
        return JsonResponse({'error': 'Partner not found'}, status=404)

    # Поиск статистики баннеров для данного партнера и ключа
    stat = partner.option.get("stat", {})
    if not stat:
        return JsonResponse({'error': 'Statistic not found'}, status=404)

    json_data = json.dumps({'decrypted_data':decrypted_data, 'stat': stat}, ensure_ascii=False, indent=4).encode('utf-8')
    return HttpResponse(json_data, content_type="application/json; charset=utf-8")


def documentation_no_slug(request):
    content = {
        "meta": {
            "title": 404,
        }
    }
    return render(request, 'documentation/base_content/404.html', content)

def documentation(request, slug):

    documentation_page = DocumentationPage.objects.filter(slug=slug).first()

    if not documentation_page:
        content = {
            "meta": {
                "title": 404,
            }
        }

        return render(request, 'documentation/base_content/404.html', content)

    content = {
        "title": documentation_page.title,
        "documentation": {
            "content": documentation_page.content
        }
    }

    return render(request, 'documentation/index.html', content)


def notice_get(request):

    content = {
        "notices": Notice.get_notifications(request.user)
    }

    return JsonResponse(content)