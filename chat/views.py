import datetime
import re
import time
from django.shortcuts import render

from utils.models import Img
from .models import *
from django.http import JsonResponse
from hotel.models import Booking, GroupBooking, Hotel, RCategory
from user.models import Notification, User
from django.db.models.query import QuerySet
from django.db.models import Max


def hide_contact_info(text):
    # шаблон для поиска номера телефона
    phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
    email_pattern = r"\b[^\s@]*@[^\s@]*[^\s]\b"
    # шаблон для поиска номера кредитной карты
    payment_pattern = r"\b(\d{4}[- ]?){3}\d{4}\b"
    # шаблон для поиска других контактов (Skype, Viber и т.д.)
    skype_pattern = r"\bskype\b|\bviber\b"
    url_pattern = r'(https?://\S+)'  # шаблон для поиска ссылок
    # шаблон для поиска нижнего подчеркивания в тексте
    underscore_pattern = r"\\b\\w+_\\w+\\b"

    for pattern in [phone_pattern, email_pattern, payment_pattern, skype_pattern, url_pattern, underscore_pattern]:
        text = re.sub(
            pattern, lambda match: '<div class="info_hide">' + '●●●●●' + '</div>', text)

    return text


def get_chat(request):
    chat_id = request.POST.get('chat')

    url = request.META.get('HTTP_REFERER')

    page = ""
    if str.find(url, "profile/hotel/chat/") >= 0:
        page = "hotel.chat"

    elif str.find(url, "profile/chat/") >= 0:
        page = "client.chat"

    elif str.find(url, "techsupport/chat/") >= 0:
        page = "techsupport.chat"

    elif str.find(url, "admin/page/ts/chat/") >= 0:
        page = "admin.techsupport.chat"

    if chat_id != None:
        user: User = User.objects.get(id=request.user.id)
        chat = Chat.objects.get(id=chat_id)

        is_allowed_user_type = \
            (user.user_type in ["hotel", "admin", "moder", "owner"] and page == "hotel.chat") or \
            (user.user_type in ["client", "hotel", "admin", "moder", "owner"] and page == "client.chat") or \
            (user.user_type in ["client", "hotel", "admin", "moder", "owner"] and page == "techsupport.chat") or \
            (user.user_type in ["admin", "moder", "owner"]
                and page == "admin.techsupport.chat")

        content = {}

        if is_allowed_user_type:
            users = chat.users.all()
            content = {
                "id": chat.id,
                "date_start": chat.created_at,
                "user_id": users.first().id
            }

        # Что броней несколько чтоб они были в одном чате
        booking_id = chat.data.get("booking")
        g_booking: GroupBooking = GroupBooking.objects.filter(
            bookings__id=booking_id).first()
        if g_booking:
            bookings = list(
                g_booking.bookings.all().values_list("id", flat=True))

            chats = list(Chat.objects.filter(
                data__booking__in=bookings).values("id", "data"))

            if len(chats) > 0:
                content["group_booking"] = chats

        if is_allowed_user_type:
            return JsonResponse({"result": True, "chat": content})

    return JsonResponse({"result": False})


def check_for_new_messages(chat: Chat, user: User):
    return not chat.check_messages_read_all(user)


