from audioop import reverse
from django import template
from django.conf import settings
from django.http import HttpRequest
from user.google_auth import create_authorization_url
from hotel.models import Hotel
from user.models import User

register = template.Library()

@register.inclusion_tag('template/reglog_popup.html', takes_context=True)
def reglog_popup(context):

    request : HttpRequest = context.request

    content = {}

    client_id = settings.VK_APP_ID

    redirect_uri_vk = "/vk/register/"
    content["vk_auth_url"] = f"https://oauth.vk.com/authorize?client_id={client_id}&display=page&scope=email&redirect_uri={redirect_uri_vk}&response_type=token&v=5.131&revoke=1"
    content["google_auth_url"] = create_authorization_url(state="register")


    return content