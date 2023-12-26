import datetime
import json
import os
import random
import re
import sys
import time
from urllib.parse import parse_qs, urlparse
import uuid
from django.core.management.base import BaseCommand
import requests
from user.urls_views.views.admin import fun_add_hotel
from utils.models import Constant
import datetime
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from selenium import webdriver
from seleniumwire import webdriver as webdriver_ajax # Import from seleniumwire
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from seleniumwire.utils import decode

import time
from xvfbwrapper import Xvfb
from colorama import *


def update_query_params(url, new_values):
    parsed_url = urlparse(url)
    query_dict = parse_qs(parsed_url.query)

    new_values["q"] = random.randint(1000, 9999)
    new_values["sid"] = str(uuid.uuid4())

    for key, value in new_values.items():
        query_dict[key] = value

    new_query = urlencode(query_dict, doseq=True)
    updated_url = urlunparse((parsed_url.scheme, parsed_url.netloc,
                              parsed_url.path, parsed_url.params, new_query, parsed_url.fragment))

    return updated_url


def get_hotel(hotel_id):
    start_time = int(time.time())

    url = "https://ostrovok.ru/hotel/search/v2/site/hp/content"
    params = {
        "lang": "ru",
        "hotel": hotel_id,
    }

    response = requests.get(url, params=params)


    if response.status_code != 200:
        return {"error": "not 200", "status_code": response.status_code}

    json_data = response.json()

    amenities = {}

    for group in json_data["data"]["hotel"]["amenity_groups_v2"]:
        category = group["group_name"]
        amenities[category] = []
        for amenity in group["amenities"]:
            name = amenity["name"]
            amenities[category].append(name)

    address_parts = json_data["data"]["hotel"]["address"].split(', ')
    street = address_parts[0]
    house_number = address_parts[1]
    city = json_data["data"]["hotel"]["city"]
    country = json_data["data"]["hotel"]["country"]

    description = json_data["data"]["hotel"]["description"]

    images = []

    for img in json_data["data"]["hotel"]["images"]:
        w = img["width"]
        h = img["height"]

        url: str = img["tmpl"]

        url = url.replace("{size}", "1024x768")

        images.append({
            "url": url,
        })

    latitude = json_data["data"]["hotel"]["latitude"]
    longitude = json_data["data"]["hotel"]["longitude"]

    name = json_data["data"]["hotel"]["name"]

    rooms_data_parser_selenium, additional_data, return_urls = parser_hotel_rooms(
        hotel_id)

    rooms = []

    room_groups = json_data["data"]["hotel"]["room_groups"]

    for room in room_groups:
        if not rooms_data_parser_selenium.get(room["name"]):
            continue

        date_room = {
            "name": room["name"],
            "size": room.get("size"),
            "amenitie": [item for item in rooms_data_parser_selenium[room["name"]]["amenity"]],
            "search": rooms_data_parser_selenium[room["name"]]["search"],
            "visibility_area": {
                "date": [],
            },
            "rg_hash": room["rg_hash"],
        }

        days_list = [search["date"]["days"]
                     for search in rooms_data_parser_selenium[room["name"]]["search"]]
        guests = {
            "max": max(days_list) if days_list else None,
            "min": min(days_list) if days_list else None,
        }

        days_list = [search["date"]["days"]
                     for search in rooms_data_parser_selenium[room["name"]]["search"]]
        days = {
            "max": max(days_list) if days_list else None,
            "min": min(days_list) if days_list else None,
        }

        guests_list = [search["guests"]
                       for search in rooms_data_parser_selenium[room["name"]]["search"]]
        guests = {
            "max": max(guests_list) if guests_list else None,
        }

        date_room["visibility_area"]["days"] = days
        date_room["visibility_area"]["guests"] = guests

        date_room["imgs"] = []
        if rooms_data_parser_selenium.get(room["name"]):
            date_room["price"] = rooms_data_parser_selenium[room["name"]]["price"]
        else:
            date_room["price"] = 0

        for img in room["image_list_tmpl"]:
            w = img["width"]
            h = img["height"]

            url: str = img["src"]

            url = url.replace("{size}", "1024x768")

            date_room["imgs"].append({
                "url": url,
                "size": f"{w}x{h}",
            })

        rooms.append(date_room)

    end_time = int(time.time())

    hotel_data = {
        "debug": {
            "start_time": datetime.datetime.fromtimestamp(start_time).strftime("%d.%m.%Y %H:%M:%S"),
            "end_time": datetime.datetime.fromtimestamp(end_time).strftime("%d.%m.%Y %H:%M:%S"),
            "d_time_m": f"{round((end_time - start_time) / 60, 1)} минут",
            "d_time_s": f"{(end_time - start_time)} секунд",
        },
        "urls": return_urls,
        "name_hotel": name,
        "address": {
            "street": street,
            "house": house_number,
            "city": city,
            "continent": country,
        },
        "description": description,
        "images": images,
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "description": description,
        "services": amenities,
        "rooms": rooms,
    }

    hotel_data.update(additional_data)

    print(f"Скачался за {hotel_data['debug']['d_time_s']}")

    return hotel_data


