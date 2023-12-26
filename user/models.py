import base64
import datetime
import json
import random
import re

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, UserManager
from django.contrib.auth.models import PermissionsMixin, Permission
from brontur import settings
import brontur.funs as funs
from django.utils import timezone
from django.db.models import QuerySet, Q
from cryptography.fernet import Fernet
import secrets
import cryptocode
from brontur.funs import generate_password


class MyUserManager(BaseUserManager):
    def create_user(self, username: str, lastname: str, middlename: str, email: str, login: str, password: str, gender: str, phone: str, active_code_email=None, ignor_valid: bool = False):
        if not ignor_valid:
            if not email:
                raise ValueError(
                    'Пользователи должны иметь адрес электронной почты')

            if not login:
                raise ValueError('Пользователи должны иметь логин')

            if not password:
                raise ValueError('Пользователи должны иметь пароль')

            if not username:
                raise ValueError('Пользователи должны иметь имя')

            if not lastname:
                raise ValueError('Пользователи должны иметь фамилию')

            if not gender:
                raise ValueError('Пользователи должны иметь гендер')

            if not phone:
                raise ValueError('Пользователи должны иметь телефон')

        email = self.normalize_email(email)
        uid = funs.gen_uid()


        user = self.model(
            uid=uid,
            email=email,
            login=login,
            password=password,
            username=username,
            lastname=lastname,
            middlename=middlename,
            gender=gender,
            phone=phone,
            active_code_email=active_code_email,
        )
        user : User


        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, password, uid, username):
        user = self.create_user(
            username=username,
            lastname="",
            middlename="",
            email="",
            login=username,
            password=password,
            gender="",
            phone="",
            ignor_valid=True,
        )
        user.uid = uid
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def authenticate(login, password):
        users: User = User.objects.filter(Q(login=login) | Q(
            email=login) | Q(phone=login) | Q(uid=login))

        for user in users:
            if user and user.check_password(password):
                return user
        return None


