from django.urls import path
from . import views

app_name = 'menus'

urlpatterns = [
    path('', views.menu_list, name='list'),
    path('api/orderable/', views.orderable_menus_api, name='orderable_menus_api'),
    path('<int:menu_id>/toggle-sold-out/', views.toggle_sold_out, name='toggle_sold_out'),
]
