from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import AdminLog

ignore_logs = [
    "get_notifications",
    "jsi18n",
    "main_home",
    "profile",
    "profile_balance",
    "profile_favourites",
    "profile_booking",
    "profile_booking_full",
    "profile_hotel",
    "profile_hotel_balance",
    "profile_hotel_boost",
    "profile_hotel_rcs",
    "profile_hotel_rooms",
    "profile_hotel_booking",
    "profile_hotel_booking_full",
    "profile_hotel_booking_сhess",
    "profile_hotel_price_calendar",
    "profile_hotel_chat",
    "profile_chat",
    "page_back_url_login_page",
    None,
]

class AdminLogMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated and request.user.user_type in ["moder", "admin"]:
            url : str = request.build_absolute_uri()
            url = url.replace("https://turgorodok.ru", "")
            url_name = resolve(request.path_info).url_name
            if url_name not in ignore_logs:
                if request.method == 'GET':
                    params : dict = request.GET.dict()

                    action = f"[{request.method}] {url} {params}"
                    AdminLog.objects.create(user=request.user, action=action)

                elif request.method == 'POST':
                    params = request.POST.dict()

                    if len(params.keys()) > 0:
                        action = f"[{request.method}] {url} {params}"
                        AdminLog.objects.create(user=request.user, action=action)
                else:
                    params = {}
                    action = f"[{request.method}] {url} {params}"
                    AdminLog.objects.create(user=request.user, action=action)
        return None
