from django.contrib.auth import views as auth
from django.urls import path
from django.views.generic import RedirectView
from .views import admin, admin_staff as staff, admin_moderwork as moderwork, admin_debug as debug

urlpatterns = [

    #Управления сайтом
    path('site_management/', admin.page_site_management, name='admin.page.site_management'),
    path('site_management/settings_options/get/', admin.ajax_site_management_settings_options_get, name='admin.ajax.site_management.settings_options.get'),
    path('site_management/settings_options/save/', admin.ajax_site_management_settings_options_save, name='admin.ajax.site_management.settings_options.save'),

    #Парсер
    path('parser/hotel/', admin.page_parser_hotel, name='admin.page.parser.hotel'),
    path('parser/api/hotel/add/', admin.api_parser_hotel_add, name='admin.api.parser.hotel.add'),
    path('parser/api/hotel/get/', admin.api_parser_hotel_get, name='admin.api.parser.hotel.get'),
    path('parser/api/hotel/materialize_a_hotel/', admin.api_parser_hotel_materialize_a_hotel, name='admin.api.parser.hotel.materialize_a_hotel'),

    #Управления персоналом
    path('staff/', staff.index, name='admin.staff'),
    path('staff/api/get/list/', staff.api_get_list, name='admin.staff.api.get.list'),
    path('staff/api/get/user/', staff.api_get_user, name='admin.staff.api.get.user'),
    path('staff/api/edit/profile/', staff.api_edit_user, name='admin.staff.api.edit.profile'),


    path('moderwork/', moderwork.index, name='admin.moderwork'),
    path('moderwork/api/get/list/', moderwork.api_get_list, name='admin.moderwork.api.get.list'),
    path('moderwork/api/move/item/', moderwork.api_move_item, name='admin.moderwork.api.move.item'),


    path('debug/test_1/', debug.test_1, name='admin.debug.test_1'),



    #Редирект с /admin/ на другую страницу
    path('', RedirectView.as_view(url='/admin/page/list/user/')),

    #page
    path('page/ts/chat/', admin.page_ts_chat, name='admin.page.ts.chat'),
    path('page/list/moderation/hotel/', admin.page_list_moderation_hotel, name='admin.page.list.moderation.hotel'),
    path('ajax/list/moderation/hotel/', admin.ajax_list_moderation_hotel, name='admin.ajax.list.moderation.hotel'),
    path('ajax/moderation/hotel/disallow/', admin.ajax_moderation_hotel_disallow, name='admin.ajax.moderation.hotel.disallow'),
    path('ajax/moderation/hotel/allow/', admin.ajax_moderation_hotel_allow, name='admin.ajax.moderation.hotel.allow'),
    path('ajax/moderation/hotel/document_allow/', admin.ajax_moderation_hotel_document_allow, name='admin.ajax.moderation.hotel.document_allow'),

    #Таблица пользователей
    path('page/list/user/', admin.page_list_users, name='admin.page.list.user'),
    path('ajax/list/user/', admin.ajax_list_user, name='admin.ajax.list.user'),

    path('page/list/admin/', admin.page_list_admin, name='admin.page.list.admin'),
    path('ajax/list/admin/', admin.ajax_list_admin, name='admin.ajax.list.admin'),


    #Реальная работа модераторов
    path('page/list/real_work_moderators/', admin.page_list_real_work_moderators, name='admin.page.list.real_work_moderators'),
    path('ajax/list/real_work_moderators/', admin.ajax_list_real_work_moderators, name='admin.ajax.list.real_work_moderators'),


    path('page/list/booking/', admin.page_list_bookings, name='admin.page.list.booking'),
    path('ajax/booking/cancellation/', admin.ajax_booking_cancellation, name='admin.ajax.booking.cancellation'),


    path('page/statistics/', admin.page_statistics, name='admin.page.statistics'),
    path('page/user/financial_transactions/', admin.page_user_financial_transactions, name='admin.page.user.financial_transactions'),
    path('page/user/new/', admin.page_user_new, name='admin.page.user.new'),
    path('page/hotel/new/', admin.page_hotel_add, name='admin.page.hotel.new'),
    path('page/hotel/new/multi/', admin.page_hotel_add_multi, name='admin.page.hotel.new.multi'),
    # path('page/list/ownerless_hotel/', admin.page_list_ownerless_hotel, name='admin.page.list.ownerless_hotel'),
    path('page/moving/hotel/', admin.page_moving_hotel, name='admin.page.list.moving_hotel'),
    path('ajax/moving/hotel/run/', admin.ajax_moving_hotel_run, name='ajax.list.moving_hotel.run'),


    path('page/moderator_office/', admin.page_moderator_office, name='ajax.page.page_moderator_office'),
    path('ajax/moderator_office/get/', admin.ajax_moderator_office_get, name='ajax.ajax.page_moderator_office.get'),
    path('ajax/moderator_office/save/', admin.ajax_moderator_office_save, name='ajax.ajax.page_moderator_office.save'),
    path('ajax/add_an_entry_moder_work/', admin.ajax_add_an_entry_moder_work, name='ajax.ajax.add_an_entry_moder_work'),



    path('page/list/place/', admin.page_list_place, name='admin.page.list.place'),
    path('ajax/list/place/add/', admin.ajax_list_place_add, name='admin.ajax.list.place.add'),
    path('page/list/services/', admin.page_list_services, name='admin.page.list.services'),


    path('page/list/hotel/', admin.page_list_hotel, name='admin.page.list.hotel'),
    path('ajax/hotel/list/', admin.ajax_list_hotel, name='admin.ajax.hotel.list'),
    path('ajax/hotel/add_to_report/', admin.ajax_hotel_add_to_report, name='admin.ajax.hotel.add_to_report'),
    path('ajax/hotel/set_enable/', admin.ajax_hotel_set_enable, name='admin.ajax.hotel.set_enable'),

    path('page/list/moderator_reports/', admin.page_list_moderator_reports, name='admin.page.list.moderator_reports'),
    path('ajax/list/moderator_reports/', admin.ajax_list_moderator_reports, name='admin.ajax.list.moderator_reports'),

    #supermoderator
    path('page/list/moderator/', admin.page_list_moderator, name='admin.page.list.moderator'),
    path('ajax/list/moderator/', admin.ajax_list_moderator, name='admin.ajax.list.moderator'),

    #Логи действий админов (Показывать только владельцу)
    path('page/list/actions_admin/', admin.page_list_actions_admin, name='admin.page.list.actions_admin'),
    path('ajax/list/actions_admin/', admin.ajax_list_actions_admin, name='admin.ajax.list.actions_admin'),




    path('ajax/auth/user/', admin.ajax_auth_user, name='admin.ajax.auth_user'),
    path('ajax/user/new/', admin.ajax_user_new, name='admin.ajax.user.new'),

    path('ajax/hotel/add/', admin.ajax_hotel_add, name='admin.ajax.hotel.add'),

    path('ajax/bookings/list/', admin.ajax_list_bookings, name='admin.ajax.bookings.list'),


    # path('ajax/get_access_token/', admin.ajax_get_access_token, name='admin.ajax_get_access_token'),

    path('ajax/bonus/add/', admin.ajax_bonus_add, name='admin.ajax.bonus.add'),
    path('ajax/bonus/deny/', admin.ajax_bonus_deny, name='admin.ajax.bonus.deny'),

    path('ajax/booking/mark_as_answered/', admin.ajax_booking_mark_as_answered, name='admin.ajax.booking.mark_as_answered'),

    # redirect
    path('redirect/open_user_chat/', admin.redirect_open_user_chat, name='admin.redirect.open_user_chat'),


    # Не используется
    path('client_hotel/chat/', admin.page_client_hotel_chat, name='admin.page_client_hotel_chat'),



    # Коментарии
    path('page/review_moderation/', admin.page_review_moderation, name='admin.page_review_moderation'),
    path('ajax/get_reviews/', admin.ajax_get_reviews, name='admin.ajax_get_reviews'),
    path('ajax/update_reviews/', admin.ajax_update_reviews, name='admin.ajax_update_reviews'),

    # Для рарабочика
    path('set_debug_mode/', admin.set_debug_mode),
    path('ajax_user_statistics/', admin.ajax_user_statistics),
]
