from django.urls import path
from .views import ajax

urlpatterns = [
    path('ajax_toggle_favorite_hotel/', ajax.toggle_favorite_hotel, name='ajax_toggle_favorite_hotel'),
    path('ajax_get_favorite_hotel/', ajax.get_favorite_hotel, name='ajax_ajax_get_favorite_hotel'),


    # Отелю
    path('register_hotel/',  ajax.ajax_register_hotel, name='form_register_hotel'),

    path('register/placement_object/',  ajax.ajax_register_placement_object, name='ajax_register_placement_object'),


    path('save_hotel/',  ajax.ajax_save_hotel, name='form_save_hotel'),

    path('switch_hotel/',  ajax.ajax_switch_hotel, name='ajax_switch_hotel'),


    #Бусты
    path('add_common_boost/', ajax.ajax_add_common_boost, name='ajax_add_common_boost'),
    path('add_super_boost/', ajax.ajax_add_super_boost, name='ajax_add_super_boost'),

    #Управления номерами
    path('hotel/rc/',  ajax.ajax_get_hotel_rc, name='get_hotel_rc'), #Получения обекта
    path('save_rcategory/', ajax.ajax_save_rcategory, name='form_save_rcategory'), #Сохранения
    path('del_rcategory/', ajax.ajax_del_rcategory, name='form_del_rcategory'), #Удаления
    path('form_toggle_eneble_rcategory/', ajax.ajax_toggle_eneble_rcategory, name='form_toggle_eneble_rcategory'),

    path('hotel/room/',  ajax.ajax_get_hotel_room, name='get_hotel_room'),  #Получения обекта
    path('save_room/', ajax.ajax_save_room, name='form_save_room'), #Сохранения
    path('del_room/', ajax.ajax_del_room, name='form_del_room'), #Удаления
    path('toggle_eneble_room/', ajax.ajax_toggle_eneble_room, name='form_toggle_eneble_room'),


    #Отель - Бронирования
    path('booking_edit_status/', ajax.ajax_booking_edit_status, name='ajax_booking_edit_status'), #Изменения статуса
    path('booking_edit_comment/', ajax.ajax_booking_edit_comment, name='ajax_booking_edit_comment'), #Изменения статуса
    path('booking_edit_payment_for_accommodation/', ajax.ajax_booking_edit_payment_for_accommodation, name='ajax_booking_edit_payment_for_accommodation'), #Изменения заметки оплачено или нет

    #Отель - Шахматка
    path('rcs_rooms_chess/', ajax.ajax_rcs_rooms_chess, name='form_rcs_rooms_chess'),
    path('booking_chess/', ajax.ajax_booking_chess, name='form_booking_chess'),

    path('open_room/', ajax.ajax_open_room, name='form_open_room'),
    path('close_room/', ajax.ajax_close_room, name='form_close_room'),

    #Отель - Календарь цен
    path('get_room_ppd/', ajax.ajax_get_room_ppd, name='form_get_room_ppd'),
    path('get_value_ppd/', ajax.ajax_get_value_ppd, name='form_get_value_ppd'),
    path('edit_price_calendar/', ajax.ajax_edit_price_calendar, name='form_edit_price_calendar'),


    # Формы
    path('reset_password/', ajax.ajax_reset_password, name='form_reset_password'),
    path('save_search/',  ajax.ajax_save_search, name='form_save_search'),
    path('fillter_rc_search/',  ajax.ajax_fillter_rc_search, name='form_fillter_rc_search'),
    path('hotel/detal/rooms',  ajax.ajax_get_hotel_detal_rooms, name='get_hotel_detal_rooms'),

    #notification
    path('get_notifications/', ajax.get_notifications, name='get_notifications'),
    path('open_notification/', ajax.open_notification, name='open_notification'),
    path('del_all_notification/', ajax.del_all_notification, name='del_all_notification'),

    #Для клиента и отеля
    path('cancellation_booking/', ajax.cancellation_booking, name='cancellation_booking'),

    path('phone_verification_create/', ajax.phone_verification_create, name='phone_verification_create'),
    path('phone_verification_check/', ajax.phone_verification_check, name='phone_verification_check'),

    path('add_rubl_lk/', ajax.add_rubl_lk, name='add_rubl_lk'),
    path('return_add_rubl_lk/', ajax.return_add_rubl_lk, name='return_add_rubl_lk'),
]