class User(AbstractBaseUser, PermissionsMixin):
    user_type_choices = [
        ("client", "Клиент"),
        ("hotel", "Отельер"),
        ("moder", "Модератор"),
        ("admin", "Админ"),
        ("owner", "Владелец"),
    ]

    uid = models.CharField(
        verbose_name='Индивидуальный код', max_length=19, unique=True)
    email = models.EmailField(
        verbose_name='Электронная почта', max_length=100, default="", blank=True)
    login = models.CharField(verbose_name='Логин',
                             max_length=50, default="", blank=True)

    date_joined = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)
    last_login = models.DateTimeField(
        verbose_name='Последний вход', auto_now=True)
    is_admin = models.BooleanField(verbose_name='Администратор', default=False)
    is_active = models.BooleanField(verbose_name='Активный', default=True)
    is_staff = models.BooleanField(verbose_name='Персонал', default=False)

    is_superuser = models.BooleanField(
        verbose_name='Суперпользователь', default=False)

    user_type = models.CharField(choices=user_type_choices,
                                 verbose_name='Тип пользователя', max_length=50, default="client")

    username = models.CharField(
        verbose_name='Имя', max_length=30, default="", blank=True)
    lastname = models.CharField(
        verbose_name='Фамилия', max_length=30, default="", blank=True)
    middlename = models.CharField(
        verbose_name='Отчество', max_length=30, default="", blank=True)

    phone = models.CharField(verbose_name='Телефон',
                             max_length=50, default="", blank=True)
    active_phone = models.BooleanField(
        verbose_name='Телефон - активнен', default=0)
    active_code_phone = models.CharField(
        verbose_name='Телефон - код активации', max_length=30, null=True, blank=True)

    phone_2 = models.CharField(
        verbose_name='Доп. телефон', max_length=50, default="", blank=True)
    active_phone_2 = models.BooleanField(
        verbose_name='Доп. телефон - активнен', default=0)
    active_code_phone_2 = models.CharField(
        verbose_name='Доп. телефон - код активации', max_length=30, null=True, blank=True)

    rbal = models.PositiveIntegerField(
        verbose_name='Реальные деньги', default=0, blank=True)

    nationality = models.CharField(
        verbose_name='Национальность/гражданство', max_length=20, default="", blank=True)
    date_birth = models.DateField(verbose_name='Дата рождения', null=True, blank=True)
    gender = models.CharField(verbose_name='Пол', max_length=20)

    email = models.CharField(verbose_name='Почта',
                             max_length=40, null=True, blank=True)
    active_email = models.BooleanField(
        verbose_name='Почта - активна', default=0)
    active_code_email = models.CharField(
        verbose_name='Почта - код активации', max_length=30, default=0, null=True, blank=True)

    token_google = models.CharField(
        verbose_name='Токен Google', max_length=40, null=True, blank=True)
    token_vk = models.CharField(
        verbose_name='Токен ВКонтакте', max_length=40, null=True, blank=True)
    token_telegram = models.CharField(
        verbose_name='Токен Telegram', max_length=40, null=True, blank=True)

    access_token = models.CharField(
        verbose_name='Токен доступа', max_length=200, null=True, blank=True)
    access_token_key = models.CharField(
        verbose_name='Ключ токена доступа', max_length=200, null=True, blank=True)

    additional_info = models.JSONField(
        default=dict, blank=True, verbose_name='Доп. параметры')  # Дополнителные параметры

    USERNAME_FIELD = 'uid'
    REQUIRED_FIELDS = ['username']

    objects = MyUserManager()

    def __str__(self):
        return f"({self.id}) {self.email} {self.username}"

    # Проверка на доступ к части сайта
    def has_user_type(self, type_user):
        return self.user_type == type_user

    def get_main_account(self):
        id_main_account = self.additional_info.get("main_account")
        if id_main_account:
            return User.objects.get(id=id_main_account)

        return self

    def get_mini_accounts(self):
        """Получения всех мини аккаунтов пользователя

        Returns:
            users: Список мини акаутов в формате QS
        """

        users = User.objects.filter(Q(additional_info__main_account=self.id))

        return users

    def create_mini_account(self):
        new_user_data = {
            "uid": funs.gen_uid(),
            "additional_info": {
                "main_account": self.id
            }
        }
        user = User.objects.create(
            **new_user_data
        )

        return user

    def get_FIO(self):
        FIO : str = f"{self.lastname} {self.username} {self.middlename}"
        FIO = FIO.strip()
        if len(FIO) == 0:
            FIO = "Нет ФИО"
        return FIO

    @property
    def avatar(self):
        from utils.models import Img
        avatar = self.additional_info.get("avatar")
        if not avatar:
            imgs = Img.get_url("user.avatar", self.id)
            if len(imgs) > 0:
                avatar = imgs[0]
                self.additional_info["avatar"] = avatar
        return avatar

    @property
    def fio(self):
        FIO : str = f"{self.lastname} {self.username} {self.middlename}"
        FIO = FIO.strip()
        return FIO

    @property
    def str_date_birth(self):
        if not self.date_birth: return ""
        return self.date_birth.strftime("%d.%m.%Y")


    def normal(user) -> "User":
        try:
            if isinstance(user, int):
                return User.objects.get(id=user)
            else:
                return User.objects.get(id=user.id)
        except:
            return None

    # Метод для шифрования access_token
    def encrypt_access_token(access_token: str):
        access_token_key = 'HLJOcS7lqWHE'

        encrypted_token = cryptocode.encrypt(access_token, access_token_key)

        return encrypted_token

    # Метод для расшифровки access_token
    def decrypt_access_token(encrypted_access_token: str):
        access_token_key = 'HLJOcS7lqWHE'

        decrypt_token = cryptocode.decrypt(
            encrypted_access_token, access_token_key)

        return decrypt_token

    # Метод для получения зашифрованного access_token
    def get_access_token(self):
        if not self.access_token:
            self.access_token = generate_password(15)
            self.save()

        return User.encrypt_access_token(self.access_token)

    # Метод для проверки совпадения расшифрованного access_token
    def check_access_token(self, encrypted_access_token):
        decrypted_access_token = User.decrypt_access_token(
            encrypted_access_token)
        return decrypted_access_token == self.access_token

    def send_telegram(user, mess: str, parse_mode=False):
        from bot.views import send_message

        if user.token_telegram:
            if not re.match('auth_code', user.token_telegram):
                return send_message(user.token_telegram, mess, parse_mode=parse_mode)

        return False

    def send_email(user, title, mess: str):
        from user.mail import send as send_mail

        result = send_mail("raw", title, user.email, mess)
        return result

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    pass
    import chat.models
    chats = QuerySet[chat.models.Chat]


