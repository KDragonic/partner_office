import random
from django.db import models
from hotel.models import Hotel
from user.models import Notification, User


def gen_rid():
    list_part = {}
    char = list('1234567890abcdefghigklmnopqrstuvyxwzABCDEFGHIGKLMNOPQRSTUVYXWZ')
    for i in range(4):
        list_part[i] = ""
        for x in range(4):
            list_part[i] += random.choice(char)

    return f"{list_part[0]}-{list_part[1]}-{list_part[2]}-{list_part[3]}"


class Request(models.Model):
    rid = models.CharField(max_length=19, unique=True, verbose_name="ID")
    text = models.TextField(verbose_name="Сообщения")
    title = models.CharField(max_length=100, verbose_name="Название")
    title = models.CharField(max_length=100, verbose_name="Название")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    status = models.CharField(max_length=20, default="start", verbose_name="Статус")
    answered = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="Кто ответил")

    def add(title, text, user):
        request = Request.objects.create(title=title, text=text, rid=gen_rid())
        request.save()

        link_h = Link_U.objects.create(request=request, user=user)
        link_h.save()
        admins = User.objects.filter(user_type__in=["moder", "admin"])
        for admin in admins:
            Notification.new(admin, "Пришел запрос в техподдержку", f"{title}<br>{text}")

    def add(title, text, hotel):
        request = Request.objects.create(title=title, text=text, rid=gen_rid())
        request.save()

        link_h = Link_H.objects.create(request=request, hotel=hotel)
        link_h.save()

    def __str__(self):
        return f'{self.title} - {self.text}'

    class Meta:
        verbose_name = 'Запрос'
        verbose_name_plural = 'Запросы'


class Link_H(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, verbose_name="Отель")
    request = models.OneToOneField(Request, on_delete=models.CASCADE)


    class Meta:
        verbose_name = 'Связь Запрос-Отель'
        verbose_name = 'Связь Запрос-Отель'


class Link_U(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    request = models.OneToOneField(Request, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Связь Запрос-Пользователь'
        verbose_name = 'Связь Запрос-Пользователь'
