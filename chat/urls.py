from django.urls import path

from chat import views

urlpatterns = [
    #ajax
    path('chat/get/', views.get_chat, name='get_chat'),
    path('chat/messages/', views.messages, name='chat_messages'),
    path('chat/send/', views.send, name='chat_send'),


    path('chat/get_chats/', views.get_list, name='chat_get_list'),
    path('chat/load/', views.chat_load, name='chat_load'),
]
