from django.urls import path
from . import views

app_name = 'tables'

urlpatterns = [
    path('', views.table_dashboard, name='dashboard'),
    path('api/status/', views.table_status_api, name='status_api'),
    path('api/update/<int:table_id>/', views.update_table_status, name='update_status'),
    path('detail/<int:table_id>/', views.table_detail, name='detail'),
    path('order/table/<int:table_number>/', views.customer_order, name='customer_order'),
    path('order/submit/<int:table_number>/', views.submit_order, name='submit_order'),
    path('order/status/<int:table_number>/', views.order_status_api, name='order_status_api'),
    path('payment/<int:table_id>/', views.process_payment, name='process_payment'),
]