from django import template
from user.models import User

register = template.Library()

@register.inclusion_tag('partner/template/header.html', takes_context=True)
def header(context):
    content = {}
    content["breadcrumbs"] = context.get('breadcrumbs', [])
    content["title"]  = context.get('title', "Без названия")
    user : User = context.request.user
    if user.is_authenticated:
        content["user"] = {
            "id": user.id,
            "fio": user.get_FIO(),
            "email": user.email,
            "phone": user.phone,
        }

    return content


@register.inclusion_tag('partner/template/menu.html', takes_context=True)
def menu(context):
    return {}


@register.inclusion_tag('partner/template/footer.html', takes_context=True)
def footer(context):
    return {}