def messages(request):
    chat_id = int(request.GET.get('chat'))
    isRestart = request.GET.get('isRestart')
    chat = Chat.objects.get(pk=chat_id)
    user: User = request.user.normal()

    # Получения типа пользователя, пусто если он не соотвествет странице
    user_type = chat.available_to_the_user(request)

    if user_type == None:
        return JsonResponse({"status": "no_access"})

    if isRestart == "true":
        if not check_for_new_messages(chat, user):
            return JsonResponse({"status": "not_now_messages"})

    messages: QuerySet[Message] = Message.get_all_messages(chat)

    result_messages = []

    for mess in messages.filter(~Q(read_user=user)):
        mess.read_user.add(user)

    for message in messages:

        type_message = ""

        message_user_obj = message.user
        message_user = None
        if message_user_obj:
            message_user: User = User.normal(message_user_obj)
            if message_user.user_type in ["admin", "moder", "owner"]:
                type_message = "admin"
            else:
                type_message = message_user.user_type
        else:
            type_message = "info"

        show = False

        if chat.data["type"] in ["ts", "personal"]:
            show = True

        elif type_message == "info":
            show = False

            if user_type in ["admin", "moder", "owner"]:
                show = True

            if message.text in ["hotel.start.chat", "hotel.edit.booking", "registered_hotel"] and user_type in ["hotel"]:
                show = True

            if message.text in ["user.start.chat", "user.edit.booking", "user.add.bonus.booking_left"] and user_type in ["client"]:
                show = True

        else:
            show = True

        if show == False:
            continue

        message_datetime = message.datetime + datetime.timedelta(hours=3)

        if message.param.get("img"):
            file = Img.objects.filter(id=message.param["img"]).first()
        else:
            file = None

        result = {
            "text": message.text,
            "file_url": file.image.url if file else None,
            "belong": type_message,
            "time": message_datetime.time().strftime("%H:%M"),
            "date": message_datetime.date(),
        }

        if user.user_type in ["admin", "moder", "owner"]:
            result["admin_info"] = []
            admin_info_read_user = []
            for u_obj in message.read_user.all():
                color = "black"
                if u_obj.id in message.read_user.filter(user_type__in=["hotel", "client"]).values_list("id", flat=True):
                    color = "#ff0000"

                admin_info_read_user.append({"name": str(u_obj), "color": color})

            if message.user != None:
                result["admin_info"].append(["Кто написал", str(message.user)]),
            result["admin_info"].append(["Кто прочитал", admin_info_read_user])


        if type_message == "hotel":
            hotel = Hotel.objects.filter(owner=message_user).first()
            imgs = Img.get_url("hotel.hotel", hotel.id, 0)
            result["avatar"] = imgs[0]["url"] if len(imgs) > 0 else ""

        main_content = message.text


        if type_message == "info":
            if chat.data.get("booking"):
                booking: Booking = Booking.objects.get(
                    id=chat.data.get("booking"))

            if message.text == "user.start.chat":
                main_content = f"""
                <a href="/profile/booking/?id={booking.id}" class="info_card_name">Бронирование {booking.id}</a>
                <a href="/hotel/{booking.booked_room.category.hotel.id}/" class="info_card_hotel">{booking.booked_room.category.hotel.name}</a>
                <span class="info_card_text">{booking.booked_room.category.name}</span>
                <span class="info_card_text">Заезд: {booking.start_date_time.strftime("%d.%m.%Y %H:%M")}</span>
                <span class="info_card_text">Выезд: {booking.end_date_time.strftime("%d.%m.%Y %H:%M")}</span>
                <span class="info_card_text">Стоймость бронирования: {booking.site_price} р</span>
                <span class="info_card_text">Доплата отелю: {booking.hotel_price} р</span>
                <span class="info_card_text" style="color: gray; letter-spacing: 1px; ">{message_datetime.strftime("%d.%m.%Y %H:%M:%S")}</span>
                """
            elif message.text == "hotel.start.chat":
                main_content = f"""
                <a href="/profile/hotel/booking/?id={booking.id}" class="info_card_name">Бронирование {booking.id}</a>
                <span class="info_card_text">{booking.booked_room.category.name}</span>
                <span class="info_card_text">Заезд: {booking.start_date_time.strftime("%d.%m.%Y %H:%M")}</span>
                <span class="info_card_text">Выезд: {booking.end_date_time.strftime("%d.%m.%Y %H:%M")}</span>
                <span class="info_card_text">Стоймость бронирования: {booking.site_price} р</span>
                <span class="info_card_text">Доплата отелю: {booking.hotel_price} р</span>
                <span class="info_card_text" style="color: gray; letter-spacing: 1px; ">{message_datetime.strftime("%d.%m.%Y %H:%M:%S")}</span>
                """
            elif message.text == "hotel.edit.booking":
                status_text = dict(Booking.STATUS_CHOICES).get(
                    message.param["status"])
                main_content = f"""
                <a href="/profile/hotel/booking/?id={booking.id}" class="info_card_name">Бронирование {booking.id}</a>
                <span class="info_card_text">Вы изменили статус бронирования на <span class="status_text_color_{message.param["status"]}">{status_text}</span></span>
                <span class="info_card_text" style="color: gray; letter-spacing: 1px; ">{message_datetime.strftime("%d.%m.%Y %H:%M:%S")}</span>
                """

            elif message.text == "user.edit.booking":
                status_text = dict(Booking.STATUS_CHOICES).get(
                    message.param["status"])
                main_content = f"""
                <a href="/profile/booking/?id={booking.id}" class="info_card_name">Бронирование {booking.id}</a>
                <span class="info_card_text">Статус бронирования изменён на <span class="status_text_color_{message.param["status"]}">{status_text}</span></span>
                <span class="info_card_text" style="color: gray; letter-spacing: 1px; ">{message_datetime.strftime("%d.%m.%Y %H:%M:%S")}</span>
                """

            elif message.text == "user.add.bonus.booking_left":
                main_content = f"""
                <a href="/profile/booking/?id={booking.id}" class="info_card_name">Бронирование {booking.id}</a>
                <span class="info_card_text">За проживание вам начислено бонусы: {message.param["count"]}</span>
                <span class="info_card_text" style="color: gray; letter-spacing: 1px; ">{message_datetime.strftime("%d.%m.%Y %H:%M:%S")}</span>
                """

            elif message.text == "ts.start":
                title = message.param.get("title")
                text = message.param.get("text")

                main_content = f"""
                <div class="info_card_name">{title if title else "Без название"}</div>
                <span class="info_card_text">{text if text else "Без текста"}</span>
                <span class="info_card_text" style="color: gray; letter-spacing: 1px; ">{message_datetime.strftime("%d.%m.%Y %H:%M:%S")}</span>
                """

            elif message.text == "moderation.status":
                success = message.param.get("success")
                comment = message.param.get("comment")

                comment = comment if (
                    comment != "" or comment != None) else "Комментария нету"

                if success == True:
                    main_content = f"""
                    <a href="/profile/hotel/" class="info_card_name">Модерация прошла успешно</a>
                    <span class="info_card_text">{comment}</span>
                    <span class="info_card_text" style="color: gray; letter-spacing: 1px; ">{message_datetime.strftime("%d.%m.%Y %H:%M:%S")}</span>
                    """

                if success == False:
                    main_content = f"""
                    <a href="/profile/hotel/" class="info_card_name">Модерация не пройдена</a>
                    <span class="info_card_text">{comment}</span>
                    <span class="info_card_text" style="color: gray; letter-spacing: 1px; ">{message_datetime.strftime("%d.%m.%Y %H:%M:%S")}</span>
                    """

            elif message.text == "about_help":
                main_content = f"""
                <span class="info_card_text">Обращаем Ваше внимание, что для удобства работы наших партнеров мы сделали Частые вопросы, которую можно найти во вкладке "FAQ".</span>
                <span class="info_card_text">Пожалуйста, обращайтесь, если у Вас возникнут вопросы в этот чат или создайте новый запрос чтоб не потерять его.</span>
                <span class="info_card_text" style="color: gray; letter-spacing: 1px; ">{message_datetime.strftime("%d.%m.%Y %H:%M:%S")}</span>
                """

            elif message.text == "registered_hotel":
                main_content = f"""
                    <span class="info_card_text">Добрый день, уважаемый партнер!</span><br>
                    <span class="info_card_text">Благодарим вас за регистрацию объекта в turgorodok.ru</span><br>
                    <span class="info_card_text">-В личном кабинете заполнить полностью информацию о Вашем объекте. Добавить категории номеров и указать количество однотипных номеров.</span><br>
                    <span class="info_card_text">-Если у вас есть еще номера, то зайдите в управление категории номеров и создайте еще один номер, если нет, то зайдите в управление номерами.</span><br>
                    <span class="info_card_text" style="color: gray; letter-spacing: 1px; ">{message_datetime.strftime("%d.%m.%Y %H:%M:%S")}</span>
                """

            result["text"] = f"""
            <div class="media media-info">
                <div class="media-body media-body-left">
                    <div class="message-body">
                        {main_content}
                    </div>
                    <div class="admin-info"></div>
                </div>
            </div>
            """

        result_messages.append(result)

    return JsonResponse({"messages": result_messages})


