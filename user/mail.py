import requests
from django.template.loader import render_to_string

url = 'https://api.smtp.bz/v1/smtp/send'

headers = {
    "Authorization": "gse7G3KRmGL6aVfjzi3zZNxoardJIaSOsWKZ"
}


def send(type, title, to_user_email, param) -> dict[str, any]:
    data = {
        'from': 'info@turgorodok.ru',
        'name': 'Тургородок',
        'subject': title,
        'to': to_user_email,
    }

    if type == "new_user":
        data["html"] = render_to_string("mail/new_user.html", {
            "login": param["login"],
            "password": param["password"],
        })

    elif type == "confirmation_email_address":
        data["html"] = render_to_string("mail/confirmation_email_address.html", param)


    elif type == "reset_password":
        data["html"] = render_to_string("mail/password_reset.html", param)


    elif type == "new_password":
        data["html"] = render_to_string("mail/new_password.html", param)

    elif type == "raw":
        data["html"] = param if param != "" else " "

    json_result = {}

    if data.get("html"):
        response = requests.post(url, headers=headers, json=data)
        json_result["status"] = response.status_code

        if json_result["status"] != 200:
            return json_result

        json_result["param"] = response.json()
    else:
        json_result = {
            "not_html": True,
            "type": type,
            "param": param,
        }

    return json_result
