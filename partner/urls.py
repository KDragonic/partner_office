from django.urls import path
import partner.views.base as base
import partner.views.external_api as external_api



urlpatterns = [
    path('', base.index, name='partner.index'),
    path('get_page/', base.get_page, name='partner.get_page'),
    path('api/form/', base.send_form_post, name='partner.send_form_post'),
    path('api/get/', base.api_get, name='partner.send_form_post'),


    # Другой API
    path('api/widget_get_code/', base.widget_get_code, name='partner.api.widget_get_code'),

]