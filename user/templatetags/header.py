from django import template
from hotel.models import Hotel
from user.models import Notification

register = template.Library()

@register.inclusion_tag('template/header.html', takes_context=True)
def header(context):
    """Выводит header
    Returns:
        _type_: _description_
    """

    if context.request.user.is_authenticated:
        return {
            "hotel": Hotel.objects.filter(owner=context.request.user).exists(),
            "login": True,
            "admin": context.request.user.user_type in ["admin", "moder", "owner"]
        }
    else:
        return {
            "hotel": False,
            "login": False,
        }

@register.inclusion_tag('template/header_notifications.html', takes_context=True)
def header_notifications(context):
    notif = Notification.objects.filter(user=context.request.user)
    return {"count": len(notif)}


# @register.inclusion_tag('partner/template/header.html', takes_context=True)
# def header(context):
#     if context.request.user.is_authenticated:
#         return {
#             "hotel": Hotel.objects.filter(owner=context.request.user).exists(),
#             "login": True,
#             "admin": context.request.user.user_type in ["admin", "moder", "owner"]
#         }
#     else:
#         return {
#             "hotel": False,
#             "login": False,
#         }