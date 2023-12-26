from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from hotel.models import Hotel
from user.models import Notification, User
from .models import Request
from chat.models import Chat, Message
from django.db.models import Q



@login_required
def page_chat(request):
    user = User.normal(request.user)

    chats_qs = Chat.objects.filter(Q(users__id=request.user.id) & (Q(data__type = "ts") | Q(data__type='personal')))

    if len(chats_qs) == 0:
        return redirect("techsupport.pattern")


    full_chat = None
    chat_id = request.GET.get("chat")
    chats = []

    if chat_id: #TODO: Поправить тут потом чтоб нельзя было через тех подершку баги делать если URL поменять
        chat_qs = Chat.objects.filter(id=chat_id)
        if chat_qs.exists():
            full_chat = chat_qs.first().id

    url : str = request.build_absolute_uri()

    page = ""
    if url.find("techsupport/chat/") >= 0:
        page = "techsupport.chat"
        url_base = "/techsupport/chat/"

    elif url.find("admin/page/ts/chat/") >= 0:
        page = "admin.techsupport.chat"
        url_base = "admin/page/ts/chat/"


    for chat_item in chats_qs:
        try:
            data : dict = chat_item.data

            title = data.get("title")
            status = data.get("status")
            chat_type = data.get("type")

            param = {
                "status": status,
                "start": chat_item.created_at.strftime("%d.%m.%Y"),
                "title": title if title else "Без темы",
                "url": url_base + f"?chat={chat_item.id}",
                "user_id": chat_item.users.all().first().id,
                "id": chat_item.id,
                "chat_type": chat_type,
                "not_read_messages_count": chat_item.get_not_read_messages(request.user.normal()).count()
            }

            chats.append(param)
        except:
            continue

    chats.reverse()

    content = {"full_chat": full_chat, "chats": chats}
    return render(request, 'user/ts_chat.html', content)


@login_required
def create_ts(request):
    title = request.POST.get("title")
    text = request.POST.get("text")


    if not title or len(title) == 0:
        return

    if not text or len(text) == 0:
        return

    user = User.normal(request.user)

    chat = Chat.objects.create(
        data = {
            "type": "ts",
            "title": title,
            "text": text,
        }
    )

    chat.users.add(user)

    chat.add_info_message("ts.start", {
        "title": title,
        "text": text,
    })


    admins = User.objects.filter(user_type__in=["moder", "admin", "owner"])
    url_to_admin = reverse("admin.page.ts.chat") + f"?chat={chat.id}"
    for admin in admins:
        Notification.new(admin, "Новый запрос в техподдержку", f"[{title}] {text}", url_to_admin, True, True)

    url = reverse("profile_v2_chats") + f"?chat={chat.id}&chat_type=techsupport"

    return JsonResponse({"result": "ok", "chat_url": url})

def page_tpl_ts(request):
    type = request.GET.get("type")
    if type == "register_hotel":
        title = "Помощь в регистрации объекта размещения"
        user = request.user
        username = user.username
        lastname = user.lastname
        middlename = user.middlename
        phone = user.phone
        email = user.email

        if lastname == '':
            lastname = ""

        if middlename == '':
            middlename = ""

        if phone == '':
            phone = "+123456789"


        if email == '':
            email = "email@email.com"

        text = f"Здравствуйте, меня зовут {username} {lastname} {middlename}, мне нужна помощь в регистрации объекта размещения на сайте. Связаться со мной можно: написать в чат сайта, позвонить по телефону {phone} или написать на почту {email}"
        return render(request, 'user/ts_create.html', {"title": title, "text": text})
    return render(request, 'user/ts_create.html')