def parser_hotel_rooms(hotel_id):
    return_urls = []

    dates = [
        ["05.01.2024-10.01.2024", 5],
        ["10.01.2024-14.01.2024", 4],
        ["15.01.2024-20.01.2024", 5],
        ["20.01.2024-25.01.2024", 5],
        ["25.01.2024-30.01.2024", 5],

        ["05.02.2024-10.02.2024", 5],
        ["10.02.2024-14.02.2024", 4],
        ["15.02.2024-20.02.2024", 5],
        ["20.02.2024-25.02.2024", 5],
        ["25.02.2024-30.02.2024", 5],
    ]

    retrun_rooms: dict[str, dict[str, list]] = {}

    additional_values = None
    guests_count_max = 5

    operation_counter = 0
    operation_counter_max = len(dates) * guests_count_max

    for date, days in dates:
        for guests in range(1, guests_count_max + 1):
            url = update_query_params(f"https://ostrovok.ru/hotel/russia/moscow/mid7597114/{hotel_id}/", {"dates": date, "guests": guests})
            return_urls.append(url)
            operation_counter += 1

            if additional_values == None:
                print(f"[{operation_counter}/{operation_counter_max}] {date} | {guests} => ", end="")
                additional_values, rooms = parser_room(url, True, date, days, guests)
                print(f"(+)")
            else:
                print(f"[{operation_counter}/{operation_counter_max}] {date} | {guests} => ", end="")
                _, rooms = parser_room(url, False, date, days, guests)
                print(f"")


            for key, val in rooms.items():
                if not retrun_rooms.get(key):
                    retrun_rooms[key] = {
                        "price": [],
                        "amenity": None,
                        "search": [],
                    }

                retrun_rooms[key]["price"].append(val["price"])
                retrun_rooms[key]["search"].append(val["search"])

                if retrun_rooms[key]["amenity"] == None:
                    retrun_rooms[key]["amenity"] = val["amenity"]

    # [Название] Цена | Гостей => Количество захваченных поисков
    print(f"Информация об номерах [{len(retrun_rooms)}]:")
    for key, val in retrun_rooms.items():
        prices = [round(price["price"] / price["days"])
                  for price in val["price"]]
        max_price = max(prices)

        guests = [search["guests"] for search in val["search"]]
        max_guest = max(guests)

        print(
            f"[{key}] ↑{max_price} | ↑{max_guest} => s{len(val['search'])}")

    return retrun_rooms, additional_values, return_urls


