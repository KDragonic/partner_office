
import datetime
import json
import os
import random
import time
from django.conf import settings
from django.shortcuts import render, redirect
import requests
from user.google_auth import create_authorization_url, token_to_user_info, get_userinfo
from django.forms import model_to_dict

from user.models import FinancialOperation, Notification, User, MyUserManager, Bonus_rubles
from django.contrib.auth import login as uLogin, logout as uLogout
from django.urls import reverse
from urllib.parse import urlencode
from brontur.funs import generate_password, gen_uid, send_mail_user
import user.mail as my_mail
from django.http import FileResponse, Http404, HttpRequest, JsonResponse, HttpResponse
from django.db.models import Q
from django.contrib import messages
from tqdm import tqdm


from utils.models import Place


def page_register(request):
    content = {}

    client_id = settings.VK_APP_ID

    redirect_uri_vk = "/vk/register/"

    content["vk_auth_url"] = f"https://oauth.vk.com/authorize?client_id={client_id}&display=page&scope=email&redirect_uri={redirect_uri_vk}&response_type=token&v=5.131&revoke=1"
    content["google_auth_url"] = create_authorization_url(state="register")

    if request.method == 'POST':
        username = request.POST.get("username")
        lastname = request.POST.get("lastname")
        middlename = request.POST.get("middlename")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone = request.POST.get("phone")

        if User.objects.filter(Q(email=email)).exists():
            content["email_is_busy"] = True

        if User.objects.filter(Q(phone=phone)).exists():
            content["phone_is_busy"] = True

        if content.get("phone_is_busy") or content.get("email_is_busy"):
            content["past_values"] = {
                "username": username,
                "lastname": lastname,
                "middlename": middlename,
                "email": email if not content.get("email_is_busy") else "Такой email уже зарегистрирован",
                "phone": phone if not content.get("phone_is_busy") else "Такой телефон уже зарегистрирован",
                "password": password,
            }
            return render(request, 'user/register.html', content)

        active_code_email = generate_password(30)

        user: User = User.objects.create_user(
            username=username,
            lastname=lastname,
            middlename=middlename,
            email=email,
            login=email,
            password=password,
            gender="Мужской",
            phone=phone,
            active_code_email=active_code_email,
        )

        user.additional_info["password"] = password
        user.save()

        confirmation_email_address_url = request.build_absolute_uri(
            reverse("confirmation_email_address")) + f"?code={active_code_email}"

        if my_mail.send("confirmation_email_address", "Подтвердите свою почту на сайте", email, {"confirmation_email_address_url": confirmation_email_address_url}) == False:
            Notification.new(user, "Вы вели неправильную почту",
                             "", "/profile/", True, True)
        else:
            Notification.new(user, "Подтвердите почту",
                             "Вам на почту пришло письмо для подтверждения почты", "/profile/", True, True)

        from utils.models import Constant
        settings_options_obj: dict = Constant.get("settings_options", "json")
        bonus_lifetime = int(
            settings_options_obj["registration_bonuses"]["lifetime"])
        bonus_value = int(
            settings_options_obj["registration_bonuses"]["value"])

        Bonus_rubles.objects.create(
            user=user,
            value=bonus_value,
            lifespan=bonus_lifetime,
            text="Получено за регистрацию"
        )

        FinancialOperation.new(
            user, bonus_value, True, "user", "Получено за регистрацию")

        uLogin(request, user)
        return render(request, 'user/page_back_url_login_page.html', {"type_user": user.user_type, "type_of_transition": "simple_registration"})

    return render(request, 'user/register.html', content)


def page_login(request):
    if request.method == 'POST':
        login = request.POST.get("login")
        password = request.POST.get("password")

        if len(password) > 4:
            user = MyUserManager.authenticate(login=login, password=password)
            if user is not None:
                uLogin(request, user)
                return render(request, 'user/page_back_url_login_page.html')

    client_id = settings.VK_APP_ID

    redirect_uri_vk = request.build_absolute_uri(reverse("vk_login"))

    vk_auth_url_params = {
        "client_id": client_id,
        "display": "page",
        "redirect_uri": redirect_uri_vk,
        "response_type": "token",
        "v": 5.131,
        "revoke": 1,
    }

    content = {
        "vk_auth_url": f"https://oauth.vk.com/authorize?" + urlencode(vk_auth_url_params),
        # "google_auth_url": f"https://accounts.google.com/o/oauth2/auth?" + urlencode(google_auth_url_params)
        # "google_auth_url": f"https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(google_auth_url_params)
        "google_auth_url": create_authorization_url(state="login")
    }

    return render(request, 'user/login.html', content)


