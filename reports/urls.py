from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.sales_dashboard, name='dashboard'),
    path('api/today-order-count/', views.today_order_count_api, name='today_order_count_api'),
    path('api/daily-sales/', views.daily_sales_api, name='daily_sales_api'),
    path('api/menu-sales/', views.menu_sales_api, name='menu_sales_api'),
    path('api/hourly-sales/', views.hourly_sales_api, name='hourly_sales_api'),
    path('api/monthly-sales/', views.monthly_sales_api, name='monthly_sales_api'),
]
