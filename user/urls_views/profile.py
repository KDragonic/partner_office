from django.contrib.auth import views as auth
from django.urls import path
# from .. import views_client as client, views_hotel as hotel
from .views import client, hotel, client_v2

urlpatterns = [
    # Клиенту
    # path('', client.page_profile, name='profile'),
    # path('balance/', client.page_balance, name='profile_balance'),
    # path('favourites/', client.page_favourites, name='profile_favourites'),
    # path('booking/', client.page_booking,  name='profile_booking'),
    # path('booking/full/<str:id>/', client.page_booking_full, name='profile_booking_full'),

    path('notifications/', client.page_notifications, name='profile_notifications'),


    # Отелю
    # path('hotel/', hotel.page_hotel, name='profile_hotel'),
    # path('hotel/balance/', hotel.page_hotel_balance, name='profile_hotel_balance'),

    #Бусты
    # path('hotel/boost/', hotel.page_hotel_boost, name='profile_hotel_boost'),


    #Управления номерами
    # path('hotel/rcs/', hotel.page_hotel_rcs, name='profile_hotel_rcs'), #Страница

    # path('hotel/rooms/', hotel.page_hotel_rooms, name='profile_hotel_rooms'), #Страница


    #Отель - Бронирования
    # path('hotel/booking/', hotel.page_hotel_booking, name='profile_hotel_booking'), #Список бронирований
    # path('hotel/booking/full/<str:id>/', hotel.page_hotel_booking_full, name='profile_hotel_booking_full'), #Полная информацию о брони

    #Отель - Шахматка
    # path('hotel/booking/chess/', hotel.page_hotel_booking_сhess, name='profile_hotel_booking_сhess'),

    #Отель - Календарь цен
    # path('hotel/price_calendar/', hotel.page_hotel_price_calendar_new, name='profile_hotel_price_calendar'),

    #Чаты
    # path('hotel/chat/', hotel.page_hotel_chat,  name='profile_hotel_chat'),
    # path('chat/', hotel.page_chat,  name='profile_chat'),

    #Отзывы (Отель)
    # path('hotel/reviews/', hotel.page_hotel_reviews,  name='profile_hotel_reviews'),
    path('hotel/ajax/get_reviews/', hotel.ajax_hotel_get_reviews,  name='profile_hotel_get_reviews'),
    path('hotel/ajax/update_reviews/', hotel.ajax_hotel_update_reviews,  name='profile_hotel_update_reviews'),
    path('hotel/ajax/sending_documents/', hotel.ajax_hotel_sending_documents,  name='profile_hotel_sending_documents'),
    path('hotel/ajax_documents_get/', hotel.ajax_hotel_documents_get,  name='profile_hotel_documents_get'),

    path('page_back_url_login_page/', hotel.page_back_url_login_page,  name='page_back_url_login_page'),


    #v2
    path('', client_v2.page_home,  name='profile_v2'),

    path('edit/', client_v2.page_profile_edit,  name='profile_v2_edit'),
    path('edit/ajax_fio', client_v2.ajax_profile_edit_fio,  name='ajax_profile_v2_edit_fio'),
    path('edit/ajax_email', client_v2.ajax_profile_edit_email,  name='ajax_profile_v2_edit_email'),
    path('edit/ajax_phone', client_v2.ajax_profile_edit_phone,  name='ajax_profile_v2_edit_phone'),
    path('edit/ajax_password', client_v2.ajax_profile_edit_password,  name='ajax_profile_v2_edit_password'),


    path('bookings/', client_v2.page_bookings,  name='profile_v2_bookings'),
    path('booking/', client_v2.page_booking,  name='profile_v2_booking'),
    path('chats/', client_v2.page_chats,  name='profile_v2_chats'),
    path('billing/', client_v2.page_billing,  name='profile_v2_billing'),

    path('hotel/price_calendar/', client_v2.page_hotel_price_calendar, name='profile_v2_hotel_price_calendar'),
    path('hotel/price_calendar/weekend_prices/save/', client_v2.ajax_hotel_price_calendar_weekend_prices_save, name='ajax_profile_v2_hotel_price_calendar_weekend_prices_save'),
    path('hotel/price_calendar/weekend_prices/get/', client_v2.ajax_hotel_price_calendar_weekend_prices_get, name='ajax_profile_v2_hotel_price_calendar_weekend_prices_get'),
    path('hotel/booking_chess/', client_v2.page_hotel_booking_chess, name='profile_v2_hotel_booking_chess'),
    path('hotel/upgrade/', client_v2.page_hotel_upgrade,  name='profile_v2_hotel_upgrade'),

    path('hotel/bookings/', client_v2.page_hotel_bookings,  name='profile_v2_hotel_bookings'),
    path('hotel/booking/', client_v2.page_hotel_booking,  name='profile_v2_hotel_booking'),

    path('hotel/edit/', client_v2.page_hotel_edit,  name='profile_v2_hotel_edit'), # Страница изменения отеля
    path('hotel/edit/get/', client_v2.ajax_profile_hotel_edit_get,  name='ajax_profile_v2_hotel_edit_get'), # Получить все данные отеля
    path('hotel/edit/save/', client_v2.ajax_profile_hotel_edit_save,  name='ajax_profile_v2_hotel_edit_save'), # Сохранить отель


    path('hotel/rooms/', client_v2.page_hotel_rooms,  name='profile_v2_hotel_rooms'),
    path('hotel/rooms/get/', client_v2.ajax_profile_hotel_rooms_edit_get,  name='ajax_profile_v2_hotel_rooms_edit_get'), # Получить все данные отеля
    path('hotel/rooms/save/', client_v2.ajax_profile_hotel_rooms_edit_save,  name='ajax_profile_v2_hotel_rooms_edit_save'), # Сохранить отель
    path('hotel/rooms/remove/', client_v2.ajax_profile_hotel_rooms_edit_remove,  name='ajax_profile_v2_hotel_rooms_edit_remove'), # Сохранить отель
    path('hotel/reviews/', client_v2.page_hotel_reviews,  name='profile_v2_hotel_reviews'),


    path('reviews/', client_v2.page_reviews,  name='profile_v2_reviews'),
    path('reviews/ajax/get/', client_v2.ajax_get_review,  name='ajax_profile_v2_get_review'),

    path('ts/', client_v2.page_ts, name='profile_v2_ts'),


    path('new_login/', client_v2.page_new_login, name='profile_v2_new_login'),


]
