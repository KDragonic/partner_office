from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from user.models import Profile
import telebot
from telebot import types
import json

bot = telebot.TeleBot(settings.TELEGRAM_BOT_API_KEY)


class Command(BaseCommand):
		def handle(self, *args, **kwargs):
				bot.enable_save_next_step_handlers(delay=2) # Сохранение обработчиков
				bot.load_next_step_handlers()								# Загрузка обработчиков
				bot.infinity_polling()
				print("Бот запустился")


@bot.message_handler(commands=['start'])
def start_message(message):
		print("Показ привет")
		bot.send_message(message.chat.id, "Здравствуйте, я бот который поможет не забыть о бронирование")

@bot.message_handler(commands=['Профиль'])
def get_profile(message:telebot.types.Message):
		print("Показ профиля")
		profile = Profile.objects.get(token_telegram=message.from_user.id)
		user = profile.user
		bot.send_message(message.chat.id, f"{user.username} {user.first_name} {user.last_name}")

@bot.message_handler(commands=['data'])
def get_profile(message:telebot.types.Message):
		print("Вывод информации")

		mass = {
			"message_id": message.message_id,
			"from": message.from_user.id,
			"date": message.date,
		}

		bot.send_message(message.chat.id,  json.dumps(mass))
		# json.dumps()