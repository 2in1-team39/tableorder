from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='list'),
    path('create/<int:table_id>/', views.create_order, name='create'),
    path('save/<int:table_id>/', views.save_order, name='save'),
    path('detail/<int:order_id>/', views.order_detail, name='detail'),
    path('update/<int:order_id>/', views.update_order_status, name='update_status'),
    path('item/update/<int:item_id>/', views.update_menu_item_status, name='update_menu_status'),
    path('item/cancel/<int:item_id>/', views.cancel_order_item, name='cancel_item'),
    path('api/kitchen-status/', views.kitchen_status_api, name='kitchen_status_api'),
]