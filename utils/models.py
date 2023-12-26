import json
import os
import random
import string
from typing import Type, TypedDict, Union
from django.conf import settings
from django.db import models
from django.urls import reverse
import requests
from transliterate import translit
from hotel.models import Address
from user.models import User
from brontur.funs import generate_password
from django.db.models import Q, QuerySet, Manager, Count
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.core.files.base import ContentFile
from django.utils.text import slugify

import concurrent.futures
from tinymce import HTMLField
from mptt.models import MPTTModel, TreeForeignKey
# Когда буду импортировать на сервер нужно будет сделать в модуле tinymce
#from django.urls import re_path
#from .views import spell_check, filebrowser, css, spell_check_callback
#urlpatterns = [
#    re_path(r'^spellchecker/$', spell_check, name='tinymce-spellchecker'),
#    re_path(r'^filebrowser/$', filebrowser, name='tinymce-filebrowser'),
#    re_path(r'^tinymce4.css', css, name='tinymce-css'),
#    re_path(r'^spellcheck-callback.js', spell_check_callback, name='tinymce-spellcheck-callback')
#]



def upload_to_path(instance, filename):
    return f"img/{generate_password()}.jpg"


class Img(models.Model):
    image = models.ImageField(upload_to=upload_to_path, null=True, blank=True, verbose_name="Файл")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_date = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")
    param = models.JSONField(default=dict, verbose_name="Опции")

    def get_missing_images_paths():
        all_path = []
        for img in Img.objects.all():
            try:
                img.image.size
            except:
                all_path.append(str(img.image).split("/")[1])

        return all_path


    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'

    def creating_a_photo_cache(app_model: str, obj: str):
        from hotel.models import Hotel, RCategory

        url_list = Img.get_url_list(app_model, obj)

        if app_model == "hotel.hotel":
            hotel = Hotel.objects.filter(id=obj).first()

            if hotel:
                hotel.additional_info["url_cache_phote"] = list(url_list)
                hotel.save()

        if app_model == "hotel.rc":
            rc = RCategory.objects.filter(id=obj).first()
            if rc:
                rc.additional_info["url_cache_phote"] = list(url_list)
                rc.save()

    def new(app_model: str, obj: str, file):
        last_order = 0
        last: Img = Img.objects.filter(Q(param__contains={"model": app_model, "obj": obj})).order_by("param__order").last()
        if last:
            last_order = last.param["order"] + 1

        img = Img.objects.create(
            param={
                "model": app_model,
                "obj": obj,
                "order": last_order,
            }
        )

        if file != None:
            img.image.save("", file)

        return img

    def get_id_to_obj(ids: list) -> Manager["Img"]:
        id_to_obj = Img.objects.in_bulk(ids)

        ordered_qs = []
        for id in ids:
            ordered_qs.append(id_to_obj[int(id)])

        return ordered_qs

    def get(app_model: str, obj: str, order=None):
        if order:
            if isinstance(order, int):
                return Img.objects.filter(Q(param__contains={"model": app_model, "obj": obj, "order": order})).order_by("param__order")
            if isinstance(order, list):
                return Img.objects.filter(Q(param__contains={"model": app_model, "obj": obj}, param__order__in=order)).order_by("param__order")
        else:
            return Img.objects.filter(Q(param__contains={"model": app_model, "obj": obj})).order_by("param__order")

    def get_url(app_model: str, obj: str, order=None) -> list:
        imgs = Img.get(app_model, obj, order)
        try:
            return [{"id": obj.id, "url": obj.image.url} for obj in imgs]
        except:
            return [{"id": 0, "url": ""}]


    def get_url_list(app_model: str, obj: str, order=None) -> list[str]:
        imgs = Img.get(app_model, obj, order)
        try:
            return [obj.image.url for obj in imgs]
        except:
            return []


    def not_linked_new():
        """Создаёт не привязаное к модели и обекту изображение, можно использовать чтоб потом привязать его по его ID

        Returns:
            _type_: _description_
        """
        return Img.objects.create(
            param={
                "model": "not_linked",
            }
        )

    def link_to(id, app_model, obj):
        img: Img = Img.objects.filter(id=id)
        img.param["app_model"] = app_model
        img.param["obj"] = obj
        img.save()

    def delete_unused_files():
        media_path = settings.MEDIA_ROOT + '/img/'
        all_files = os.listdir(media_path)

        img_files = Img.objects.all().values_list("image")
        img_files = [os.path.basename(f.name) for f in img_files if f]

        for file_name in all_files:
            if file_name not in img_files:
                os.remove(media_path + file_name)

    def save_image_from_url(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            self.image.save(f"", ContentFile(response.content))
            return True
        return False



def upload_to_path_doc(instance, filename):
    extension = os.path.splitext(filename)[1]
    return f"doc/{generate_password()}{extension}"

ALLOWED_FILE_TYPES = {
    'images': ['.jpeg', '.jpg', '.png', '.webp', '.tiff', ".heif"],
    'documents': ['.pdf', '.doc', '.docx', '.odt', '.txt', '.rtf', '.tex', '.xlsx', '.pptx', '.xml', '.csv', '.eps', '.ods', '.odp', '.odg', '.odf'],
    'video': ['.mp4', '.avi', '.mov', '.flv', '.mkv', '.wmv', '.m4v', '.webm', '.vob', '.qt', '.3gp', '.asf', '.avchd', '.divx'],
    'spreadsheets': ['.ods', '.xls', '.xlsx', '.csv', '.tsv', '.sdc', '.dbf', '.dif', '.slk', '.stc', '.sxc', '.ots'],
}

class Doc(models.Model):
    file = models.FileField(upload_to=upload_to_path_doc, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    param = models.JSONField(default=dict)

    @staticmethod
    def creating_a_photo_cache(app_model: str, obj: str):
        from hotel.models import Hotel, RCategory

        url_list = Doc.get_url_list(app_model, obj)

        if app_model == "hotel.hotel":
            hotel = Hotel.objects.filter(id=obj).first()

            if hotel:
                hotel.additional_info["cache_doc"] = list(url_list)
                hotel.save()

        if app_model == "hotel.rc":
            rc = RCategory.objects.filter(id=obj).first()
            if rc:
                rc.additional_info["cache_doc"] = list(url_list)
                rc.save()

        if app_model == "user.user":
            user = User.objects.filter(id=obj).first()
            if user:
                user.additional_info["cache_doc"] = list(url_list)
                user.save()

    @staticmethod
    def new(app_model: str, obj: str, file):
        extension = os.path.splitext(file.name)[1]
        if extension not in sum(ALLOWED_FILE_TYPES.values(), []):
            return None

        last_order = 0
        last: Doc = Doc.objects.filter(Q(param__contains={"model": app_model, "obj": obj})).order_by("param__order").last()
        if last:
            last_order = last.param["order"] + 1

        doc = Doc.objects.create(
            param={
                "model": app_model,
                "obj": obj,
                "order": last_order,
            }
        )

        if file != None:
            doc.file.save(file.name, file)

        return doc

    @staticmethod
    def get_id_to_obj(ids: list) -> Manager["Doc"]:
        id_to_obj = Doc.objects.in_bulk(ids)

        ordered_qs = []
        for id in ids:
            ordered_qs.append(id_to_obj[int(id)])

        return ordered_qs

    @staticmethod
    def get(app_model: str, obj: str, order=None):
        if order:
            if isinstance(order, int):
                return Doc.objects.filter(Q(param__contains={"model": app_model, "obj": obj, "order": order})).order_by("param__order")
            if isinstance(order, list):
                return Doc.objects.filter(Q(param__contains={"model": app_model, "obj": obj}, param__order__in=order)).order_by("param__order")
        else:
            return Doc.objects.filter(Q(param__contains={"model": app_model, "obj": obj})).order_by("param__order")

    @staticmethod
    def get_url(app_model: str, obj: str, order=None) -> list:
        docs = Doc.get(app_model, obj, order)
        return [{"id": obj.id, "url": obj.file.url} for obj in docs]

    @staticmethod
    def get_url_list(app_model: str, obj: str, order=None) -> list[str]:
        docs = Doc.get(app_model, obj, order)
        return [obj.file.url for obj in docs]


    @staticmethod
    def not_linked_new():
        """Создаёт не привязаное к модели и обекту изображение, можно использовать чтоб потом привязать его по его ID

        Returns:
            _type_: _description_
        """
        return Doc.objects.create(
            param={
                "model": "not_linked",
            }
        )

    @staticmethod
    def link_to(id, app_model, obj):
        doc: Doc = Doc.objects.filter(id=id)
        doc.param["app_model"] = app_model
        doc.param["obj"] = obj
        doc.save()

    @staticmethod
    def delete_unused_files():
        media_path = settings.MEDIA_ROOT + '/doc/'
        all_files = os.listdir(media_path)

        doc_files = Doc.objects.all().values_list("file")
        doc_files = [os.path.basename(f.name) for f in doc_files if f]

        for file_name in all_files:
            if file_name not in doc_files:
                os.remove(media_path + file_name)


@receiver(pre_delete, sender=Img)
def image_model_delete(sender, instance, **kwargs):
    if instance.image.name:
        instance.image.delete(False)

class LogAction(models.Model):
    LOG_TYPE_CHOICES = [
        ("hotel", 'Отель'),
        ("user", 'Пользователь'),
        ("site", 'Сайт'),
        ("api", "API"),
    ]

    LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    level = models.CharField(choices=LEVEL_CHOICES, max_length=20)
    message = models.TextField()
    log_type = models.CharField(choices=LOG_TYPE_CHOICES, max_length=20)

    @classmethod
    def create(cls, level, message, log_type):
        log = cls(level=level, message=message, log_type=log_type)
        log.save()
        return log

    @classmethod
    def get_logs(cls, log_type):
        return cls.objects.filter(log_type=log_type)


class Constant(models.Model):
    code = models.CharField(max_length=255, unique=True)
    value = models.TextField()

    def __str__(self):
        return self.code

    @classmethod
    def set(cls, code, value, type = 'str'):
        if type == "json":
            value = json.dumps(value)

        obj, created = cls.objects.update_or_create(
            code=code.lower(),
            defaults={'value': value},
        )
        return obj

    @classmethod
    def get(cls, code, type = "str") -> Union[str, dict]:
        obj = cls.objects.filter(code=code.lower()).first()
        if obj:
            if type == "str":
                return obj.value
            elif type == "json":
                return json.loads(obj.value)
        return None

    class CashbackCalculationReturnType(TypedDict):
        value: int
        lifetime: int

    def cashback_calculation(hotel_type, cashback_type, site_price, accommodation) -> CashbackCalculationReturnType:
        """Получения значений для кешбека

        Args:
            hotel_type (str): Тип отеля
            cashback_type (str): Тип кешбека booking, review, to_hotel
            site_price (int): Цена за сайт
            accommodation (int): Полная стоимость номера

        Raises:
            ValueError: Не удалось рассчитать кэшбэк

        Returns:
            dict: value (int), lifetime (int)
        """
        settings = Constant.get("settings_options", "json")
        obj = settings["cashback_table"][hotel_type][cashback_type]

        if obj["type"] == "accommodation":
            return {
                "value": round(accommodation * obj["value"] / 100),
                "lifetime": obj["lifetime"]
            }

        if obj["type"] == "site_price":
            return {
                "value": round(site_price * obj["value"] / 100),
                "lifetime": obj["lifetime"]
            }

        raise ValueError(f"Не удалось рассчитать кэшбэк для [{hotel_type}, {cashback_type}]")

    class Meta:
        verbose_name = 'Переменая'
        verbose_name_plural = 'Переменые'


class Payment(models.Model):
    orderNumber = models.CharField(max_length=16)
    orderID = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    param = models.JSONField(default=dict)


class Mailing(models.Model):
    email = models.CharField(max_length=50, verbose_name='Адрес электронной почты')
    date_modified = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    is_sent = models.BooleanField(default=False, verbose_name='Отправлено')
    is_enabled = models.BooleanField(default=False, verbose_name='Включено')

    def get_emails(self):
        return [obj.email for obj in Mailing.objects.all()]

    def add_email(email):
        Mailing.objects.create(email=email)

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'

class Place(models.Model):
    PLACE_TYPES = [
        ('city', 'Город'),
        ('town', 'Городок'),
        ('village', 'Деревня'),
        ('settlement', 'Поселок'),
        ('hamlet', 'Хутор'),
        ('suburb', 'Пригород'),
        ('region', 'Регион'),
        ('province', 'Провинция'),
        ('state', 'Штат'),
        ('country', 'Страна'),
        ('continent', 'Континент'),
        ('other', 'Другое')
    ]

    name = models.CharField(max_length=255)
    en_name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, blank=True, null=True)
    coordinates = models.CharField(max_length=255, blank=True, null=True)
    place_type = models.CharField(max_length=255, choices=PLACE_TYPES)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='children')
    auto_created = models.BooleanField(default=0)
    hotels = models.ManyToManyField('hotel.Hotel', related_name='places', verbose_name='Отели', blank=True)
    active = models.BooleanField(default=1)


    qwert_to_ycyken = {
        'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't',
        'н': 'y', 'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p',
        'х': '[', 'ъ': ']', 'ф': 'a', 'ы': 's', 'в': 'd',
        'а': 'f', 'п': 'g', 'р': 'h', 'о': 'j', 'л': 'k',
        'д': 'l', 'ж': ';', 'э': "'", 'я': 'z', 'ч': 'x',
        'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm',
        'б': ',', 'ю': '.', 'ё': '`', ' ': ' '
    }

    ycyken_to_qwert = {value: key for key, value in qwert_to_ycyken.items()}

    @staticmethod
    def detect_layout(text: str) -> str:
        if all(c in Place.qwert_to_ycyken for c in text.lower()):
            return "qwerty"
        elif all(c in Place.ycyken_to_qwert for c in text.lower()):
            return "йцукен"
        else:
            raise ValueError("Unable to detect layout")

    @staticmethod
    def convert_layout(text: str) -> str:
        from_layout = Place.detect_layout(text)

        # Создадим список, в который будем добавлять символы в правильной раскладке
        new_text = []

        # Создадим словарь соответствий символов в раскладке from_layout и to_layout
        if from_layout == 'qwerty':
            layout_dict = Place.qwert_to_ycyken
            to_layout = 'йцукен'
        elif from_layout == 'йцукен':
            layout_dict = Place.ycyken_to_qwert
            to_layout = 'qwerty'
        else:
            raise ValueError("Unsupported layout")
        # Пройдемся по каждому символу в тексте
        for char in text:
            # Если символ есть в словаре, то добавим соответствующий ему символ в правильной раскладке в новый список
            if char.lower() in layout_dict:
                new_text.append(layout_dict[char.lower()].upper() if char.isupper() else layout_dict[char.lower()])
            # Если символ не найден в словаре, то просто добавим его в новый список
            else:
                new_text.append(char)

        # Объединим все символы в новом списке в одну строку
        return ''.join(new_text)

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        slug = self.slug
        return reverse("hotel_search", kwargs={'slug': slug})

    @staticmethod
    def get_list_mini():
        places = []
        for place in Place.objects.all():

            if place.parent:
                places.append({
                    "id": place.id,
                    "title": place.name + ", " + place.parent.name,
                })

        return places


    def get_slug(self):
        slug = ""
        if not self.slug:
            parent = self.get_top_parent()
            if self.id == parent.id:
                self_name = self.en_name
                slug = slugify(self.name)
            else:
                self_name = self.en_name
                parent_name = parent.en_name
                slug = slugify(parent_name) + "/" + slugify(self_name)

            self.slug = slug
            self.save()
        else:
            slug = self.slug
        return slug

    def get_top_parent(self) -> "Place":
        if self.parent is None:
            return self
        return self.parent.get_top_parent()

    def get_descendants(self : "Place"):
        descendants = []
        children = self.children.all()
        for child in children:
            child : Place
            descendants.append(child)
            descendants += child.get_descendants()
        return descendants

    def get_descendants_name(self : "Place") -> list[str]:
        """
        Функция get_descendants_name рекурсивно извлекает имена всех потомков данного места.

        :param self: Параметр «self» относится к текущему экземпляру класса Place. Он используется для
        доступа к атрибутам и методам текущего экземпляра
        :type self: "Place"
        :return: список имен всех потомков данного места.
        """
        descendants = []
        children = self.children.all()
        for child in children:
            child : Place
            descendants.append(child.name)
            descendants += child.get_descendants_name()
        return descendants


    def get_parents(self) -> list["Place"]:
        parents = []
        parent = self.parent

        while parent is not None:
            parents.append(parent)
            parent = parent.parent

        return parents

    def get_parents_sity(self) -> list["Place"]:
        parents = []
        parent = self.parent

        while parent is not None:
            parent : Place
            parents.append(parent.name)
            parent = parent.parent

        return parents

    def get_all_objects_children(self):
        descendants = self.children.all()

        node = {
            'place': self,
            'children': []
        }

        for descendant in descendants:
            node['children'].append(descendant.get_all_objects_children())

        return node

    def get_all_objects(self=None):
        if self is None:
            top_level_places = Place.objects.filter(parent=None)

        objects_list = []
        for place in top_level_places:
            objects_list.append(place.get_all_objects_children())
        return objects_list

    @staticmethod
    def get_address(places, separator=', ', with_type=False):
        address_parts = []

        for place in places:
            if with_type:
                address_parts.append(f'[{place.place_type}]{place.name}')
            else:
                address_parts.append(place.name)

        return separator.join(address_parts)

    @staticmethod
    def process_unknown_places(unknown_places):
        for place in unknown_places:
            name : str = place["name"]
            #Проверка что первый символ большой
            if not (name[0].upper() == name[0]):
                continue

            #Проверка что в название не более 10% цифр
            if not (sum(char.isdigit() for char in name) / len(name) <= 0.1):
                continue

            addres = Address.objects.filter(city=name).first()
            if addres:
                coordinates = addres.coordinates
                Place.objects.create(name = name, coordinates = coordinates, place_type = "other", parent = None, auto_created = True, active = False, )
        return True

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'


class AdminLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Лог админа'
        verbose_name_plural = 'Логи админа'

class ShortLink(models.Model):
    original_url = models.URLField()
    short_code = models.CharField(max_length=10, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    option = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return self.original_url

    def create_short_code(self):
        code_length = 6
        characters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        short_code = ''.join(random.choice(characters) for _ in range(code_length))
        return short_code

    def save(self, *args, **kwargs):
        if not self.short_code:  # Если короткий код отсутствует, создайте его
            self.short_code = self.create_short_code()

        return super().save(*args, **kwargs)

    def get_absolute_url(self):
            return "http://127.0.0.1:8000" + reverse('shortlink_redirect', args=[self.short_code])

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'


class DocumentationPage(MPTTModel):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    slug = models.SlugField(unique=True, verbose_name='URL')
    content = HTMLField(verbose_name='Текст')
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE, verbose_name='Родительская страница')
    related_pages = models.ManyToManyField('self', blank=True, related_name='related', symmetrical=False, verbose_name='Связанные страницы')
    order = models.IntegerField(default=0, verbose_name='Порядок')



    class MPTTMeta:
        verbose_name = 'Страница документации'
        verbose_name_plural = 'Страницы документации'
        order_insertion_by = ['order']

    def save(self, *args, **kwargs):
        slug = slugify(translit(self.title, 'ru', reversed=True))
        self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f'/documentation/{self.slug}'

    def __str__(self):
        return f"{self.title} [{self.slug}]"

    def get_flat_documentation_pages():
        flat_list = []
        pages = DocumentationPage.objects.get_queryset()  # Получаем все страницы документации и их дочерние страницы
        root_pages = pages.filter(parent__isnull=True)  # Фильтруем только корневые страницы

        def add_to_flat_list(page, depth):
            flat_list.append({
                "id": page.id,
                "title": page.title,
                "url": page.get_absolute_url(),
                "level": depth
            })  # Добавляем словарь в плоский список
            children = page.children.all()
            for child in children:
                add_to_flat_list(child, depth + 1)  # Рекурсивно добавляем дочерние страницы

        for page in root_pages:
            add_to_flat_list(page, 0)  # Вызываем рекурсивную функцию для каждой корневой страницы

        return flat_list

    class Meta:
        verbose_name = 'Документация'
        verbose_name_plural = 'Документация'