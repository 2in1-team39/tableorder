from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import json
from .models import Order, OrderItem
from tables.models import Table
from menus.models import Menu

def order_list(request):
    # 주문 대기, 주문 확인 단계를 자동으로 조리중으로 변경
    Order.objects.filter(status__in=['pending', 'confirmed']).update(status='cooking')
    
    # 조리가 필요한 메뉴가 있는 주문만 표시
    orders = Order.objects.filter(
        status__in=['cooking', 'ready'],
        items__menu__requires_cooking=True
    ).distinct().order_by('created_at')
    
    return render(request, 'orders/list.html', {'orders': orders})

def create_order(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    menus = Menu.objects.filter(is_active=True)
    return render(request, 'orders/create.html', {'table': table, 'menus': menus})

@csrf_exempt
@require_http_methods(["POST"])
def save_order(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    data = json.loads(request.body)
    
    order = Order.objects.create(
        table=table,
        status='pending'
    )
    
    total_amount = 0
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
    
    order.total_amount = total_amount
    order.save()
    
    table.status = 'ordered'
    table.save()
    
    return JsonResponse({'success': True, 'order_id': order.id})

@csrf_exempt
@require_http_methods(["POST"])
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    data = json.loads(request.body)
    new_status = data.get('status')
    
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save()
        
        # 테이블 상태도 함께 업데이트
        if new_status == 'ready':
            order.table.status = 'cooking'
        elif new_status == 'paid':
            order.table.status = 'paid'
        order.table.save()
        
        return JsonResponse({'success': True, 'status': order.status})
    
    return JsonResponse({'success': False, 'error': 'Invalid status'})

@csrf_exempt
@require_http_methods(["POST"])
def update_menu_item_status(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id)
    data = json.loads(request.body)
    status = data.get('status')
    
    if status in ['cooking', 'ready']:
        order_item.status = status
        order_item.save()
        
        # 주문의 모든 메뉴가 완료되었는지 확인
        if status == 'ready':
            all_ready = all(item.status == 'ready' for item in order_item.order.items.all())
            if all_ready:
                order_item.order.status = 'ready'
                order_item.order.table.status = 'cooking'
                order_item.order.table.save()
                order_item.order.save()
        
        return JsonResponse({'success': True, 'status': status})
    
    return JsonResponse({'success': False, 'error': 'Invalid status'})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/detail.html', {'order': order})
