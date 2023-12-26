from django import template
from django.template.loader import render_to_string


register = template.Library()

@register.simple_tag
def get_card(type, data):
    if type == 'profile_booking':
        context = {'data': data}
        return render_to_string('template/card_profile_booking_hotel.html', context)