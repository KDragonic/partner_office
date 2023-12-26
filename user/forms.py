from django import forms
from .models import User

class UserUpdateForm(forms.Form):
    name = forms.CharField(
        label="Имя", required=True, help_text="", initial="123")
    surname = forms.CharField(
        label="Фамилия", required=True, help_text="")
    patronymic = forms.CharField(
        label="Отчество", required=False, help_text="")
    email = forms.EmailField(
        label="Почта", required=True, help_text="")
    phone = forms.CharField(
        label="Телефон", required=False, help_text="")
    phone2 = forms.CharField(
        label="Телефон (Запосной)", required=False, help_text="")
