from django.contrib.auth import views as auth
from django.urls import path
from utils.views import *

urlpatterns = [
    path('utils/add_not_linked_img/', add_not_linked_img, name='utils.add_not_linked_img'),
    path('utils/add_not_linked_doc/', add_not_linked_doc, name='utils.add_not_linked_doc'),

    path('ajax/search/place/', ajax_search_place, name='utils.ajax.search.place'),
    path('ajax/get_missing_images_paths/', ajax_get_missing_images_paths, name='utils.get_missing_images_paths'),

    path('s/<str:short_code>/', shortlink_redirect, name='shortlink_redirect'),
    path('rw/', widget_redirect),
    path('rb/', benner_redirect),
    path('get_stats/', get_stats),

    path('documentation/', documentation_no_slug),
    path('documentation/<slug:slug>/', documentation),


    path('api/notice/get/', notice_get, name='notice_get'),
]