def send(request):
    text = request.POST.get('text')
    chat_id = request.POST.get('chat')
    chat = Chat.objects.get(pk=chat_id)
    user = User.normal(request.user.id)
    file = request.FILES.get("file")

    url = request.META.get('HTTP_REFERER')

    user_type = chat.available_to_the_user(request)

    page = ""
    if str.find(url, "admin/page/ts/chat/") >= 0:
        if user_type in ["moder", "admin", "owner"]:
            return sendTS(text, chat, user, file)

    elif str.find(url, "techsupport/chat/") >= 0:
        return sendTS(text, chat, user, file)

    elif str.find(url, "profile/hotel/chat/") >= 0:
        if user_type in ["hotel", "moder", "admin", "owner"]:
            page = "hotel.chat"

    elif str.find(url, "profile/chat/") >= 0:
        if user_type in ["client", "hotel", "moder", "admin", "owner"]:
            page = "hotel.chat"

        page = "client.chat"

    if not user:
        return JsonResponse({"result": False})

    if user:
        date = datetime.datetime.now()

        mess = Message.objects.create(text=text, user=user, datetime=date)

        if file:
            img = Img.new("chat.message", mess.id, file)
            mess.param["img"] = img.id
            mess.save()

        chat.messages.add(mess)

        chat.messages.add(mess)

        if user.user_type not in ["hotel"]:
            user_notif: User = chat.users.filter(user_type="hotel").first()
            if user_notif:
                Notification.new(user_notif, "Новое сообщение с клиентом", text,
                                 f"/profile/chats/?chat={chat.id}&chat_type=hotel_booking", True, True, send_by_mail_and_telegram=True)

        if user.user_type in ["hotel"]:
            user_notif: User = chat.users.filter(user_type="client").first()
            if user_notif:
                Notification.new(user_notif, "Новое сообщение с отелем", text,
                                 f"/profile/chats/?chat={chat.id}&chat_type=booking",  True, True, send_by_mail_and_telegram=True)

        return JsonResponse({"result": True})
    return JsonResponse({"result": False})