class Bonus_rubles(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.PositiveIntegerField()
    date = models.DateTimeField(default=timezone.now)
    text = models.CharField(max_length=100, default="")  # Описания бонуса
    notification_marks = models.JSONField(default=dict, blank=True)
    lifespan = models.PositiveIntegerField(default=182)  # Срок жизни бонуса


    def __str__(self):
        return f"({self.id}) user-{self.user.id} {self.value}"

    def get_notification_marks(self):
        marks = {
            "5_m": "5 месяцев",
            "4_m": "4 месяца",
            "3_m": "3 месяца",
            "2_m": "2 месяца",
            "1_m": "1 месяц",
            "7_d": "неделю до сгорания",
            "2_d": "2 дня",
        }
        return {marks[k]: v for k, v in self.notification_marks.items()}

    def get_last_false(self):
        for k in self.notification_marks:
            if not self.notification_marks[k]:
                return self.notification_marks

    def days_left(self):
        # жизненный цикл бонуса - 6 месяцев
        bonus_lifetime = timezone.timedelta(days=self.lifespan)
        time_passed = timezone.now() - self.date
        time_left = bonus_lifetime - time_passed
        return time_left.days  # количество дней до конца жизни бонуса

    def get_days_left(self):
        marks = {
            "5_m": 150,
            "4_m": 120,
            "3_m": 90,
            "2_m": 60,
            "1_m": 30,
            "7_d": 7,
            "2_d": 2
        }
        last_false = self.get_last_false()
        if last_false is None:
            return None
        days_left = marks[last_false]
        bonus_date = self.date + datetime.timedelta(days=days_left)
        return (bonus_date - datetime.datetime.now()).days

    def get(user: User):
        """
        Функция принимает объект типа User и возвращает словарь, содержащий количество и сумму бонусных рублей пользователя.

        Параметры:
        - user: Объект типа User, обязательный параметр.

        Возвращаемое значение:
        Словарь, содержащий:
        - count: количество бонусных рублей пользователя.
        - sum: сумма бонусных рублей пользователя.

        Если при вычислении суммы произойдет ошибка, функция вернет словарь {"count": 0, "sum": 0}.

        Пример использования:
        ```
        from models import User, Bonus_rubles

        user = User.objects.first()
        bonus_dict = get(user)
        print(bonus_dict)
        ```

        Описание работы функции:
        Функция получает объект User, затем находит все записи в таблице Bonus_rubles, связанные с данным пользователем и вычисляет сумму бонусных рублей. Если при этом происходит ошибка, функция возвращает словарь {"count": 0, "sum": 0}. Если ошибок не происходит, функция возвращает словарь, содержащий количество и сумму бонусных рублей пользователя.
        """
        brs = Bonus_rubles.objects.filter(user=user)
        try:
            sum = 0
            for br in brs:
                sum += br.value

            count = len(brs)
        except:
            return {"count": 0, "sum": 0}
        else:
            return {"count": count, "sum": sum}

    @staticmethod
    def add(user: User, value: int, lifetime = 180, text : str = ""):
        """
        Функция создает новую запись в БД таблице Bonus_rubles.

        :param user: объект класса User
        :param value: целочисленное значение баллов
        :param lifetime: продолжительность бонуса
        :param text: описание бонуса
        """
        if value > 0:
            Bonus_rubles.objects.create(
                user=user,
                value=value,
                lifespan=lifetime,
                text=text,
                date=datetime.datetime.now(),
            )
        elif value < 0:  # Если за самма отрицательная то это онимания баллов
            Bonus_rubles.deny(user, -value)

    def percent(user: User, value: int):
        """
        Функция вычисляет процент скидки для пользователя.

        :param user: объект класса User
        :param value: целочисленное значение баллов
        :return: дробное число - процент скидки
        """
        BR_get_result = Bonus_rubles.get(user)
        value_pricet = value / 10  # Сколько за 10% можно отнять
        if BR_get_result["sum"] == 0:
            return float('inf')

        if BR_get_result["sum"] >= value_pricet:
            return 0.1
        else:
            return value_pricet / BR_get_result["sum"]

    def deny(user: User, value: int):
        """
        Функция удаляет запись из таблицы Bonus_rubles и вызывает сама себя, если необходимо отнять баллов больше, чем есть в одной записи.

        :param user: объект класса User
        :param value: целочисленное значение баллов
        """
        if Bonus_rubles.get(user)["sum"] - value >= 0:
            last_bonus = Bonus_rubles.objects.filter(
                user=user).order_by("-date").first()

            last_bonus_value = last_bonus.value

            if last_bonus_value >= value:  # Если больше отнимается чем есть в одном
                last_bonus.value -= value
                last_bonus.save()
            else:
                value -= last_bonus_value
                last_bonus.delete()
                Bonus_rubles.deny(user, value)

    class Meta:
        verbose_name = 'Бонус пользователя'
        verbose_name_plural = 'Бонусы пользователя'


class FinancialOperation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.IntegerField()
    isBonus = models.BooleanField(default=False)
    datetime = models.DateTimeField()
    operation_type = models.CharField(max_length=50)
    comments = models.TextField()

    def new(user: User, price: int, isBonus: bool, type: str, text: str):
        # if (price != 0):
        FinancialOperation.objects.create(
            user=user,
            price=price,
            isBonus=isBonus,
            datetime=datetime.datetime.now(
                datetime.timezone(datetime.timedelta(hours=3))),
            operation_type=type,
            comments=text,
        )


    class Meta:
        verbose_name = 'Финансовая операция'
        verbose_name_plural = 'Финансовые операция'


# [Устарело] (Но код сломается без этого =( )
class Child(models.Model):  # Ребёнок в поисковике
    age = models.SmallIntegerField()

    def set_many(sid, age_c):
        Child.objects.filter(sid=sid).delete()
        childs = []
        for age in age_c:
            childs.append(Child.objects.create(sid=sid, age=age).age)
        return childs

    class Meta:
        verbose_name = 'Ребёнок'
        verbose_name_plural = 'Дети'

# [Устарело] (Но код сломается без этого =( )
class Companion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=60)
    lastname = models.CharField(max_length=60)
    firstname = models.CharField(max_length=60)
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Компаньен'
        verbose_name_plural = 'Компаньены'


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField()
    url = models.URLField(null=True, blank=True, default=None)
    datetime = models.DateTimeField()
    viewed = models.BooleanField(default=False)
    push = models.BooleanField(default=False)
    delete_on_click = models.BooleanField(default=False)

    def new(user: User, title: str, text: str, url=None, push=False, delete_on_click=False, quietly=False, send_by_mail_and_telegram = False):
        """
        Метод `new` создает новый объект уведомления и сохраняет его в базе данных.
        """
        notification = Notification.objects.create(
            user=user,
            title=title,
            text=text,
            datetime=datetime.datetime.now(),
            url=url,
            push=push,
            delete_on_click=delete_on_click,
        )

        content = {}

        already_sent = False

        if user.user_type in ["moder", "admin", "owner"]:
                content["type"] = "admin_notif"
                content["telegram"] = user.send_telegram(f"*{title}*\n{text}", parse_mode=True)
                content["email"] = user.send_email(title, text)
                already_sent = True

        else:
            if send_by_mail_and_telegram and not already_sent:
                content["type"] = "client"
                content["telegram"] = user.send_telegram(f"*{title}*\n{text}", parse_mode=True)
                content["email"] = user.send_email(title, text)

        notification.save()

        return content

    def open_link(id):
        notif = Notification.objects.get(id=id)
        url = notif.url
        notif.delete()
        return url

    def get(user: User):
        if user.is_authenticated:
            notifications = Notification.objects.filter(user=user)
            list_notifications = list(notifications.values())
            list_notifications.reverse()
            for index, item in enumerate(list_notifications):
                list_notifications[index]["datetime"] = list_notifications[index]["datetime"] + \
                    datetime.timedelta(hours=3)
                list_notifications[index]["datetime"] = list_notifications[index]["datetime"].strftime(
                    "%d.%m.%Y %H:%M")
            notifications.update(push=False)
            return list(list_notifications)
        return []

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'



