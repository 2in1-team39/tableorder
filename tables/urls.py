from django.urls import path
from . import views

app_name = 'tables'

urlpatterns = [
    path('', views.table_dashboard, name='dashboard'),
    path('api/status/', views.table_status_api, name='status_api'),
    path('api/update/<int:table_id>/', views.update_table_status, name='update_status'),
    path('detail/<int:table_id>/', views.table_detail, name='detail'),
    path('payment/<int:table_id>/', views.process_payment, name='process_payment'),
    path('api/groups/', views.groups_api, name='groups_api'),
    path('api/groups/create/', views.create_group, name='create_group'),
    path('api/groups/delete/<int:group_id>/', views.delete_group, name='delete_group'),
    path('api/groups/<int:group_id>/orders/', views.group_orders_api, name='group_orders_api'),
    path('api/groups/<int:group_id>/payment/', views.group_payment, name='group_payment'),
    path('api/discounts/', views.discounts_api, name='discounts_api'),
    path('api/payment-methods/', views.payment_methods_api, name='payment_methods_api'),
]
