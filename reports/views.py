from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from urllib.parse import quote
from orders.models import Order, OrderItem
from menus.models import Menu


def sales_dashboard(request):
    """매출 대시보드"""
    today = timezone.localdate()
    # 매출은 주문 생성일이 아니라 실제 결제일을 기준으로 집계한다.
    paid_orders = Order.objects.filter(paid_at__date=today, status='paid')
    # 주문 내역은 오늘 생성된 전체 주문과 오늘 결제된 과거 주문을 함께 보여준다.
    today_orders_list = Order.objects.filter(
        Q(created_at__date=today) | Q(paid_at__date=today, status='paid')
    ).distinct()

    # 오늘 매출
    today_sales = paid_orders.aggregate(total=Sum('total_amount'))['total'] or 0

    # 오늘 할인 금액
    today_discount = paid_orders.aggregate(total=Sum('discount'))['total'] or 0
    
    # 오늘 순매출
    today_net_sales = today_sales - today_discount
    
    # 오늘 주문 수
    today_orders = paid_orders.count()

    today_card_sales = (
        paid_orders.filter(payment_method='카드').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
    )
    today_cash_sales = (
        paid_orders.filter(payment_method='현금').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
    )

    sales_orders = today_orders_list.select_related('table').prefetch_related(
        'items__menu'
    ).order_by('created_at', 'id')
    
    context = {
        'today_sales': today_sales,
        'today_discount': today_discount,
        'today_net_sales': today_net_sales,
        'today_orders': today_orders,
        'today_total_orders': today_orders_list.count(),
        'today_card_sales': today_card_sales,
        'today_cash_sales': today_cash_sales,
        'sales_orders': sales_orders,
    }
    
    return render(request, 'reports/dashboard.html', context)

def daily_sales_api(request):
    """일별 매출 API"""
    days = int(request.GET.get('days', 7))
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=days-1)
    
    daily_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        
        orders = Order.objects.filter(
            paid_at__date=date,
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
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=days-1)
    
    from django.db.models import F
    
    menu_sales = OrderItem.objects.filter(
        order__paid_at__date__range=[start_date, end_date],
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
    date_str = request.GET.get('date', timezone.localdate().strftime('%Y-%m-%d'))
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    hourly_data = []
    for hour in range(24):
        orders = Order.objects.filter(
            paid_at__date=target_date,
            paid_at__hour=hour,
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
    today = timezone.localdate()
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
            paid_at__date__gte=month_start,
            paid_at__date__lt=month_end,
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


def order_details_export(request):
    """모든 주문과 각 주문의 메뉴 상세를 한 행씩 CSV로 내보낸다."""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f'주문상세내역_{timezone.localdate().isoformat()}.csv'
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    # Excel에서 한글을 올바르게 인식하도록 UTF-8 BOM을 추가한다.
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        '주문번호', '주문일시', '주문수정일시', '주문상태',
        '테이블번호', '좌석수', '테이블메모', '단체손님', '주문메모',
        '결제방법', '결제일시', '주문금액', '할인금액', '최종금액',
        '상세번호', '메뉴명', '단가', '수량', '상세금액', '선택옵션',
        '조리상태', '상세생성일시',
    ])

    orders = Order.objects.select_related('table').prefetch_related(
        'items__menu'
    ).order_by('-created_at', '-id')
    for order in orders:
        order_values = [
            order.id,
            timezone.localtime(order.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            timezone.localtime(order.updated_at).strftime('%Y-%m-%d %H:%M:%S'),
            order.get_status_display(),
            order.table.number,
            order.table.seats,
            order.table.memo,
            order.group_name,
            order.memo,
            order.payment_method,
            timezone.localtime(order.paid_at).strftime('%Y-%m-%d %H:%M:%S') if order.paid_at else '',
            order.total_amount,
            order.discount,
            order.get_final_amount(),
        ]
        items = list(order.items.all())

        # 주문 상세가 없는 예외적인 주문도 주문 내역 자체는 내보낸다.
        if not items:
            writer.writerow(order_values + [''] * 8)
            continue

        for item in items:
            writer.writerow(order_values + [
                item.id,
                item.menu.name,
                item.unit_price,
                item.quantity,
                item.get_total_price(),
                ', '.join(item.options),
                item.get_status_display(),
                timezone.localtime(item.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            ])