class Notice(models.Model):
    TEMPS = {
        'registration_confirmation': {
            'telegram': 'Привет, {username}! Мы рады сообщить тебе, что твоя заявка на участие в {event_name} была принята!',
            'email': 'Здравствуй, {username}!<br>Мы хотим предоставить тебе информацию о твоей заявке на участие в {event_name}.',
            'website': 'Добро пожаловать, {username}!<br>Ты успешно зарегистрировался на {event_name}.'
        },
        'contest_winner_notification': {
            'telegram': 'Привет, {username}! Отличная новость - мы выбрали тебя в качестве победителя в конкурсе {contest_name}!',
            'email': 'Поздравляю, {username}!<br>Ты стал победителем в конкурсе {contest_name}.',
            'website': 'Поздравляем, {username}!<br>Ты победил в конкурсе {contest_name} и получаешь приз!'
        },
        'job_offer': {
            'telegram': 'Привет, {username}! У нас для тебя новое предложение - присоединись к нашей команде разработчиков!',
            'email': 'Привет, {username}!<br>Мы предлагаем тебе стать частью нашей команды разработчиков.',
            'website': '{username}, у нас есть интересное предложение для тебя - присоединись к нашей команде разработчиков!'
        },
        'webinar_reminder': {
            'telegram': 'Привет, {username}! Мы хотим напомнить тебе о вебинаре {webinar_name}, который состоится завтра.',
            'email': 'Привет, {username}!<br>Напоминаем тебе о важном событии - вебинар {webinar_name} состоится завтра.',
            'website': '{username}, не забудь о вебинаре {webinar_name}, который состоится завтра.'
        },
        'daily_reminder': {
            'telegram': 'Привет, {username}! Это твоё ежедневное напоминание - продолжай развиваться и учиться новому!',
            'email': 'Привет, {username}!<br>Хотим напомнить тебе о важности постоянного обучения и личностного роста.',
            'website': '{username}, не забывай, что развитие и обучение - важные компоненты успеха!'
        }
    }

    TEMPS_CHOICES = [
        ('registration_confirmation', 'Подтверждение регистрации'),
        ('contest_winner_notification', 'Уведомление о победе в конкурсе'),
        ('job_offer', 'Предложение о работе'),
        ('webinar_reminder', 'Напоминание о вебинаре'),
        ('daily_reminder', 'Ежедневное напоминание')
    ]

    TEMPS_DISPLAY_OPTIONS = {
        "registration_confirmation": {
            "title": "Подтверждение регистрации",
            "icon": None,
        },
        "contest_winner_notification": {
            "title": "Уведомление о победе в конкурсе",
            "icon": None,
        },
        "job_offer": {
            "title": "Предложение о работе",
            "icon": None,
        },
        "webinar_reminder": {
            "title": "Напоминание о вебинаре",
            "icon": None,
        },
        "daily_reminder": {
            "title": "Ежедневное напоминание",
            "icon": None,
        },
    }
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    template = models.CharField(max_length=255, choices=TEMPS_CHOICES, verbose_name='Шаблон')
    option = models.JSONField(default=dict, blank=True, verbose_name='Опции')
    push = models.CharField(max_length=20, default="not_viewed", choices=[('not_shown', 'Не показывать'), ('not_viewed', 'Ещё не показано'), ('shown', 'Показано')], verbose_name='Push')
    view_type = models.CharField(max_length=20, default="not_viewed", choices=[('not_viewed', 'Ещё не показано'), ('shown', 'Показано'), ('visited', 'Перешёл')], verbose_name='Тип просмотра')
    url = models.CharField(max_length=400, default="/", null=True, blank=True, verbose_name='Url')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    viewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата просмотра')

    @classmethod
    def new(cls, user, template, option, push="not_viewed"):
        notice = cls(user=user, template=template, option=option)
        notice.save()
        return notice

    def pre_save(self):
        if not self.option.get("values"):  # Проверяем, пустое ли поле option
            self.option["values"] = dict.fromkeys(self._get_template_values(Notice.TEMPS[self.template]["telegram"]), "")

    def save(self, *args, **kwargs):
        self.pre_save()
        super().save(*args, **kwargs)


    @staticmethod
    def _get_template_values(template):
        import re
        matches = re.findall(r'{(.*?)}', template)
        return matches

    def get_template(self, template_type, reset=False):
        if not reset and f'hash_{template_type}' in self.option:
            return self.option[f'hash_{template_type}']
        else:
            template = Notice.TEMPS[self.template][template_type]
            values_from_option = self.option.get('values', {})
            template_values = self._get_template_values(template)

            missing_values = set(template_values) - set(values_from_option)
            if missing_values: raise ValueError(f"Не хватает значений для шаблона: {', '.join(missing_values)}")

            for key, value in values_from_option.items():
                template = template.replace(f'{{{key}}}', str(value))

            self.option[f'hash_{template_type}'] = template
            self.save()
            return template

    def open_link(id):
        notic = Notice.objects.get(id=id)
        action = notic.action.get("url")
        return action

    def get_notifications(user):
        if user.is_authenticated:
            notices = Notice.objects.filter(user=user)
            list_notices = [
                {
                    "title": Notice.TEMPS_DISPLAY_OPTIONS[notice.template]["title"],
                    "text": notice.option[f'hash_website'],
                    "created_at": notice.created_at,
                    "view_type": notice.view_type,
                    "push": notice.push,
                } for notice in notices
            ]
            list_notices.reverse()
            # notices.update(push='shown')
            return list(list_notices)
        else:
            return []

    class Meta:
        verbose_name = 'Уведомление+'
        verbose_name_plural = 'Уведомления+'