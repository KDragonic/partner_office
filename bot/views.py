import datetime
import json
import re
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.conf import settings
import requests
from utils.models import LogAction, Constant
from user.models import User, Notification
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

# settings.TELEGRAMBOT_TOKEN

url_base = f"https://api.telegram.org/bot{settings.TELEGRAMBOT_TOKEN}/"


def start(request):
    params = {
        'url': request.build_absolute_uri(reverse('telebot.webhook'))
    }

    response = requests.get(url_base + "setWebhook", params=params)

    content = {
        "params": params,
        "response": response.json(),
    }

    json_data = json.dumps(content, ensure_ascii=False).encode('utf-8')
    return HttpResponse(json_data, content_type="application/json; charset=utf-8")


def check(request):
    response = requests.get(url_base + "getWebhookInfo")

    content = {
        "response": response.json(),
    }

    json_data = json.dumps(content, ensure_ascii=False).encode('utf-8')
    return HttpResponse(json_data, content_type="application/json; charset=utf-8")

def end(request):
    response = requests.get(url_base + "deleteWebhook")

    content = {
        "response": response.json(),
    }

    json_data = json.dumps(content, ensure_ascii=False).encode('utf-8')
    return HttpResponse(json_data, content_type="application/json; charset=utf-8")

def send_message(chat_id, message, parse_mode=False):

    message = re.sub(r'([_[\]()~>`#+\-=|{}.!])', r'\\\1', message)

    params = {
        "chat_id": chat_id,
        "text": message,
    }

    if parse_mode:
        params["parse_mode"] = "MarkdownV2"

    response = requests.get(url_base + "sendMessage", params=params)

    content = {
        "params": params,
        "response": response.json(),
    }

    print("Отправлено сообщение", response.json())

    return content


def check_auth_user(id_user_telegram):
    return User.objects.filter(token_telegram=id_user_telegram).exists()


@csrf_exempt
def webhook(request):
    data = request.body.decode('utf-8')
    data_dict = json.loads(data)

    if data_dict.get("message"):
        is_bot = data_dict["message"]["from"]["is_bot"]
        if not is_bot:
            if not check_auth_user(data_dict["message"]["from"]["id"]):
                pattern = r'^auth_code_'

                # Проверка что сообщение начинаетс с auth_code_
                if re.match(pattern, data_dict["message"]["text"]):
                    user: User = User.objects.filter(
                        token_telegram=data_dict["message"]["text"]).first()
                    if user:  # Если есть такой пользователь
                        user.token_telegram = data_dict["message"]["from"]["id"]
                        user.save()
                        send_message(data_dict["message"]["chat"]["id"], f"Вы успешно авторизированы, {user.get_FIO()}")
                    else:
                        send_message(data_dict["message"]["chat"]["id"], f"Не верный код")
                else:
                    send_message(data_dict["message"]["chat"]["id"], "Вы не авторизированы, ведите код который находится в личном кабинете")

    return HttpResponse("True")


def getUpdates(request):
    params = {
        "allowed_updates": ["message"],
    }

    offset_str = Constant.get('telebot_index_getupdates')
    if offset_str != None:
        params["offset"] = int(offset_str)

    messages = []

    response = requests.get(url_base + "getUpdates", params=params)

    messages_json = response.json()["result"]

    if messages_json:  # если список не пуст
        last_element = messages_json[-1]  # получаем последний элемент
        Constant.set('telebot_index_getupdates',
                     str(last_element["update_id"] + 1))

    for mess_json in messages_json:
        is_bot = mess_json["message"]["from"]["is_bot"]
        if not is_bot:
            date = datetime.datetime.fromtimestamp(
                mess_json["message"]["date"])

            if not check_auth_user(mess_json["message"]["from"]["id"]):
                pattern = r'^auth_code_'

                # Проверка что сообщение начинаетс с auth_code_
                if re.match(pattern, mess_json["message"]["text"]):
                    user: User = User.objects.filter(
                        token_telegram=mess_json["message"]["text"]).first()
                    if user:  # Если есть такой пользователь
                        user.token_telegram = mess_json["message"]["from"]["id"]
                        user.save()
                        send_message(
                            mess_json["message"]["chat"]["id"], f"Вы успешно авторизированы, {user.get_FIO()}")
                    else:
                        send_message(mess_json["message"]
                                     ["chat"]["id"], f"Не верный код")
                else:
                    send_message(mess_json["message"]["chat"]["id"],
                                 "Вы не авторизированы, ведите код который находится в личном кабинете")

            messages.append({
                "user": {
                    "id": mess_json["message"]["from"]["id"],
                    "username": mess_json["message"]["from"]["username"],
                },
                "message": {
                    "date": date.strftime('%d.%m.%Y %H:%M:%S'),
                    "text": mess_json["message"]["text"],
                }
            })

    content = {
        "messages": messages,
    }

    json_data = json.dumps(content, ensure_ascii=False,
                           indent=2).encode('utf-8')
    return HttpResponse(json_data, content_type="application/json; charset=utf-8")
