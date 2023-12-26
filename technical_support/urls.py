from django.contrib.auth import views as auth
from django.urls import path
from . import views
urlpatterns = [
    path('pattern/', views.page_tpl_ts, name='techsupport.pattern'),
    path('create_ts/', views.create_ts, name='techsupport.create_ts'),
    path('chat/', views.page_chat, name='techsupport.page_chat'),
]