def sendTS(text: str, chat: Chat, user: User, file=None):
    if not user:
        return JsonResponse({"result": False})

    if user:
        date = datetime.datetime.now()
        mess = Message.objects.create(text=text, user=user, datetime=date)

        if file:
            img = Img.new("chat.message", mess.id, file)
            mess.param["img"] = img.id
            mess.save()

        chat.messages.add(mess)

        data: dict = chat.data

        if user.user_type in ["moder", "admin", "owner"]:
            user_notif: User = chat.users.filter(
                user_type__in=["client", "hotel"]).first()

            if user_notif:
                Notification.new(user_notif, "Новое сообщение в запросе", "",
                                 f"/profile/chats/?chat={chat.id}?chat_type=techsupport", True, True, send_by_mail_and_telegram=True)

        if user.user_type in ["client", "hotel"]:
            users_notif = User.objects.filter(
                user_type__in=["moder", "admin", "owner"])

            for user_notif in users_notif:
                Notification.new(user_notif, "Новое сообщение в запросе", "",
                                 f"/admin/page/ts/chat/?chat={chat.id}", True, True, send_by_mail_and_telegram=True)

        return JsonResponse({"result": True})
    return JsonResponse({"result": False})


def get_list(request: HttpRequest):

    user = request.user
    chats = []

    chat_type = request.GET.get("chat_type", "techsupport")

    count_chats_qs = 0

    content = {}

    if chat_type == "techsupport":
        chats_qs: QuerySet[Chat] = Chat.objects.filter(
            Q(users=user) & ~Q(data__type="booking"))
        count_chats_qs = len(chats_qs)

        for chat_item in chats_qs:
            try:
                buff_item = {}
                buff_item["id"] = chat_item.id
                buff_item["title"] = chat_item.data.get("title", "Без темы")
                buff_item["img"] = "/static/img/av_user_ts.png"
                buff_item["text"] = chat_item.data.get("text", "Без текста")
                chats.append(buff_item)
            except:
                pass

        chats.reverse()
        content = {"chats": chats, "count": len(
            chats), "full_count": count_chats_qs}

    elif chat_type == "booking":
        all_booking = list(Booking.objects.filter(
            booked_room__category__hotel__owner=user).values_list("id", flat=True))
        chats_qs: QuerySet[Chat] = Chat.objects.filter(Q(users=user) & Q(
            data__type="booking") & ~Q(data__booking__in=all_booking))
        count_chats_qs = len(chats_qs)

        for chat_item in chats_qs:
            try:
                booking: Booking = Booking.objects.filter(
                    id=chat_item.data["booking"]).first()
                if booking:

                    if booking.payment_status == "not_paid":
                        continue

                    rc: RCategory = booking.booked_room.category
                    buff_item = {}
                    buff_item["id"] = chat_item.id
                    buff_item["title"] = booking.booked_room.category.hotel.name
                    buff_item["img"] = booking.booked_room.category.hotel.additional_info["url_cache_phote"][0]
                    buff_item["text"] = rc.name
                    chats.append(buff_item)
            except:
                pass

        chats.reverse()
        content = {"chats": chats, "count": len(
            chats),  "full_count": count_chats_qs}

    elif chat_type == "hotel_booking":
        all_booking = list(Booking.objects.filter(
            booked_room__category__hotel__owner=user).values_list("id", flat=True))
        chats_qs: QuerySet[Chat] = Chat.objects.filter(
            Q(data__type="booking") & Q(data__booking__in=all_booking))
        count_chats_qs = len(chats_qs)

        for chat_item in chats_qs:
            try:
                booking: Booking = Booking.objects.filter(
                    id=chat_item.data["booking"]).first()
                if booking:

                    if booking.payment_status == "not_paid":
                        continue

                    rc: RCategory = booking.booked_room.category
                    buff_item = {}
                    buff_item["id"] = chat_item.id
                    buff_item["title"] = booking.booked_room.category.hotel.name
                    buff_item["img"] = booking.booked_room.category.hotel.additional_info["url_cache_phote"][0]
                    buff_item["text"] = rc.name
                    chats.append(buff_item)
            except:
                pass

        chats.reverse()
        content = {"chats": chats, "count": len(
            chats), "all_booking": all_booking,  "full_count": count_chats_qs}

    return JsonResponse(content)


def chat_load(request):
    chat_id = request.GET.get('chat')

    url = request.META.get('HTTP_REFERER')

    page = ""
    if str.find(url, "profile/chats/") >= 0:
        page = "chat_lk"

    if chat_id == None:
        return JsonResponse({"error": "There is no chat GET parameter"})

    user_id: User = request.user.id
    chat = Chat.objects.get(id=chat_id)

    is_allowed_user = chat.users.filter(id=user_id).exists()

    if not is_allowed_user:
        return JsonResponse({"error": "The chat does not belong to the user"})

    content = {}

    # Что броней несколько чтоб они были в одном чате
    booking_id = chat.data.get("booking")
    g_booking: GroupBooking = GroupBooking.objects.filter(
        bookings__id=booking_id).first()
    if g_booking:
        bookings = list(g_booking.bookings.all().values_list("id", flat=True))

        chats = list(Chat.objects.filter(
            data__booking__in=bookings).values("id", "data"))

        if len(chats) > 0:
            content["group_booking"] = chats

    return JsonResponse({"result": True, "chat": content})
