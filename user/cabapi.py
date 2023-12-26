import requests

PUBLIC_KEY = "cd44a82b0d9bb71799468e78a0576c67"
CAMPAIGN_ID = "1161238072"


def flashcall(phone: str):
    """Создать звонок на телефон

    Args:
        phone (str): Номер куда нужно позвонить

    Returns:
        dirt: Список с свойствами которые вернул запрос
    """
    url = "https://zvonok.com/manager/cabapi_external/api/v1/phones/flashcall/"

    payload = {
        'public_key': PUBLIC_KEY,
        'phone': phone,
        'campaign_id': CAMPAIGN_ID,
    }

    files = [

    ]

    headers = {}

    response = requests.request(
        "POST", url, headers=headers, data=payload, files=files)

    return response.json()
