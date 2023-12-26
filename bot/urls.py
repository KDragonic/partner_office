from django.contrib import admin
from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    path('telebot/start/', views.start, name="telebot.start"),
    path('telebot/check/', views.check, name="telebot.check"),
    path('telebot/end/', views.end, name="telebot.end"),
    path('telebot/webhook/', views.webhook, name="telebot.webhook"),
    path('telebot/getUpdates/', views.getUpdates, name="telebot.getUpdates"),
]