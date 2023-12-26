from django import template
import json
import datetime

from hotel.models import Address, Hotel, RCategory

register = template.Library()

@register.inclusion_tag('template/input_text.html')
def input_text(type: str, label: str, name: str, value: any, placeholder: str, required: bool, autocomplete="off", maxlength=None):
    '''
    Создаёт нужный инпут по запросу, с параметрами
    @type - Тип: text, email, tel, date_3, radio
    @label - Названия которые видел пользователь
    @name - Названия input для сервера
    @value - Значения которое подставляется в инпут
    @placeholder - placeholder
    @required - Обезательный: 1 или 0
    @autocomplete - Автопредложения
    '''
    return {
        "type": type,
        "label": label,
        "name": name,
        "value": value,
        "placeholder": placeholder,
        "required": required,
        "autocomplete": autocomplete,
        "maxlength": maxlength,
    }


@register.inclusion_tag('template/input_cr.html')
def input_cr(type: str, label: str, name: str, values_json: str, checkeds_json: str, required: bool = False):
    '''
    Создаёт нужный chackbox или radio
    '''
    if values_json == "type_hotel":
        values = data_list("type_hotel")
        r_value = []
        for item in values:
            r_value.append([[item["code"], item["name"]], False])

        return {
            "type": type,
            "label": label,
            "name": name,
            "values": r_value,
            "required": required,
        }

    if values_json == "yes_no":
        values = data_list("type_hotel")
        r_value = [
            [["True", "Да"], True],
            [["False", "Нет"], False],
        ]

        return {
            "type": "radio",
            "label": label,
            "name": name,
            "values": r_value,
            "required": required,
        }

    if len(values_json) > 0:
        values = json.loads(values_json)
    else:
        values = []

    if len(checkeds_json) > 1:
        checkeds = json.loads(checkeds_json)
    else:
        checkeds = []

    r_values = []


    if type != 'checkbox_grupe':
        for value in values:
            if value[0] in checkeds:
                r_values.append([value, 1])
            else:
                r_values.append([value, 0])
    else:
        values_buff = {}
        for value in values:
            if value[0] not in values_buff:
                values_buff[value[0]] = []

            if value[1] in checkeds:
                values_buff[value[0]].append([value[1], value[2], True])
            else:
                values_buff[value[0]].append([value[1], value[2], False])

        for item in values_buff:
            r_values.append([item, values_buff[item]])

    return {
        "type": type,
        "label": label,
        "name": name,
        "values": r_values,
        "required": required,
    }


@register.inclusion_tag('template/table.html')
def table(label: str, data_json: str):
    data = json.loads(data_json)

    print(data)

    return {
        "label": label,
        "th": data["th"],
        "items": data["items"],
        "click": data["click"],
    }


@register.inclusion_tag('template/input_text.html')
def input_list(label: str, data_json: str):
    data = json.loads(data_json)

    print(data)

    return {
        "label": label,
        "items": data["items"],
        "type": "list",
    }


@register.inclusion_tag('template/input_file.html')
def input_file(type: str, label: str, name: str, imgs: list, min: int, max: int = None, sort = False, arrange_first = False, help = None):
    if max == None:
        max = min

    return {
        "label": label,
        "name": name,
        "type": type,
        "imgs": imgs,
        "range": [min, max],
        "sort": sort,
        "arrange_first": arrange_first,
        "help": help,
    }


@register.simple_tag()
def data_list(type):
    if type == "beds":
        list = []
        for item in RCategory.beds_choices:
            list.append({"code": item[0], "name": item[1]})
        return list

    if type == "foods":
        return [
            {"code": "breakfast", "name": "Завтрак"},
            {"code": "lunch", "name": "Обед"},
            {"code": "dinner", "name": "Ужин"},
        ]

    if type == "cancels":
        return [
            {"code": "yes", "name": "С отменой"},
            {"code": "no", "name": "Без отмены"},
        ]

    if type == "type_hotel":
        list = []
        for item in Hotel.type_hotel_choices:
            list.append({"code": item[0], "name": item[1]})
        return list

    if type == "city":
        list = []
        for item in Address.objects.all().values_list("city", flat=True):
            if item not in list:
                list.append(item)
        return list
