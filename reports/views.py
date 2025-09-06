from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from orders.models import Order, OrderItem
from menus.models import Menu

def sales_dashboard(request):
    """매출 대시보드"""
    today = timezone.now().date()
    
    # 오늘 매출
    today_sales = Order.objects.filter(
        created_at__date=today,
        status='paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # 오늘 할인 금액
    today_discount = Order.objects.filter(
        created_at__date=today,
        status='paid'
    ).aggregate(total=Sum('discount'))['total'] or 0
    
    # 오늘 순매출
    today_net_sales = today_sales - today_discount
    
    # 오늘 주문 수
    today_orders = Order.objects.filter(
        created_at__date=today,
        status='paid'
    ).count()
    
    # 결제 방법별 매출 (추후 구현)
    today_card_sales = 0
    today_cash_sales = 0
    
    context = {
        'today_sales': today_sales,
        'today_discount': today_discount,
        'today_net_sales': today_net_sales,
        'today_orders': today_orders,
        'today_card_sales': today_card_sales,
        'today_cash_sales': today_cash_sales,
    }
    
    return render(request, 'reports/dashboard.html', context)

def daily_sales_api(request):
    """일별 매출 API"""
    days = int(request.GET.get('days', 7))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    daily_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        
        orders = Order.objects.filter(
            created_at__date=date,
            status='paid'
        )
        
        total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        total_discount = orders.aggregate(total=Sum('discount'))['total'] or 0
        net_sales = total_sales - total_discount
        order_count = orders.count()
        
        # 결제 방법별 매출 (추후 구현)
        card_sales = 0
        cash_sales = 0
        
        daily_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'date_display': date.strftime('%m/%d'),
            'total_sales': total_sales,
            'total_discount': total_discount,
            'net_sales': net_sales,
            'order_count': order_count,
            'card_sales': card_sales,
            'cash_sales': cash_sales
        })
    
    return JsonResponse(daily_data, safe=False)

def menu_sales_api(request):
    """메뉴별 판매 현황 API"""
    days = int(request.GET.get('days', 7))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    from django.db.models import F
    
    menu_sales = OrderItem.objects.filter(
        order__created_at__date__range=[start_date, end_date],
        order__status='paid'
    ).values(
        'menu__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_amount=Sum(F('unit_price') * F('quantity'))
    ).order_by('-total_quantity')[:10]
    
    return JsonResponse(list(menu_sales), safe=False)

def hourly_sales_api(request):
    """시간대별 매출 분석 API"""
    date_str = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    hourly_data = []
    for hour in range(24):
        orders = Order.objects.filter(
            created_at__date=target_date,
            created_at__hour=hour,
            status='paid'
        )
        
        total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        order_count = orders.count()
        
        hourly_data.append({
            'hour': f'{hour:02d}:00',
            'sales': total_sales,
            'orders': order_count
        })
    
    return JsonResponse(hourly_data, safe=False)

def monthly_sales_api(request):
    """월별 매출 조회 API"""
    months = int(request.GET.get('months', 6))
    today = timezone.now().date()
    current_year = today.year
    current_month = today.month
    
    monthly_data = []
    for i in range(months):
        # 월 계산
        target_month = current_month - i
        target_year = current_year
        
        if target_month <= 0:
            target_month += 12
            target_year -= 1
        
        # 월 시작일과 마지막일
        month_start = datetime(target_year, target_month, 1).date()
        if target_month == 12:
            month_end = datetime(target_year + 1, 1, 1).date()
        else:
            month_end = datetime(target_year, target_month + 1, 1).date()
        
        orders = Order.objects.filter(
            created_at__date__gte=month_start,
            created_at__date__lt=month_end,
            status='paid'
        )
        
        total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        total_discount = orders.aggregate(total=Sum('discount'))['total'] or 0
        net_sales = total_sales - total_discount
        order_count = orders.count()
        
        monthly_data.insert(0, {
            'month': month_start.strftime('%Y-%m'),
            'month_display': month_start.strftime('%Y년 %m월'),
            'total_sales': total_sales,
            'total_discount': total_discount,
            'net_sales': net_sales,
            'order_count': order_count
        })
    
    return JsonResponse(monthly_data, safe=False)