def parser_room(url, get_additional_values: bool, date, days, guests):
    rooms: dict[str, list] = {}

    additional_values = None


    print("[", end="")

    driver_ajax.get(url)

    # ждем полной загрузки страницы
    driver_ajax.execute_script("return document.readyState")

    scripts = driver_ajax.find_elements(
        "xpath", "//script[@type='text/javascript']")

    for script in scripts:
        try:
            driver_ajax.execute_script(script.get_attribute('innerHTML'))
        except:
            pass

    if get_additional_values:
        additional_values = {}
        try:
            title_stars = driver_ajax.find_element(
                By.CLASS_NAME, "zen-roomspage-title-stars")
            stars = title_stars.find_elements(
                By.CLASS_NAME, "zen-ui-stars-star")
            additional_values["stars_count"] = len(stars)
            print(Fore.GREEN + "Звёзды" + Fore.RESET, end=", ")
        except:
            print(Fore.RED + "Звёзды" + Fore.RESET, end=", ")
            additional_values["stars_count"] = 0

        try:
            span_time_in_out = driver_ajax.find_elements(
                By.CLASS_NAME, "PolicyBlock__policyTableCell_checkInCheckOut--sezvV")

            for obj in span_time_in_out:
                if obj.text.startswith("После"):
                    additional_values["time_in"] = obj.text.replace("После", "").strip()
                if obj.text.startswith("До"):
                    additional_values["time_out"] = obj.text.replace("До", "").strip()
            print(Fore.GREEN + "Время" + Fore.RESET, end=", ")
        except:
            print(Fore.RED + "Время" + Fore.RESET, end=", ")
            additional_values["time_in"] = "12:00"
            additional_values["time_out"] = "14:00"

        additional_values["title"] = driver_ajax.title

        # wait = WebDriverWait(driver_ajax, 120)
        # time.sleep(20)

        # for req in driver_ajax.requests:
        #     if req.response:
        #         if re.search("hotel/search/v2/site/hp/pages", req.url):
        #             try:
        #                 body = decode(req.response.body, req.response.headers.get('Content-Encoding', 'identity')).decode('utf-8')
        #                 body_obj = json.loads(body)
        #                 print("Удача получение ajax")
        #                 print(body_obj)
        #             except:
        #                 print("Ошибка получения ajax")
        #                 pass

        # del driver_ajax.requests

    try:
        # Ожидание появления элемента с классом zenroomspage-b2c-rates
        rates = WebDriverWait(driver_ajax, timeout=20).until(lambda d: d.find_elements(By.CLASS_NAME, "zenroomspage-b2c-rates"))
        print(Fore.GREEN + "Номера" + Fore.RESET, end=" ")
    except:
        print(Fore.RED + "Номера" + Fore.RESET, end=" ")
        rates = []

    print(f"{len(rates)}", end="")
    for rate in rates:
        name = rate.find_element(
            By.CLASS_NAME, "zenroomspagerate-name-title").text
        name = name.replace("\n", " ")

        if not rooms.get(name):
            rooms[name] = {
                "price": None,
                "amenity": [],
                "search": None,
            }

        rooms[name]["search"] = {
            "date": {"start": date, "days": days}, "guests": guests}

        price : str = rate.find_elements(
            By.CLASS_NAME, "zenroomspage-b2c-rates-price-amount")[0].text

        if (price.find("млн") != -1):
            price = int(float(price.replace(" ", "").replace("₽", "").replace("млн", "")) * 1000000)
        else:
            price = int(price.replace(" ", "").replace("₽", "").replace(",", ""))

        rooms[name]["price"] = {"price": price, "days": days}

        if len(rooms[name]["amenity"]) == 0:
            amenitys = rate.find_elements(
                By.CLASS_NAME, "zenroomspageroom-header-content-amenity")
            for amenity in amenitys:
                text_amenity = amenity.text
                rooms[name]["amenity"].append(text_amenity)

    print("]", end=" ")

    return additional_values, rooms


def create_webdriver():
    # Create a new instance of the Chrome driver
    chrome_options = webdriver.ChromeOptions()
    chrome_service = Service(executable_path="/usr/bin/chromedriver")

    # Отключение загрузки картинок
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    # Отключение загрузки шрифтов и css
    arguments = [
        '--disable-background-networking', '--disable-breakpad', '--disable-client-side-phishing-detection', '--disable-component-update',
        '--disable-default-apps', '--disable-dev-shm-usage', '--disable-extensions-file-access-check', '--disable-extensions-http-throttling',
        '--disable-extensions-scheme-whitelist', '--disable-extensions', '--disable-features=VizDisplayCompositor', '--disable-gpu',
        '--disable-hang-monitor', '--disable-infobars', '--disable-ipc-flooding-protection', '--disable-logging-redirect', '--disable-logging',
        '--disable-popup-blocking', '--disable-prompt-on-repost', '--disable-renderer-backgrounding', '--disable-setuid-sandbox', '--disable-sync',
        '--disable-threaded-animation', '--disable-threaded-scrolling', '--disable-translate', '--disable-web-security', '--disable-web-security',
        '--disable-webgl', '--disable-xss-auditor', '--disk-cache=true', '--ignore-certificate-errors', '--log-level=3' '--metrics-recording-only',
        '--mute-audio', '--no-first-run', '--no-sandbox', '--no-sandbox', '--safebrowsing-disable-auto-update', '--start-maximized'
    ]

    for arg in arguments:
        chrome_options.add_argument(arg)

    chrome_options.add_argument('--headless=new')

    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)

    # driver.request_interceptor = interceptor

    return driver

