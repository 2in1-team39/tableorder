from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import models
import json
from .models import Order, OrderItem
from tables.models import Table
from menus.models import Menu

def order_list(request):
    from django.utils import timezone
    
    # 주문 대기, 주문 확인 단계를 자동으로 조리중으로 변경
    Order.objects.filter(status__in=['pending', 'confirmed']).update(status='cooking')
    
    status_filter = request.GET.get('status', 'all')
    today = timezone.now().date()
    
    if status_filter == 'cooking':
        orders = Order.objects.filter(status='cooking')
    elif status_filter == 'ready':
        orders = Order.objects.filter(status='ready')
    elif status_filter == 'completed':
        # 모든 주문을 paid로 변경 (테스트용)
        Order.objects.filter(status__in=['cooking', 'ready']).update(status='paid')
        orders = Order.objects.filter(status='paid', created_at__date=today)
    else:
        # 전체: 조리중 + 완료 + 오늘 결제완룼
        orders = Order.objects.filter(
            models.Q(status__in=['cooking', 'ready']) |
            models.Q(status='paid', created_at__date=today)
        )
    
    orders = orders.order_by('created_at')
    
    # 카운트 계산
    cooking_count = Order.objects.filter(status='cooking').count()
    ready_count = Order.objects.filter(status='ready').count()
    completed_count = Order.objects.filter(status='paid', created_at__date=today).count()
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'cooking_count': cooking_count,
        'ready_count': ready_count,
        'completed_count': completed_count,
        'total_count': cooking_count + ready_count + completed_count
    }
    
    return render(request, 'orders/list.html', context)

def create_order(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    menus = Menu.objects.filter(is_active=True)
    return render(request, 'orders/create.html', {'table': table, 'menus': menus})

@csrf_exempt
@require_http_methods(["POST"])
def save_order(request, table_id):
    try:
        table = get_object_or_404(Table, id=table_id)
        data = json.loads(request.body)
        
        items = data.get('items', [])
        if not items:
            return JsonResponse({'success': False, 'error': '주문 항목이 없습니다.'})
        
        order = Order.objects.create(
            table=table,
            status='pending'
        )
        
        total_amount = 0
        for item_data in items:
            try:
                menu_id = item_data.get('menu_id')
                quantity = int(item_data.get('quantity', 0))
                options = item_data.get('options', [])
                
                if not menu_id or quantity <= 0:
                    continue
                
                menu = Menu.objects.get(id=menu_id)
                
                order_item = OrderItem.objects.create(
                    order=order,
                    menu=menu,
                    quantity=quantity,
                    options=options if options else [],
                    unit_price=menu.price
                )
                total_amount += order_item.get_total_price()
                
            except (Menu.DoesNotExist, ValueError, KeyError):
                continue
        
        if total_amount == 0:
            order.delete()
            return JsonResponse({'success': False, 'error': '유효한 주문 항목이 없습니다.'})
        
        order.total_amount = total_amount
        order.save()
        
        table.status = 'ordered'
        table.save()
        
        return JsonResponse({'success': True, 'order_id': order.id})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

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
        
        # 주문의 모든 조리 필요 메뉴가 완료되었는지 확인
        if status == 'ready':
            cooking_items = order_item.order.items.filter(menu__requires_cooking=True)
            all_ready = all(item.status == 'ready' for item in cooking_items)
            if all_ready:
                order_item.order.status = 'ready'
                order_item.order.table.status = 'cooking'
                order_item.order.table.save()
                order_item.order.save()
        
        return JsonResponse({'success': True, 'status': status})
    
    return JsonResponse({'success': False, 'error': 'Invalid status'})

@csrf_exempt
@require_http_methods(["POST"])
def cancel_order_item(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id)
    
    # 이미 조리 완료된 메뉴는 취소할 수 없음
    if order_item.status == 'ready':
        return JsonResponse({'success': False, 'error': 'Cannot cancel ready item'})
    
    order = order_item.order
    
    # 주문 항목 삭제
    order_item.delete()
    
    # 주문의 총 금액 재계산
    remaining_items = order.items.all()
    if remaining_items.exists():
        total_amount = sum(item.get_total_price() for item in remaining_items)
        order.total_amount = total_amount
        order.save()
    else:
        # 모든 항목이 취소되면 주문 자체를 삭제
        table = order.table
        order.delete()
        
        # 테이블에 다른 주문이 없으면 상태를 빈 테이블로 변경
        # 단, 결제완료된 주문이 있으면 paid 상태 유지
        remaining_orders = table.orders.exclude(status='paid')
        if not remaining_orders.exists():
            paid_orders = table.orders.filter(status='paid')
            if paid_orders.exists():
                table.status = 'paid'
            else:
                table.status = 'empty'
            table.save()
    
    return JsonResponse({'success': True})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/detail.html', {'order': order})

def kitchen_status_api(request):
    """주방용 실시간 상태 API"""
    # 조리가 필요한 메뉴가 있는 주문만 조회
    orders = Order.objects.filter(
        status__in=['cooking', 'ready'],
        items__menu__requires_cooking=True
    ).distinct().order_by('created_at')
    
    orders_data = []
    for order in orders:
        cooking_items = []
        for item in order.items.filter(menu__requires_cooking=True):
            cooking_items.append({
                'id': item.id,
                'menu_name': item.menu.name,
                'quantity': item.quantity,
                'options': item.options,
                'status': item.status
            })
        
        orders_data.append({
            'id': order.id,
            'table_number': order.table.number,
            'status': order.status,
            'created_at': order.created_at.strftime('%H:%M'),
            'items': cooking_items
        })
    
    # 상태별 카운트
    cooking_count = Order.objects.filter(
        status='cooking',
        items__menu__requires_cooking=True
    ).distinct().count()
    
    ready_count = Order.objects.filter(
        status='ready',
        items__menu__requires_cooking=True
    ).distinct().count()
    
    return JsonResponse({
        'orders': orders_data,
        'cooking_count': cooking_count,
        'ready_count': ready_count,
        'total_count': cooking_count + ready_count
    })
