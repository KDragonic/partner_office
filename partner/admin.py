from django.utils.html import format_html
from django.contrib import admin
from .models import *
from hotel.models import Hotel
from django_json_widget.widgets import JSONEditorWidget

# Register your models here.


class PartnerAdmin(admin.ModelAdmin):
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {'widget': JSONEditorWidget},
    }


admin.site.register(Partner, PartnerAdmin)


class PromoCodeAdmin(admin.ModelAdmin):
    list_per_page = 10000
    list_display = ("code", "str_partner", "str_channel", "name",
                    "str_hotel_type", "str_cashback", "str_enable", "str_is_delete")

    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def str_partner(self, obj: PromoCode):
        owner = obj.partner.owner
        url = f"/django_admin/user/user/{owner.id}/change/"
        return format_html(f'<a href="{url}">{owner}</a>')

    str_partner.short_description = 'Партнер'

    def str_channel(self, obj: PromoCode):
        channel = obj.channel
        channel_url = channel.url

        colors = {
            "vk": {"bg": "#45668e", "color": "#ffffff"},
            "google": {"bg": "#4285F4", "color": "#ffffff"},
            "yandex": {"bg": "#e32636", "color": "#ffffff"},
            "facebook": {"bg": "#3b5998", "color": "#ffffff"},
            "instagram": {"bg": "#e4405f", "color": "#ffffff"},
            "youtube": {"bg": "#ff0000", "color": "#ffffff"},
            "snapchat": {"bg": "#fffc00", "color": "#000000"}
        }

        channel_param = next(
            (colors[key] for key in colors if key in channel_url), None)

        if channel:
            url = f"/django_admin/partner/channel/{channel.id}/change/"
            return format_html(f'<a href="{url}" style="width: 100%; display: block; text-align: center; margin: -5px; padding: 5px; border-radius: 5px; background: {channel_param["bg"]}; color: {channel_param["color"]}">{channel.name}</a>')
        else:
            return ""

    str_channel.short_description = 'Канал'

    def str_hotel_type(self, obj: PromoCode):
        hotel_type = obj.hotel_type
        str_hotel_type = ""
        if hotel_type == "all":
            str_hotel_type = "Все"
        else:
            str_hotel_type = [
                label for code, label in Hotel.type_hotel_choices if code == hotel_type][0]

        colors = {
            'apart-hotel': {
                "background": "#ffffff",
                "text": "#000000"
            },
            'apartments': {
                "background": "#f0f0f0",
                "text": "#000000"
            },
            'flat': {
                "background": "#ffffcc",
                "text": "#000000"
            },
            'recreation center': {
                "background": "#ccffff",
                "text": "#000000"
            },
            'hotel_1': {
                "background": "#ccffcc",
                "text": "#000000"
            },
            'bungalow': {
                "background": "#ffccff",
                "text": "#000000"
            },
            'boutique hotel': {
                "background": "#ffcc99",
                "text": "#000000"
            },
            'villa': {
                "background": "#cc9966",
                "text": "#000000"
            },
            'glamping': {
                "background": "#cc99ff",
                "text": "#000000"
            },
            'guest house': {
                "background": "#cccccc",
                "text": "#000000"
            },
            'residential premises': {
                "background": "#99ffff",
                "text": "#000000"
            },
            'castle': {
                "background": "#99ff99",
                "text": "#000000"
            },
            'camping': {
                "background": "#ff99ff",
                "text": "#000000"
            },
            'resort hotel': {
                "background": "#ffff99",
                "text": "#000000"
            },
            'furnished rooms': {
                "background": "#ffcc66",
                "text": "#000000"
            },
            'mini-hotel': {
                "background": "#cc9966",
                "text": "#000000"
            },
            'bed and breakfast (b&b)': {
                "background": "#9966cc",
                "text": "#000000"
            },
            'hotel': {
                "background": "#999999",
                "text": "#000000"
            },
            'sanatorium': {
                "background": "#66cccc",
                "text": "#000000"
            },
            'farm': {
                "background": "#66cc66",
                "text": "#000000"
            },
            'hostel': {
                "background": "#cc66cc",
                "text": "#000000"
            },
            'private house': {
                "background": "#cccc66",
                "text": "#000000"
            },
            'chalet': {
                "background": "#cc6633",
                "text": "#000000"
            }
        }

        color = next(
            (colors[key] for key in colors if key in hotel_type), None)

        if not color:
          color = colors["apart-hotel"]

        return format_html(f'<span style="width: 100%; display: block; text-align: center; margin: -5px; padding: 5px; border-radius: 5px; background: {color["background"]}; color: {color["text"]}">{str_hotel_type}</ы>')

    str_hotel_type.short_description = 'Тип объекта размещения'

    def str_cashback(self, obj: PromoCode):
        str_cashback = "{:.0%}".format(obj.cashback / 100).rstrip("0").rstrip(".")

        html = f"""
        <div id="progress-bar" style="position: relative; width: 90px; background: #bb7843; color: white; height: 22px; display: flex; align-items: center; justify-content: center; margin: -3px;">
          <div id="progress" style="width: {obj.cashback}%;background: #ff9743;height: 100%;margin-right: auto;"></div>
          <span style="position: absolute;">{str_cashback}</span>
        </div>
        """

        return format_html(html)

    str_cashback.short_description = 'Кешбек'

    def str_enable(self, obj: PromoCode):
        if obj.enable:
            return format_html(f'<span style="background: #6fc86f; padding: 5px; color: white; border-radius: 5px;">Включен</span>')
        else:
            return format_html(f'<span style="background: #ff5555; padding: 5px; color: white; border-radius: 5px;">Выключено</span>')

    str_enable.short_description = 'Включено?'

    def str_is_delete(self, obj: PromoCode):
        if obj.is_delete:
            return format_html(f'<span style="background: #ff5555; padding: 5px; color: white; border-radius: 5px;">Удалено</span>')
        else:
            return format_html(f'')

    str_is_delete.short_description = 'Удалено?'


admin.site.register(PromoCode, PromoCodeAdmin)
