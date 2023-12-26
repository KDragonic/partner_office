import datetime
import json
from typing import List, Optional, Tuple, Union
from django.db import models
from django.db.models.query import QuerySet
from django.utils.functional import SimpleLazyObject
from brontur.funs import get_str_model
from django.http import HttpRequest
from django.db.models import Q

class Chat(models.Model):
    users = models.ManyToManyField('user.User', related_name="chats", blank=True)
    messages = models.ManyToManyField("Message", related_name="chat", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict, null=True, blank=True)

    def __str__(self):
        try:
            return f'Чат {self.booking.id} ({self.booking.created_at.strftime("%d.%m.%Y %H:%M")})'
        except:
            return f'Чат {self.id}'

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'

    def check_messages_read_all(self, chat_user) -> bool:
        """
        Проверяет, все ли сообщения в чате были прочитаны пользователем.

        Args:
            user_id (int): id пользователя.

        Returns:
            bool: True, если все сообщения прочитаны, в противном случае - False.
        """

        if self.messages:
            latest_message = self.messages.latest('datetime')
            read_user = latest_message.read_user.all()
            is_chat_user_in_read_user = read_user.filter(id=chat_user.id).exists()
            return is_chat_user_in_read_user
        return False

    def get_the_number_of_unread(self, user):
        unread_count = 0
        for mess in self.messages.all():
            read_user = mess.read_user.all()
            if not read_user.filter(id=user.id).exists():
                unread_count += 1

        return unread_count

    def add_info_message(self, type: str, param: dict = {}):
        mess = Message.objects.create(
            text=type,
            param=param,
            datetime=datetime.datetime.now(),
            user=None,
        )
        self.messages.add(mess)
        return mess

    def get_all(user : "User"):
        return Chat.objects.filter(users__id=user.id)

    def get_all_booking(user : "User"):
        from hotel.models import Booking
        all_chat = Chat.objects.all()
        chats = []

        for chat in all_chat:
            booking_id = chat.data.get("booking")

            if booking_id == None or booking_id == "":
                continue


            booking : Booking = Booking.objects.filter(id=booking_id).first()
            owner_hotel = booking.booked_room.category.hotel.owner

            if owner_hotel == user:
                chats.append(chat)

        return chats


    def available_to_the_user(self, request: HttpRequest) -> str:
        from user.models import User
        # Получаем данные
        # url = request.build_absolute_uri()
        url = request.META.get('HTTP_REFERER')
        user : User = User.objects.get(id=request.user.id)

        if "admin/page/ts/chat/" in url:
            if user.is_admin or \
                user.is_superuser or \
                user.user_type in ["admin", "moder", "owner"]:
                    return user.user_type

        elif "techsupport/chat" in url:
            if user.user_type in ["hotel", "client", "admin", "moder", "owner"]:
                if self.users.filter(id=user.id).exists():
                    return User


        elif "profile/chat" in url:
            if user.user_type in ["hotel", "client", "admin", "moder", "owner"]:
                if self.users.filter(id=user.id).exists():
                    return "client"

        elif "profile/hotel/chat" in url:
            if user.user_type in ["hotel", "admin", "moder", "owner"]:
                if self.users.filter(id=user.id).exists():
                    return "hotel"

        elif "profile/chats" in url:
            if self.users.filter(id=user.id).exists():
                return user.user_type

        return None


    def get_not_read_messages(self, user : "User") -> QuerySet["Message"]:
        """
        Получает список всех сообщений в чате, отсортированных по дате и времени отправки.

        Args:
            chat (Chat): Объект модели Chat.

        Returns:
            list: Список объектов модели Message.
        """
        messages = self.messages.filter(~Q(read_user=user))
        return messages

    def get_personal_chat(user):
        chats = Chat.objects.filter(Q(**{'data__type': 'personal'}, users=user))
        if chats.exists():
            chat = chats.first()
        else:
            chat = Chat.objects.create(
                data={
                    "type": "personal",
                }
            )
            chat.users.add(user)

        return chat



class Message(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)  # Дата и время сообщения
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, null=True, blank=True, related_name="chat_message")
    text = models.TextField(null=True, blank=True)
    param = models.JSONField(default=dict, null=True, blank=True)
    read_user = models.ManyToManyField('user.User', related_name="read_messages", blank=True)

    def __str__(self):
        try:
            return f'({self.user.username [self.user.user_type]}) - {self.text}'
        except:
            return f'(Без пользователя) - {self.text}'

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def get_all_messages(chat: Chat) -> QuerySet["Message"]:
        """
        Получает список всех сообщений в чате, отсортированных по дате и времени отправки.

        Args:
            chat (Chat): Объект модели Chat.

        Returns:
            list: Список объектов модели Message.
        """
        messages = chat.messages.all().order_by('datetime')
        return messages