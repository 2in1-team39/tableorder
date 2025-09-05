from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Table
from orders.models import Order

def table_dashboard(request):
    tables = Table.objects.all().order_by('number')
    return render(request, 'tables/dashboard.html', {'tables': tables})

def table_status_api(request):
    tables = Table.objects.all().values('id', 'number', 'status', 'seats')
    return JsonResponse(list(tables), safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def update_table_status(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    data = json.loads(request.body)
    new_status = data.get('status')
    
    if new_status in dict(Table.STATUS_CHOICES):
        table.status = new_status
        table.save()
        return JsonResponse({'success': True, 'status': table.status})
    
    return JsonResponse({'success': False, 'error': 'Invalid status'})

def table_detail(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    orders = Order.objects.filter(table=table).exclude(status='paid').order_by('-created_at')
    from menus.models import Menu
    menus = Menu.objects.filter(is_active=True)
    
    # 총 금액 계산
    total_amount = sum(order.get_final_amount() for order in orders)
    
    return render(request, 'tables/detail.html', {
        'table': table, 
        'orders': orders, 
        'menus': menus,
        'total_amount': total_amount
    })

def customer_order(request, table_number):
    table = get_object_or_404(Table, number=table_number)
    from menus.models import Menu
    menus = Menu.objects.filter(is_active=True).order_by('name')
    return render(request, 'orders/customer_order.html', {'table': table, 'menus': menus})

@csrf_exempt
@require_http_methods(["POST"])
def submit_order(request, table_number):
    table = get_object_or_404(Table, number=table_number)
    data = json.loads(request.body)
    
    # 새 주문 생성
    order = Order.objects.create(
        table=table,
        status='pending'
    )
    
    total_amount = 0
    from menus.models import Menu
    from orders.models import OrderItem
    
    # 주문 항목들 생성
    for item_data in data.get('items', []):
        menu = Menu.objects.get(id=item_data['menu_id'])
        quantity = int(item_data['quantity'])
        options = item_data.get('options', [])
        
        order_item = OrderItem.objects.create(
            order=order,
            menu=menu,
            quantity=quantity,
            options=options,
            unit_price=menu.price
        )
        total_amount += order_item.get_total_price()
    
    # 주문 총액 업데이트
    order.total_amount = total_amount
    order.save()
    
    # 테이블 상태를 '주문 완료'로 변경
    table.status = 'ordered'
    table.save()
    
    return JsonResponse({
        'success': True, 
        'order_id': order.id,
        'total_amount': total_amount
    })

@csrf_exempt
@require_http_methods(["POST"])
def process_payment(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    data = json.loads(request.body)
    payment_method = data.get('payment_method')
    
    # 해당 테이블의 모든 미결제 주문들을 결제 완료로 변경
    orders = Order.objects.filter(table=table).exclude(status='paid')
    total_amount = sum(order.get_final_amount() for order in orders)
    
    for order in orders:
        order.status = 'paid'
        order.save()
    
    # 테이블 상태를 '결제 완료'로 변경
    table.status = 'paid'
    table.save()
    
    return JsonResponse({
        'success': True,
        'payment_method': payment_method,
        'total_amount': total_amount,
        'message': f'{payment_method} 결제가 완료되었습니다.'
    })

def order_status_api(request, table_number):
    table = get_object_or_404(Table, number=table_number)
    orders = Order.objects.filter(table=table).exclude(status='paid').order_by('-created_at')
    
    orders_data = []
    for order in orders:
        items_data = []
        for item in order.items.all():
            items_data.append({
                'menu_name': item.menu.name,
                'quantity': item.quantity,
                'options': item.options,
                'total_price': item.get_total_price(),
                'status': getattr(item, 'status', 'cooking')
            })
        
        orders_data.append({
            'id': order.id,
            'status': order.status,
            'status_display': order.get_status_display(),
            'total_amount': order.get_final_amount(),
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'items': items_data
        })
    
    return JsonResponse({'orders': orders_data})
