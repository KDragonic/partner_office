import os
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import admin
from .models import *
from mptt.admin import MPTTModelAdmin
from django.db.models import QuerySet, Q
from django.contrib import messages
from django_json_widget.widgets import JSONEditorWidget

# Register your models here.


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_per_page = 10000

    def action(self, obj):
        return format_html('<p style="word-wrap: break-word">{}</p>', obj.action)

    action.short_description = 'Действие'
    action.admin_order_field = 'action'

    def user(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    user.short_description = 'Пользователь'
    user.admin_order_field = 'user'

    def timestamp(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')

    timestamp.short_description = 'Временная метка'
    timestamp.admin_order_field = 'timestamp'


def delete_without_connection(modeladmin, request, queryset: QuerySet[Img]):
    count_all = 0
    count_all_success = 0
    total_cleared = 0
    for item in queryset:
        obj = obj.param.get("obj")
        model = obj.param.get("model")

        if model == "not_linked":
            os.remove(item.image.path)
            item.delete()
            count_all_success += 1

        count_all += 1

    messages.success(
        request, f"Изображение успешно удалены {count_all_success} из {count_all} выбраных, освобождено {total_cleared / (1024 * 1024)} МБ")


delete_without_connection.short_description = "Удалить без связи"


def update_connection(modeladmin, request, queryset: QuerySet[Img]):
    from hotel.models import Hotel, RCategory, Comment
    # На 02.12.2023 14:29, так
    # Связи обновлены, 50000 [100%].
    # НЕ ИЗМЕНЕНО:
    #   Отели: 23726 [47.5%],
    #   Номера: 17275 [34.5%],
    #   Коментарии: 0 [0%],
    #   Без связи: 23726 [47.5%].
    # ИЗМЕНЕНО:
    #   Отели: 181 [0.4%],
    #   Номера: 354 [0.7%],
    #   Коментарии: 4 [0%]

    #PS. Всего фото сейчас 981649 штук, но такой длиный запрос он не выдержал, так что только 50к

    counts = {
        "all": 0,
        "not_linked": 0,
        "hotel.hotel": 0,
        "hotel.rc": 0,
        "hotel.comment": 0,
        "change_not_linked": {
            "hotel.hotel": 0,
            "hotel.rc": 0,
            "hotel.comment": 0
        }
    }

    for item in queryset[:50000]:
        obj = item.param.get("obj")
        model = item.param.get("model")

        if model == "not_linked":
            counts["not_linked"] += 1
        elif model == "hotel.hotel":
            hotel = Hotel.objects.filter(id=obj).first()
            if hotel:
                counts["hotel.hotel"] += 1
            else:
                counts["change_not_linked"]["hotel.hotel"] += 1

        elif model == "hotel.rc":
            rc = RCategory.objects.filter(id=obj).first()
            if rc:
                counts["hotel.rc"] += 1
            else:
                counts["change_not_linked"]["hotel.rc"] += 1

        elif model == "hotel.comment":
            comment = Comment.objects.filter(id=obj).first()
            if comment:
                counts["hotel.comment"] += 1
            else:
                counts["change_not_linked"]["hotel.comment"] += 1

        counts["all"] += 1

    messages.success(request, f"""
Связи обновлены, {counts['all']} [100%].
НЕ ИЗМЕНЕНО:
    Отели: {counts['hotel.hotel']} [{round(counts['hotel.hotel'] / counts['all'] * 100, 3)}%],
    Номера: {counts['hotel.rc']} [{round(counts['hotel.rc'] / counts['all'] * 100, 3)}%],
    Коментарии: {counts['hotel.comment']} [{round(counts['hotel.comment'] / counts['all'] * 100, 3)}%],
    Без связи: {counts['hotel.hotel']} [{round(counts['hotel.hotel'] / counts['all'] * 100, 3)}%].
ИЗМЕНЕНО:
    Отели: {counts['change_not_linked']['hotel.hotel']} [{round(counts['change_not_linked']['hotel.hotel'] / counts['all'] * 100, 3)}%],
    Номера: {counts['change_not_linked']['hotel.rc']} [{round(counts['change_not_linked']['hotel.rc'] / counts['all'] * 100, 3)}%],
    Коментарии: {counts['change_not_linked']['hotel.comment']} [{round(counts['change_not_linked']['hotel.comment'] / counts['all'] * 100, 3)}%]
""")


update_connection.short_description = "Обновить связи"


class ImgAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'created_date', "get_model", "get_obj")
    list_per_page = 1000

    actions = [delete_without_connection, update_connection]

    def get_model(self, obj: Img):
        model = obj.param.get("model")
        if model == "hotel.hotel": return "Отель"
        if model == "hotel.rc": return "Номер"
        if model == "hotel.comment": return "Отзыв"
        return "Без связи"

    get_model.short_description = 'Модель'
    get_model.admin_order_field = 'param__model'

    def get_obj(self, obj: Img):
        from hotel.models import Hotel, RCategory, Comment
        obj_id = obj.param.get("obj")
        model = obj.param.get("model")
        if model == "hotel.hotel":
            url = reverse('admin:hotel_hotel_change', args=[obj_id])
            text = Hotel.objects.get(id=obj_id)
            return format_html('<a href="{}">{}</a>', url, text)

        if model == "hotel.rc":
            url = reverse('admin:hotel_rcategory_change', args=[obj_id])
            text = RCategory.objects.get(id=obj_id)
            return format_html('<a href="{}">{}</a>', url, text)

        if model == "hotel.comment":
            url = reverse('admin:hotel_comment_change', args=[obj_id])
            text = Comment.objects.get(id=obj_id)
            return format_html('<a href="{}">{}</a>', url, text)

        if model == "not_linked":
            return "Нет ссылки"

    get_obj.short_description = 'Объёкт'
    get_obj.admin_order_field = 'param__obj'


admin.site.register(Img, ImgAdmin)


class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ("short_code", "short_url", "original_url", "created_at", "option",)
    exclude = ['short_code']

    def short_url(self, obj):
        return obj.get_absolute_url()

    short_url.short_description = 'Короткая ссылка'

admin.site.register(ShortLink, ShortLinkAdmin)



class ConstantAdmin(admin.ModelAdmin):
    list_display = ("code", "value")

    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.TextField: {'widget': JSONEditorWidget},
    }

admin.site.register(Constant, ConstantAdmin)


class DocumentationPageAdmin(MPTTModelAdmin):
    list_display = ('title', 'slug')
    exclude = ('related_pages', 'slug')  # Удаление поля related_pages из админки
    verbose_name = 'Страница документации'  # Наименование модели на русском
    verbose_name_plural = 'Страницы документации'  # Множественное наименование модели на русском
    fieldsets = (
        ('Содержимое', {
            'fields': ('title', 'content'),
        }),
        ('Настройки', {
            'fields': ('parent', 'order'),
        }),
    )

admin.site.register(DocumentationPage, DocumentationPageAdmin)