from django.urls import path
from .views import other

urlpatterns = [
    # Авторезация
    path('register/', other.page_register, name='register'),
    path('login/', other.page_login, name='login'),
    path('logout/', other.page_logout, name='logout'),

    path('password_recovery/', other.password_recovery, name='password_recovery'),
    path('reset_password/', other.reset_password, name='page_reset_password'),


    path('vk/login/', other.vk_login, name='vk_login'),
    path('vk/register/', other.vk_register, name='vk_register'),

    path('google/auth/', other.google_auth, name='google_auth'),

    path('confirmation_email_address/', other.confirmation_email_address, name='confirmation_email_address'),

    path('dtaf/', other.download_the_application_file, name='download_the_application_file'),

    path('fast_code_execution/', other.fast_code_execution),

    path('api/upform/auth/phone/create_code/', other.api_upform_auth_phone_create_code),
    path('api/upform/auth/phone/check_code/', other.api_upform_auth_phone_check_code),
    path('api/upform/auth/normal/reg/', other.api_upform_auth_normal_reg),
    path('api/upform/auth/normal/login/', other.api_upform_auth_normal_login),
    path('api/upform/auth/forget_password/', other.api_upform_auth_forget_password),
    path('api/upform/auth/forget_password/', other.api_upform_auth_forget_password),
]
