from django.contrib import admin
from .models import *
from django.utils.html import format_html
from html import escape
from django.utils.safestring import mark_safe


class AddressModelInline(admin.StackedInline):
    model = Address
    max_num = 1
    extra = 1
    can_delete = False


class HBoostModelInline(admin.TabularInline):
    model = HBoost


class RModelInline(admin.TabularInline):
    model = Room


class RCModelInline(admin.StackedInline):
    filter_horizontal = ('service',)
    model = RCategory


class BookingModelInline(admin.TabularInline):
    model = Booking


def allow_children(modeladmin, request, queryset):
    queryset.update(allowed_child=True)


allow_children.short_description = "Разрешить детей"


def set_enable_true(modeladmin, request, queryset):
    queryset.update(enable=True)


set_enable_true.short_description = "Включить"


def set_enable_false(modeladmin, request, queryset):
    queryset.update(enable=False)


set_enable_false.short_description = "Выключить"


def set_is_pending_true(modeladmin, request, queryset):
    queryset.update(is_pending=True)


set_is_pending_true.short_description = "Установить как на модерации"


def set_is_pending_false(modeladmin, request, queryset):
    queryset.update(is_pending=False)


set_is_pending_false.short_description = "Установить как не на модерации"


def reset_rating(modeladmin, request, queryset):
    queryset.filter(rating_stat=0, rating_amount=0).update(rating_stat=7)


set_is_pending_false.short_description = "Рейтинг - 0 в 7"


def action_hash_occupied_numbers_update(self, request, queryset):
    for hotel in queryset:
        for rc in hotel.rcategory_hotel.all():
            rc.hash_occupied_numbers_update()

    self.message_user(request, 'Хеш занятых комнат обновлён.')


action_hash_occupied_numbers_update.short_description = 'Обновить хеш занятых комнат'


class HotelAdmin(admin.ModelAdmin):
    search_fields = ("owner__email", "name", "type_hotel")
    filter_horizontal = ('service',)
    inlines = [AddressModelInline, RCModelInline, HBoostModelInline]
    actions = [set_enable_true, set_enable_false,
               set_is_pending_true, set_is_pending_false, action_hash_occupied_numbers_update]
    list_per_page = 10000

    def get_list_display(self, request):
        fields = ("id", "name", "type_hotel", "display_place", "created_at", "check_in_time", "departure_time", "stars", "real_money", "rating_stat",
                  "rating_amount", "reviews_amount", "coordinates", "percentage", "rank_points", "date_when_you_start_receiving_guests", "updated_at")
        related_fields = ("owner", "display_service")
        boolean_fields = ("enable", "is_delete",
                          "is_pending", "instant_booking")
        return related_fields + fields + boolean_fields

    def display_service(self, obj: Hotel):
        return obj.service.all().count()

    def display_place(self, obj: Hotel):
        try:
            return obj.adrress_hotel.city
        except:
            pass

        return ""

    display_service.short_description = 'Услуги'


admin.site.register(Hotel, HotelAdmin)


class GroupBookingAdmin(admin.ModelAdmin):
    list_display = ("id", "list_booking")
    list_per_page = 1000

    def list_booking(self, obj: GroupBooking):
        # получаем список id бронирований
        booking_ids = obj.bookings.all().values_list("id", flat=True)

        # создаем пустую строку для добавления HTML тегов
        html_string = ""

        # проходимся по каждому id и добавляем тег с классом tag
        for booking_id in booking_ids:
            html_string += f"[{escape(str(booking_id))}] "

        return html_string


admin.site.register(GroupBooking, GroupBookingAdmin)


# RService


class RServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_html')

    def icon_html(self, obj: RService):
        if obj.icon:
            return mark_safe('<img src="{}" />'.format(obj.icon.url))
        return '-'

    icon_html.short_description = 'Иконка'
    icon_html.allow_tags = True


admin.site.register(RService, RServiceAdmin)


class HServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'icon_html')

    list_per_page = 999

    def icon_html(self, obj: HService):
        if obj.icon:
            return mark_safe('<img src="{}" />'.format(obj.icon.url))
        return '-'

    icon_html.short_description = 'Иконка'
    icon_html.allow_tags = True

    actions = ['regen_upload_icon']

    def regen_upload_icon(self, request, queryset):
        for service in queryset:
            service.regen_upload_icon()

        self.message_user(request, 'Иконки обновлены для выбранных услуг.')

    regen_upload_icon.short_description = 'Обновить иконки'


admin.site.register(HService, HServiceAdmin)