def create_webdriver_ajax():
    # Create a new instance of the Chrome driver
    options = webdriver_ajax.FirefoxOptions()
    options.set_preference('intl.accept_languages', 'ru, ru')
    # # chrome_service = Service()

    # # Отключение загрузки картинок
    # # prefs = {"profile.managed_default_content_settings.images": 2}
    # # chrome_options.add_experimental_option("prefs", prefs)

    # # chrome_options.add_argument('--disable-extensions')
    # # chrome_options.add_argument('--disable-infobars')
    # # chrome_options.add_argument('--disable-dev-shm-usage')
    # # chrome_options.add_argument('--disable-gpu')
    # # chrome_options.add_argument('--no-sandbox')
    # # chrome_options.add_argument('--disable-setuid-sandbox')
    # # chrome_options.add_argument('--disable-web-security')
    # # chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    # # chrome_options.add_argument('--disable-logging')
    # # chrome_options.add_argument('--disable-logging-redirect')
    # # chrome_options.add_argument('--disable-background-networking')
    # # chrome_options.add_argument('--disable-breakpad')
    # # chrome_options.add_argument('--disable-client-side-phishing-detection')
    # # chrome_options.add_argument('--disable-component-update')
    # # chrome_options.add_argument('--disable-default-apps')
    # # chrome_options.add_argument('--disable-extensions-http-throttling')
    # # chrome_options.add_argument('--disable-extensions-file-access-check')
    # # chrome_options.add_argument('--disable-extensions-scheme-whitelist')
    # # chrome_options.add_argument('--disable-hang-monitor')
    # # chrome_options.add_argument('--disable-ipc-flooding-protection')
    # # chrome_options.add_argument('--disable-popup-blocking')
    # # chrome_options.add_argument('--disable-prompt-on-repost')
    # # chrome_options.add_argument('--disable-renderer-backgrounding')
    # # chrome_options.add_argument('--disable-sync')
    # chrome_options.add_argument('--disable-translate')
    # # chrome_options.add_argument('--metrics-recording-only')
    # # chrome_options.add_argument('--mute-audio')
    # chrome_options.add_argument('--no-first-run')
    # # chrome_options.add_argument('--safebrowsing-disable-auto-update')
    # chrome_options.add_argument('--start-maximized')
    # chrome_options.add_argument('--disable-webgl')
    # chrome_options.add_argument('--disable-threaded-animation')
    # chrome_options.add_argument('--disable-threaded-scrolling')
    # chrome_options.add_argument('--disable-web-security')
    # chrome_options.add_argument('--disable-xss-auditor')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--disk-cache=true')
    # # chrome_options.add_argument('--log-level=3')
    # chrome_options.add_argument("--enable-logging")


    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    # chrome_options.add_argument('--headless=new')
    options.add_argument("--disable-gpu")

    # return webdriver_ajax.Firefox(options=chrome_options, service=chrome_service)
    return webdriver_ajax.Firefox(options=options)


# driver = create_webdriver()

driver_ajax = create_webdriver_ajax()



class Command(BaseCommand):
    def parser_hotel(self):
        tz = datetime.timezone(datetime.timedelta(hours=3))

        with Xvfb(width=1920, height=1080, colordepth=16) as xvfb:
            while True:
                print(f"Запуск: {datetime.datetime.now(tz).strftime('%d.%m.%Y %H:%M:%S')}")
                parser_data = Constant.get("parser", "json")
                if parser_data:
                    for index, hotel_item in enumerate(parser_data["hotel"]["items"]):
                        if hotel_item["status"] == "not_download":
                            print(f"Скачивание: {hotel_item['id']}")
                            hotel_date = get_hotel(hotel_item["id"])
                            parser_data["hotel"]["items"][index]["param"] = hotel_date
                            parser_data["hotel"]["items"][index]["status"] = "download"
                        if hotel_item["status"] == "materialize_a_hotel_request":
                            print(f"Перенос на сайт: {hotel_item['id']}")
                            try:
                                result = fun_add_hotel(hotel_item["param"], None)
                                parser_data["hotel"]["items"][index]["status"] = "materialize_a_hotel"
                                print(f"Удача")

                                Constant.set("parser", parser_data, "json")

                            except Exception as e:
                                    print(f"Ошибка")
                                    parser_data["hotel"]["items"][index]["status"] = "error"
                                    parser_data["hotel"]["items"][index]["error_param"] = [str(e), str(sys.exc_info()[-1])]
                                    Constant.set("parser", parser_data, "json")

                        Constant.set("parser", parser_data, "json")

                time.sleep(60)

    def handle(self, *args, **kwargs):
        self.parser_hotel()