def page_logout(request):
    uLogout(request)
    return redirect('login')


def password_recovery(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            user: User = User.objects.filter(email=email).first()
            if user:
                messages.success(
                    request, 'Инструкции по восстановлению пароля отправлены на ваш email.')
                url_reset_password = request.build_absolute_uri(
                    reverse("page_reset_password"))
                url_reset_password += f"?user_id={user.id}&access_token={user.get_access_token()}"

                if my_mail.send("reset_password", "Сброс пароля",  email, {"url": url_reset_password}) == False:
                    Notification.new(
                        user, "Вы вели неправильную почту", "", "/profile/", True, True)

                return render(request, 'user/password_recovery.html', {'email_sent': True})
            else:
                messages.error(
                    request, 'Пользователь с таким email не существует.')

    return render(request, 'user/password_recovery.html')


def reset_password(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        access_token: str = request.GET.get('access_token')

        access_token = access_token.replace(" ", "+")

        user: User = User.objects.filter(id=user_id).first()

        if user.check_access_token(access_token):
            new_password = generate_password(8)
            user.set_password(new_password)
            user.additional_info["password"] = new_password
            user.save()

            if my_mail.send("new_password", "Новый пароль", user.email, {"new_password": new_password}) == False:
                Notification.new(
                    user, "Вы вели неправильную почту", "", "/profile/", True, True)

            return render(request, 'user/password_recovery.html', {"expect_a_letter": True})

    raise Http404('Пользователь, не найден')


def vk_register(request):
    vk_user_id = request.GET.get("user_id")
    if vk_user_id != None:
        vk_user_id = int(vk_user_id)
        email = request.GET.get("email")

        user = User.objects.filter(token_vk=vk_user_id).first()
        if user == None:
            password = generate_password(8)
            user = User.objects.create(
                email=email,
                token_vk=vk_user_id,
                login="",
                password=password,
                uid=gen_uid(),
            )

            user.additional_info["password"] = password
            user.save()

            from utils.models import Constant
            settings_options_obj: dict = Constant.get(
                "settings_options", "json")
            bonus_lifetime = int(
                settings_options_obj["registration_bonuses"]["lifetime"])
            bonus_value = int(
                settings_options_obj["registration_bonuses"]["value"])

            Bonus_rubles.objects.create(
                user=user,
                value=bonus_value,
                lifespan=bonus_lifetime,
                text="Получено за регистрацию"
            )

            FinancialOperation.new(
                user, bonus_value, True, "user", "Получено за регистрацию")

        uLogin(request, user)
        return redirect("/profile/")

    return render(request, "vk_auth.html")


def vk_login(request):
    vk_user_id = request.GET.get("user_id")
    if vk_user_id != None:
        vk_user_id = int(vk_user_id)
        user = User.objects.filter(token_vk=vk_user_id).first()

        if user != None:
            uLogin(request, user)
            return render(request, 'user/page_back_url_login_page.html')
        else:
            return redirect("register")

    return render(request, "vk_auth.html")


def google_auth(request):
    code = request.GET.get("code")

    credentials, obj_credentials = token_to_user_info(code)

    user_info = get_userinfo(credentials)

    user = User.objects.filter(token_google=user_info["id"]).first()

    if not user:
        password = generate_password(8)
        new_user_param = {
            "email": user_info["email"],
            "token_google": user_info["id"],
            "login": user_info["email"],
            "password": password,
            "uid": gen_uid(),
        }

        user.additional_info["password"] = password
        user.save()

        active_code_email = generate_password(30)
        new_user_param["active_code_email"] = active_code_email
        confirmation_email_address_url = request.build_absolute_uri(
            reverse("confirmation_email_address")) + f"?code={active_code_email}"

        user = User.objects.create(**new_user_param)
        my_mail.send("new_user", "Добро пожаловать на сайт turgorodok.ru",
                     user_info["email"], new_user_param)

        if my_mail.send("confirmation_email_address", "Подтвердите свою почту на сайте", user_info["email"], {"confirmation_email_address_url": confirmation_email_address_url}) == False:
            Notification.new(user, "Вы вели неправильную почту",
                             "", "/profile/", True, True)
        else:
            Notification.new(user, "Подтвердите почту",
                             "Вам на почту пришло письмо для подтверждения почты", "/profile/", True, True)

        from utils.models import Constant
        settings_options_obj: dict = Constant.get("settings_options", "json")
        bonus_lifetime = int(
            settings_options_obj["registration_bonuses"]["lifetime"])
        bonus_value = int(
            settings_options_obj["registration_bonuses"]["value"])

        Bonus_rubles.objects.create(
            user=user,
            value=bonus_value,
            lifespan=bonus_lifetime,
            text="Получено за регистрацию"
        )

        FinancialOperation.new(
            user, bonus_value, True, "user", "Получено за регистрацию")

    uLogin(request, user)
    return render(request, 'user/page_back_url_login_page.html')


def confirmation_email_address(request):
    code = request.GET.get("code")

    if code == None or code == "" or len(code) < 25:
        raise Http404('Не найден пользователь')

    user: User = User.objects.filter(active_code_email=code).first()

    if user:
        user.active_email = True
        user.save()
        return render(request, 'user/page_back_url_login_page.html')
    else:
        raise Http404('Не найден пользователь')


def download_the_application_file(request):

    return render(request, 'main/dtaf.html')


def format_time(seconds):
    seconds *= 1000
    if seconds < 1000:
        return f"< 1 с"
    else:
        hours = seconds // (3600 * 1000)
        minutes = (seconds % (3600 * 1000)) // (60 * 1000)
        seconds = ((seconds % (3600 * 1000)) % (60 * 1000)) / 1000
        return f"{hours:02.0f} ч {minutes:02.0f} мин {seconds:02.0f} с"


def fast_code_execution():
    from hotel.models import Hotel, ModerWork
    """
cd /var/www/www-root/data/www/turgorodok.ru/venv/
source bin/activate
python manage.py shell

from user.urls_views.views.other import fast_code_execution
fast_code_execution()
    """

    hotels = Hotel.objects.filter(id__in=[29107, 209, 210])

    for hotel in hotels:
        moder_work = ModerWork.objects.create(
            moder=User.objects.get(id=1),
            user=hotel.owner,
        )

        for hotel in hotel.owner.hotels.all():
            moder_work.hotels.add(hotel)
    print("Работа создана")


def all_reset_place_position():
    from hotel.models import Hotel
    count_ok = 0

    hotels = Hotel.objects.all()[25254:30000]

    pbar = tqdm(total=hotels.count(), unit='шт', desc=f"Отели: ")

    completed_list = {
        "full_count": 0,
        "one": 0,
    }

    for hotel in hotels:
        try:
            resutl = hotel.reset_place_position()

            completed_list["full_count"] += 1

            if resutl["type"] == "one":
                completed_list["one"] += 1

            count_ok += 1
        except:
            pass

        pbar.update(1)

    print(completed_list)


def calc_hotel_overall_rating():
    from hotel.models import Hotel

    count_ok = 0

    hotels = Hotel.objects.all()
    pbar = tqdm(total=hotels.count(), unit='шт', desc="Отелей")

    for hotel in hotels:
        hotel.calc_overall_rating()
        count_ok += 1
        pbar.update(1)

    return JsonResponse({"count_ok": count_ok})


def run_loader_hotel_from_parser():
    from hotel.models import Hotel, Address, RCategory, Comment
    hotels_count_exactly = 0
    hotels_count_not_found = 0
    hotels_count_room_not_found = 0

    hotels_reviews_list = []

    with open("media/valid_reviews.json", encoding='utf-8') as f:
        data = json.load(f)
        hotels_reviews_list = data

    hotels_reviews_list_count = len(hotels_reviews_list)

    time_start = time.time()

    for index, hotel_review in enumerate(hotels_reviews_list):
        hotel = hotel_review["hotel"]

        name_hotel = hotel["name_hotel"]
        coordinates = str(hotel["coordinates"]["latitude"]) + \
            ", " + str(hotel["coordinates"]["longitude"])

        is_such_review = Comment.objects.filter(
            hotel__name=name_hotel, author_name=hotel_review["author_name"], author_room=hotel_review["author_room"]).exists()
        if not is_such_review:
            hotel_qs = Hotel.objects.filter(
                name=name_hotel, adrress_hotel__coordinates=coordinates).first()
            if hotel_qs:
                rcategory: RCategory = hotel_qs.rcategory_hotel.filter(
                    name=hotel_review["author_room"]).first()
                review_date_text = hotel_review["review_date"].replace(
                    ' ', 'T')
                review_date_text = review_date_text.replace('+00', '')

                try:
                    review_date = datetime.datetime.strptime(
                        review_date_text, '%Y-%m-%dT%H:%M:%S.%f')
                except:
                    review_date = datetime.datetime.strptime(
                        review_date_text, '%Y-%m-%dT%H:%M:%S')

                if rcategory:
                    hotels_count_exactly += 1

                    try:
                        Comment.objects.create(
                            hotel=hotel_qs,
                            rc=rcategory,
                            author_name=hotel_review["author_name"],
                            author_room=rcategory.name,
                            data=review_date,
                            location=hotel_review["detailed"]["location"],
                            price_quality_ratio=hotel_review["detailed"]["price"],
                            purity=hotel_review["detailed"]["cleanness"],
                            food=hotel_review["detailed"]["services"],
                            service=hotel_review["detailed"]["services"],
                            number_quality=hotel_review["detailed"]["room"],
                            hygiene_products=hotel_review["detailed"].get(
                                "hygiene", "no"),
                            wifi_quality=hotel_review["detailed"].get(
                                "wifi_quality", "missing"),
                            what_is_good_text=hotel_review.get(
                                "review_plus", ""),
                            what_is_bad_text=hotel_review.get(
                                "review_minus", ""),
                        )
                    except:
                        pass

                else:
                    try:
                        Comment.objects.create(
                            hotel=hotel_qs,
                            rc=None,
                            author_name=hotel_review["author_name"],
                            author_room=hotel_review["author_room"],
                            data=review_date,
                            location=hotel_review["detailed"].get(
                                "location", 0),
                            price_quality_ratio=hotel_review["detailed"].get(
                                "price", 0),
                            purity=hotel_review["detailed"].get(
                                "cleanness", 0),
                            food=hotel_review["detailed"].get("meal", 0),
                            service=hotel_review["detailed"].get(
                                "services", 0),
                            number_quality=hotel_review["detailed"].get(
                                "room", 0),
                            hygiene_products=hotel_review.get("hygiene", "no"),
                            wifi_quality=hotel_review.get(
                                "wifi_quality", "missing"),
                            what_is_good_text=hotel_review.get(
                                "review_plus", ""),
                            what_is_bad_text=hotel_review.get(
                                "review_minus", ""),
                        )
                    except:
                        pass

                    hotels_count_room_not_found += 1
            else:
                hotels_count_not_found += 1
        else:
            hotels_count_exactly += 1

        if index % 25 == 0:
            with open('media/hotels_count.json', 'w', encoding='utf-8') as f:
                json.dump({
                    "last_index": index,
                    "exactly": hotels_count_exactly,
                    "room_not_found": hotels_count_room_not_found,
                    "not_found": hotels_count_not_found,
                }, f, ensure_ascii=False, indent=4)

            procent = round(((index + 1) / hotels_reviews_list_count) * 100, 2)

            if hotels_count_exactly > 0:
                procent_exactly = ((hotels_count_exactly) / (index + 1)) * 100
            else:
                procent_exactly = 0

            if hotels_count_room_not_found > 0:
                procent_room_not_found = (
                    (hotels_count_room_not_found) / (index + 1)) * 100
            else:
                procent_room_not_found = 0

            if hotels_count_not_found > 0:
                procent_not_found = (
                    (hotels_count_not_found) / (index + 1)) * 100
            else:
                procent_not_found = 0

            # Сколько прошло времени
            d_time = time.time() - time_start
            d_time_text = format_time(d_time)

            # Сколько примерно вермени осталось
            if index > 0:
                about_time_left = (d_time / index) * hotels_reviews_list_count
                about_time_left_text = format_time(about_time_left)

                print(f"Время: {d_time_text} ~ {about_time_left_text}")

            print(
                f"Сделано: [{procent:06.02f}%] {index + 1} из {hotels_reviews_list_count}")
            print(
                f"Найден - объект и номер: [{procent_exactly:06.02f}%] {hotels_count_exactly})")
            print(
                f"Найден - объект: [{procent_room_not_found:06.02f}%] {hotels_count_room_not_found})")
            print(
                f"Не найдено: [{procent_not_found:06.02f}%] {hotels_count_not_found})")
            print("=======================")

    content = {
        "ok": True,
    }

    return JsonResponse(content, safe=False)


def api_upform_auth_phone_create_code(request: HttpRequest):
    from user.cabapi import flashcall
    if request.method == 'POST':

        post_phone = request.POST.get("phone")

        flashcall_response = flashcall(post_phone)
        if flashcall_response["status"] == "ok":
            active_code_phone = flashcall_response["data"]["pincode"]
            request.session["active_code_phone"] = active_code_phone
            return JsonResponse({
                "status": "success",
                "upform": {
                    "type": "form.change",
                    "options": {
                        "type": "login",
                        "tab": "sms_2",
                    }
                }
            }, status=200)
        else:
            return JsonResponse({
                "status": "error",
                "error": {
                    "code": "request.flashcall.call_was_not_created",
                },
                "upform": {
                    "type": "form.custom.message",
                    "сontrols": {
                        "title": {
                            "label": "Ошибка"
                        },
                        "text": {
                            "label": "Звонок на телефон невозможно создать проверте правильность написания номера телефона или попробуйдет другой формат написания"
                        },
                    }
                },
            }, status=500)

    else:
        return JsonResponse({
            "status": "error",
            "error": {
                "code": "request.method.not_post",
            },
            "message": {
                "type": "error",
                "text": "Запрос пришёл на сервер не в формате POST"
            }
        }, status=405)


def api_upform_auth_phone_check_code(request: HttpRequest):
    from user.cabapi import flashcall
    if request.method == 'POST':

        post_code = request.POST.get("phone_code", "")
        post_phone = request.POST.get("phone", "")

        user = User.objects.filter(phone=post_phone).first()


        if len(post_code) == 4 and request.session.get("active_code_phone") == post_code:
            if not user:
                user = User.objects.create_user(
                        username="",
                        lastname="",
                        middlename="",
                        email="",
                        login="",
                        password="",
                        gender="Мужской",
                        phone=post_phone.strip(),
                        ignor_valid=True,
                    )

            user.active_phone = True
            user.save()

            uLogin(request, user)
            if request.session.get("active_code_phone"):
                del request.session["active_code_phone"]

            return JsonResponse({
                "status": "success",
                "upform": {
                    "type": "reload",
                },
            }, status=200)
        else:
            return JsonResponse({
                "status": "error",
                "error": {
                    "code": "request.flashcall.invalid_code",
                },
                "upform": {
                    "type": "form.custom.message",
                    "сontrols": {
                        "title": {
                            "label": "Ошибка"
                        },
                        "text": {
                            "label": "Не верный код"
                        },
                    }
                },
            }, status=200)

    else:
        return JsonResponse({
            "status": "error",
            "error": {
                "code": "request.method.not_post",
            },
            "message": {
                "type": "error",
                "text": "Запрос пришёл на сервер не в формате POST"
            }
        }, status=405)


def api_upform_auth_normal_reg(request: HttpRequest):
    if request.method == 'POST':

        post_fio = request.POST.get("fio")
        post_email = request.POST.get("email")
        post_phone = request.POST.get("phone")
        # post_login = request.POST.get("login")
        post_password = request.POST.get("password")
        post_repeat_password = request.POST.get("repeat_password")

        if post_password != post_repeat_password:
            return JsonResponse({
                "status": "error",
                "upform": {
                    "type": "render.valid",
                    "сontrols": {
                        "values": {
                            "repeat_password": {
                                "errors": ["Пароли не совпадают"]
                            },
                            "password": {
                                "errors": ["Пароли не совпадают"]
                            }
                        }
                    }
                }
            }, status=200)

        fio = post_fio.split(" ")
        middlename, username, lastname = None, None, None

        if len(fio) == 3:
            middlename = fio[2].strip()
        if len(fio) >= 2:
            username, lastname = fio[0].strip(), fio[1].strip()

        email = post_email.strip()
        phone = post_phone.strip()
        password = post_password.strip()

        user = None

        user_Q = Q(username=username, lastname=lastname)

        if middlename:
            user_Q &= Q(middlename=middlename)

        if post_email:
            user_Q |= Q(email=email)
            user_Q |= Q(login=email)

        if post_phone:
            user_Q |= Q(phone=phone)
            user_Q |= Q(login=phone)

        user = User.objects.filter(user_Q).first()

        if user:
            return JsonResponse({
                "status": "error",
                "upform": {
                    "type": "render.valid",
                    "values": {
                            "fio": {
                                "errors": ["Такой пользователь уже существует"]
                            },
                        "email": {
                                "errors": ["Такой пользователь уже существует"]
                            },
                        "phone": {
                                "errors": ["Такой пользователь уже существует"]
                            },
                    }
                }
            }, status=200)

        active_code_email = generate_password(30)

        user: User = User.objects.create_user(
            username=username,
            lastname=lastname,
            middlename=middlename,
            email=email,
            login=email,
            password=password,
            gender="Мужской",
            phone=phone,
            active_code_email=active_code_email,
            # active_code_phone="54j6kg47",
        )

        user.additional_info["password"] = password
        user.save()

        confirmation_email_address_url = request.build_absolute_uri(
            reverse("confirmation_email_address")) + f"?code={active_code_email}"

        if my_mail.send("confirmation_email_address", "Подтвердите свою почту на сайте", email, {"confirmation_email_address_url": confirmation_email_address_url}) == False:
            Notification.new(user, "Вы вели неправильную почту",
                             "", "/profile/", True, True)
        else:
            Notification.new(user, "Подтвердите почту",
                             "Вам на почту пришло письмо для подтверждения почты", "/profile/", True, True)

        from utils.models import Constant
        settings_options_obj: dict = Constant.get("settings_options", "json")
        bonus_lifetime = int(
            settings_options_obj["registration_bonuses"]["lifetime"])
        bonus_value = int(
            settings_options_obj["registration_bonuses"]["value"])

        Bonus_rubles.objects.create(
            user=user,
            value=bonus_value,
            lifespan=bonus_lifetime,
            text="Получено за регистрацию"
        )

        FinancialOperation.new(user, bonus_value, True,
                               "user", "Получено за регистрацию")
        uLogin(request, user)

        return JsonResponse({
            "status": "success",
            "upform": {
                "type": "reload",
            }
        }, status=200)

    else:
        return JsonResponse({
            "status": "error",
            "error": {
                "code": "request.method.not_post",
            },
            "message": {
                "type": "error",
                "text": "Запрос пришёл на сервер не в формате POST"
            }
        }, status=405)


def api_upform_auth_normal_login(request: HttpRequest):
    if request.method == 'POST':
        post_login = request.POST.get("login")
        post_password = request.POST.get("password")

        login = post_login.strip()
        password = post_password.strip()

        user = None

        user = MyUserManager.authenticate(login=login, password=password)

        if not user:
            return JsonResponse({
                "status": "error",
                "upform": {
                    "type": "render.valid",
                    "values": {
                        "login": {
                            "errors": ["Не верный логин или пароль"]
                        },
                        "login": {
                            "errors": ["Не верный логин или пароль"]
                        },
                    }
                }
            }, status=200)

        uLogin(request, user)

        return JsonResponse({
            "status": "success",
            "upform": {
                "type": "reload",
            }
        }, status=200)

    else:
        return JsonResponse({
            "status": "error",
            "error": {
                "code": "request.method.not_post",
            },
            "message": {
                "type": "error",
                "text": "Запрос пришёл на сервер не в формате POST"
            }
        }, status=405)


def api_upform_auth_forget_password(request: HttpRequest):
    if request.method == 'POST':
        post_email = request.POST.get("email")

        email = post_email.strip()

        user = None

        user = User.objects.filter(email=email).first()


        if user:
            url_reset_password = request.build_absolute_uri(reverse("page_reset_password"))
            url_reset_password += f"?user_id={user.id}&access_token={user.get_access_token()}"

            my_mail.send("reset_password", "Сброс пароля",  email, {"url": url_reset_password})

            return JsonResponse({
                "status": "success",
                "upform": {
                    "type": "form.custom.message",
                    "сontrols": {
                        "title": {
                            "label": "Письмо отправлено"
                        },
                        "text": {
                            "label": "Инструкции по восстановлению пароля отправлены на ваш email."
                        },
                    }
                },
            }, status=200)
        else:
            return JsonResponse({
                "status": "error",
                "upform": {
                    "type": "render.valid",
                    "values": {
                        "email": {
                            "errors": ["Пользователь с такой почтой отсутствует"]
                        },
                    }
                }
            }, status=200)


    else:
        return JsonResponse({
            "status": "error",
            "error": {
                "code": "request.method.not_post",
            },
            "message": {
                "type": "error",
                "text": "Запрос пришёл на сервер не в формате POST"
            }
        }, status=405)