from django.urls import path
import hotel.views.register as register
import hotel.views.search as search
import hotel.views.detailed as detailed
import hotel.views.booking as booking



urlpatterns = [
    # path('hotel/register/', register.hotel_register, name='hotel_register'),
    path('register/placement_object/', register.page_register_placement_object, name='page_register_placement_object'),

    path('hotel/search/fillter/', search.get_hotel_fillter, name='get_hotel_fillter'),
    path('hotel/search/<path:slug>/', search.hotel_search, name='hotel_search'),

    path('hotel/<int:id>/', detailed.hotel_detal, name='hotel_detailed'),
    path('hotel/get_rooms/', detailed.ajax_get_rooms, name='hotel_detailed_get_rooms'),

    path('hotel/reviews/',  detailed.get_reviews, name="hotel_reviews"),
    path('hotel/create_review/',  detailed.create_review, name="hotel_create_review"),


    path('hotel/room/to_book/', booking.hotel_room_to_book, name="hotel_room_to_book"),
    path('hotel/room/booking/add/',  booking.hotel_room_booking_add, name="hotel_room_booking_add"),
    path('hotel/room/booking/successful_payment/',  booking.hotel_room_booking_successful_payment, name="hotel_room_booking_successful_payment"),
    path('hotel/room/booking/failed_payment/',  booking.hotel_room_booking_failed_payment, name="hotel_room_booking_failed_payment"),
]