# RCategory


class RCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "hotel_name", "price_base", "offer_type",
                    "square", "max_adults", "count_room", "count_bedrooms", "service_count",
                    "beds", "description_of_the_room")
    inlines = [RModelInline]

    def service_count(self, obj):
        return obj.service.count()

    def hotel_name(self, obj):
        return obj.hotel.name


admin.site.register(RCategory, RCategoryAdmin)

# Booking


class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", 'str_booked_room', 'str_booking_user', 'str_created_at', 'str_start_date_time', 'str_end_date_time',
                    'str_price', 'str_count', 'str_status', 'str_is_delete')

    def str_booked_room(self, obj: Booking):
        booking_room : Room = obj.booked_room
        if not booking_room: return ""
        category : RCategory = booking_room.category
        hotel : Hotel = category.hotel
        return format_html(f"""
            <div style="margin: -5px 0">
                <a href="/django_admin/hotel/hotel/{hotel.pk}/change/" style="width: 100%; display: block; padding: 5px 5px; border-radius: 5px 5px 0 0; background: #718fff; color: white;">{hotel.name}</a>
                <a href="/django_admin/hotel/rcategory/{hotel.pk}/change/" style="width: 100%; display: block; padding: 5px 5px; background: #72d17e; color: white;">{category.name}</a>
                <a href="/django_admin/hotel/room/{booking_room.id}/change/" style="width: 100%; display: block; padding: 5px 5px; background: #e16161; color: white; border-radius: 0 0 5px 5px">{booking_room.room_number}</a>
            </div>
        """)

    str_booked_room.short_description = 'Номер'

    def str_booking_user(self, obj: Booking):
        booking_user : User = obj.booking_user
        if not booking_user: return ""
        return format_html(f"""
            <a href="/django_admin/user/user/{booking_user.pk}/change/" style="display: block; margin: -5px 0">
                <span style="width: 100%; display: block; padding: 2px 5px; border-radius: 5px 5px 0 0; background: #e16161; color: white;">{booking_user.pk}</span>
                <span style="width: 100%; display: block; padding: 2px 5px; border-radius: 0 0 5px 5px; background: #d18888; color: white;">{booking_user.fio}</span>
            </a>
        """)

    str_booking_user.short_description = 'Пользователь'

    def str_created_at(self, obj: Booking):
        created_at = obj.created_at
        russian_date = created_at.strftime('%d.%m.%Y')
        russian_time = created_at.strftime('%H:%M')

        return format_html(f"""
            <div style="margin: -5px 0">
                <span style="width: 100%; display: block; padding: 2px 5px; border-radius: 5px 5px 0 0; background: #718fff; color: white;">{russian_date}</span>
                <span style="width: 100%; display: block; padding: 2px 5px; border-radius: 0 0 5px 5px; background: #a0b4ff; color: white;">{russian_time}</span>
            </div>
        """)

    str_created_at.short_description = 'Создание'


    def str_start_date_time(self, obj: Booking):
        start_date_time = obj.start_date_time
        russian_date = start_date_time.strftime('%d.%m.%Y')
        russian_time = start_date_time.strftime('%H:%M')

        it_time = start_date_time.replace(tzinfo=datetime.timezone.utc) <= datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        color_1 = "#72d17e" if it_time else "#e16161"
        color_2 = "#92bb97" if it_time else "#d18888"

        return format_html(f"""
            <div style="margin: -5px 0">
                <span style="width: 100%; display: block; padding: 2px 5px; border-radius: 5px 5px 0 0; background: {color_1}; color: white;">{russian_date}</span>
                <span style="width: 100%; display: block; padding: 2px 5px; border-radius: 0 0 5px 5px; background: {color_2}; color: white;">{russian_time}</span>
            </div>
        """)

    str_start_date_time.short_description = 'Начало'

    def str_end_date_time(self, obj: Booking):
        end_date_time = obj.end_date_time
        russian_date = end_date_time.strftime('%d.%m.%Y')
        russian_time = end_date_time.strftime('%H:%M')

        it_time = end_date_time.replace(tzinfo=datetime.timezone.utc) <= datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        color_1 = "#72d17e" if it_time else "#e16161"
        color_2 = "#92bb97" if it_time else "#d18888"

        return format_html(f"""
            <div style="margin: -5px 0">
                <span style="width: 100%; display: block; padding: 2px 5px; border-radius: 5px 5px 0 0; background: {color_1}; color: white;">{russian_date}</span>
                <span style="width: 100%; display: block; padding: 2px 5px; border-radius: 0 0 5px 5px; background: {color_2}; color: white;">{russian_time}</span>
            </div>
        """)


    str_end_date_time.short_description = 'Конец'



    def str_price(self, obj: Booking):
        prices : dict = obj.param.get("prices")
        str_payment_status : str = next((str_status for code_status, str_status in Booking.PAYMENT_CHOICES if code_status == obj.payment_status), None)
        code_payment_status = obj.payment_status

        color_payment_status = {
            "not_paid": "#e16161",
            "site_paid": "#72d17e",
            "full_paid": "#e16161",
            "site_refund": "#575757",
            "full_refund": "#575757",
        }[code_payment_status]

        color_price = {
            "not_paid": "#d18888",
            "site_paid": "#92bb97",
            "full_paid": "#d18888",
            "site_refund": "#878787",
            "full_refund": "#878787",
        }[code_payment_status]

        if not prices: return ""

        price_balanc = round(prices["balanc"]["value"])
        price_bonus = round(prices["bonus"]["value"])
        price_card = round(prices["card"]["value"])

        # Тут будут значения из prices и payment_status
        return format_html(f"""
            <div style="margin: -5px 0">
                <span style="display: block; padding: 2px 5px; background: {color_payment_status}; color: white; border-radius: 5px 5px 0 0;">{str_payment_status}</span>
                <span style="display: block; padding: 0px 5px; background: {color_price}; color: white;"><b style="font-weight: 900;">ЛК:</b> {price_balanc} ₽</span>
                <span style="display: block; padding: 0px 5px; background: {color_price}; color: white;"><b style="font-weight: 900;">Б:</b> {price_bonus}</span>
                <span style="display: block; padding: 0px 5px; background: {color_price}; color: white; border-radius: 0 0 5px 5px;"><b style="font-weight: 900;">К:</b> {price_card} ₽</span>
            </div>
        """)

    str_price.short_description = 'Оплата'


    def str_count(self, obj: Booking):
        adults_count : int = obj.adults_count
        children_count: int = obj.children_count
        if adults_count+children_count == 0: return ""

        return format_html(f"""
            <div style="margin: -5px 0">
                <span style="width: 100%; display: block; padding: 5px 5px; border-radius: 5px 5px 0 0; background: #718fff; color: white;"><b style="font-weight: 900;">Взрослые:</b> {adults_count}</span>
                <span style="width: 100%; display: block; padding: 5px 5px; background: #e16161; color: white; border-radius: 0 0 5px 5px"><b style="font-weight: 900;">Дети:</b> {children_count}</span>
            </div>
        """)

    str_count.short_description = 'Люди'

    def str_status(self, obj : Booking):

        str_status : str = next((str_status for code_status, str_status in Booking.STATUS_CHOICES if code_status == obj.status), None)
        code_status = obj.status

        color_status = {
            'new': '#54d39c',
            'verified': '#60C0FF',
            'settled': '#54d39c',
            'left': '#B3BAC4',
            'cancelled': '#D34141',
            'close': '#D34141',
        }[code_status]

        return format_html(f'<span style="background: {color_status}; padding: 5px; color: white; border-radius: 5px;">{str_status}</span>')

    str_status.short_description = 'Статус'

    def str_is_delete(self, obj):
        if obj.is_delete:
            return format_html(f'<span style="background: #ff5555; padding: 5px; color: white; border-radius: 5px;">Удалено</span>')
        else:
            return format_html(f'')

    str_is_delete.short_description = 'Удалено?'


admin.site.register(Booking, BookingAdmin)

# Comment


class CommentAdmin(admin.ModelAdmin):
    list_display = ('hotel_name', "author_name", "date",
                    "what_is_good_text",
                    "what_is_bad_text",
                    "location",
                    "price_quality_ratio",
                    "purity",
                    "food",
                    "service",
                    "hygiene_products",
                    "wifi_quality",
                    "number_quality",
                    )

    def hotel_name(self, obj):
        return obj.hotel.name

    def author_name(self, obj):
        if obj.user:
            return obj.user.get_FIO()
        else:
            return obj.author_name


admin.site.register(Comment, CommentAdmin)


class HBoostAdmin(admin.ModelAdmin):
    list_display = ('hotel', "super", "date",)


admin.site.register(HBoost, HBoostAdmin)


class BonusAdmin(admin.ModelAdmin):
    list_display = ('hotel_name', "value", "date")

    def hotel_name(self, obj):
        return obj.hotel.name


admin.site.register(Bonus, BonusAdmin)
