from django.urls import include, path

urlpatterns = [
    path('ajax/', include('user.urls_views.ajax')), #Все ajax
    path('profile/', include('user.urls_views.profile')),
    path('admin/', include('user.urls_views.admin')),
    path('', include('user.urls_views.other')), #Остальные

]
