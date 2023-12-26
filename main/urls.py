from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='main_home'),
    path('faq/', views.faq, name='main_faq'),

    path('ajax/mailing/add', views.ajax_mailing_add, name='ajax.mailing.add'),


    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),

    path('payment-methods/', views.payment_methods, name='payment_methods'),

    path('contract-offer/', views.contract_offer, name='contract_offer'),


    path('testing_page/', views.testing_page, name='testing_page'),



]