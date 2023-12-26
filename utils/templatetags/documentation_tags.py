from django import template
from utils.models import DocumentationPage


register = template.Library()

@register.inclusion_tag('documentation/template/header.html', takes_context=True)
def header(context):
    content = {}
    content["breadcrumbs"] = context.get('breadcrumbs', [])
    content["title"]  = context.get('title', "Без названия")

    return content


@register.inclusion_tag('documentation/template/menu.html', takes_context=True)
def menu(context):

    current_path = context['request'].path.rstrip('/')

    content = {
        "pages": DocumentationPage.get_flat_documentation_pages(),
        'current_path': current_path,
    }

    return content


@register.inclusion_tag('documentation/template/footer.html', takes_context=True)
def footer(context):
    return {}