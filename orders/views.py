from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import models
from django.db import transaction
from django.utils import timezone
import json
from .models import Order, OrderItem
from tables.models import Table
from menus.models import Menu


def update_table_kitchen_status(table):
    """테이블의 모든 미결제 조리 메뉴 상태로 테이블 표시 상태를 계산한다."""
    cooking_items = OrderItem.objects.filter(
        order__table=table,
        menu__requires_cooking=True,
    ).exclude(order__status='paid')

    # 하나라도 조리 중인 메뉴가 있으면 테이블은 주문 완료 상태다.
    # 조리 대상 메뉴가 모두 완료됐을 때에만 조리 완료 상태로 표시한다.
    if cooking_items.exists() and not cooking_items.exclude(status='ready').exists():
        new_status = 'cooking'
    else:
        new_status = 'ordered'

    if table.status != new_status:
        table.status = new_status
        table.save(update_fields=['status'])


def order_list(request):
    from django.utils import timezone

    # 주방은 처리할 주문을 먼저 보여 준다. 전체 이력은 탭에서 확인한다.
    status_filter = request.GET.get('status', 'cooking')
    if status_filter not in {'all', 'cooking', 'ready', 'completed'}:
        status_filter = 'all'
    today = timezone.localdate()

    # 주방 화면에는 실제 조리가 필요한 메뉴가 포함된 주문만 표시한다.
    kitchen_orders = Order.objects.filter(
        items__menu__requires_cooking=True
    ).distinct()

    active_cooking_statuses = ['pending', 'confirmed', 'cooking']
    if status_filter == 'cooking':
        orders = kitchen_orders.filter(status__in=active_cooking_statuses)
    elif status_filter == 'ready':
        orders = kitchen_orders.filter(status='ready')
    elif status_filter == 'completed':
        # 조회는 상태를 변경하지 않는다. 결제 처리는 테이블 결제 기능만 담당한다.
        orders = kitchen_orders.filter(status='paid', updated_at__date=today)
    else:
        # 전체: 조리중 + 완료 + 오늘 결제완료
        orders = kitchen_orders.filter(
            models.Q(status__in=active_cooking_statuses + ['ready']) |
            models.Q(status='paid', updated_at__date=today)
        )
    
    orders = orders.order_by('created_at')
    
    # 카운트 계산
    cooking_count = kitchen_orders.filter(status__in=active_cooking_statuses).count()
    ready_count = kitchen_orders.filter(status='ready').count()
    completed_count = kitchen_orders.filter(status='paid', updated_at__date=today).count()
    
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

        group = table.get_group()
        order = Order.objects.create(
            table=table,
            # 주방에 표시될 새 주문은 생성 즉시 조리중 상태로 시작한다.
            status='cooking',
            group_name=group.name if group else '',
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
                if not menu.is_active:
                    order.delete()
                    return JsonResponse({'success': False, 'error': f'{menu.name} 메뉴는 현재 주문할 수 없습니다.'})
                if menu.is_sold_out:
                    order.delete()
                    return JsonResponse({'success': False, 'error': f'{menu.name} 메뉴는 품절되었습니다.'})
                
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
        if new_status == 'paid' and order.paid_at is None:
            order.paid_at = timezone.now()
            order.save(update_fields=['status', 'paid_at', 'updated_at'])
        else:
            order.save()
        
        # 테이블 상태도 함께 업데이트
        if new_status in ['cooking', 'ready']:
            update_table_kitchen_status(order.table)
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
        if order_item.order.status == 'paid':
            return JsonResponse({'success': False, 'error': 'Paid order items cannot be changed'}, status=400)

        with transaction.atomic():
            order_item.status = status
            order_item.save(update_fields=['status'])

            # 메뉴를 완료/미완료로 바꿀 때마다 주문 상태를 다시 계산한다.
            # 따라서 완료된 주문에서 메뉴를 되돌려도 주문이 완료로 남지 않는다.
            cooking_items = order_item.order.items.filter(menu__requires_cooking=True)
            all_ready = cooking_items.exists() and not cooking_items.exclude(status='ready').exists()
            order_item.order.status = 'ready' if all_ready else 'cooking'
            order_item.order.save(update_fields=['status', 'updated_at'])

            update_table_kitchen_status(order_item.order.table)
        
        return JsonResponse({
            'success': True,
            'status': status,
            'order_status': order_item.order.status,
        })
    
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
        cooking_items = remaining_items.filter(menu__requires_cooking=True)
        all_ready = cooking_items.exists() and not cooking_items.exclude(status='ready').exists()
        order.status = 'ready' if all_ready else 'cooking'
        order.save(update_fields=['total_amount', 'status', 'updated_at'])
        update_table_kitchen_status(order.table)
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


@csrf_exempt
@require_http_methods(["POST"])
def delete_order(request, order_id):
    """미결제 주문 전체를 삭제한다."""
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'paid':
        return JsonResponse(
            {'success': False, 'error': '결제 완료 주문은 삭제할 수 없습니다.'},
            status=400,
        )

    table = order.table
    order.delete()

    remaining_orders = table.orders.exclude(status='paid')
    if remaining_orders.exists():
        update_table_kitchen_status(table)
    else:
        table.status = 'paid' if table.orders.filter(status='paid').exists() else 'empty'
        table.save(update_fields=['status'])

    return JsonResponse({'success': True})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/detail.html', {'order': order})

def kitchen_status_api(request):
    """주방용 실시간 상태 API"""
    # 조리가 필요한 메뉴가 있는 주문만 조회
    kitchen_orders = Order.objects.filter(
        items__menu__requires_cooking=True
    ).distinct()
    active_cooking_statuses = ['pending', 'confirmed', 'cooking']
    orders = kitchen_orders.filter(status__in=active_cooking_statuses + ['ready']).order_by('created_at')
    
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
    from django.utils import timezone
    today = timezone.localdate()
    cooking_count = kitchen_orders.filter(status__in=active_cooking_statuses).count()
    ready_count = kitchen_orders.filter(status='ready').count()
    completed_count = kitchen_orders.filter(status='paid', updated_at__date=today).count()
    
    return JsonResponse({
        'orders': orders_data,
        'cooking_count': cooking_count,
        'ready_count': ready_count,
        'completed_count': completed_count,
        'total_count': cooking_count + ready_count + completed_count,
    })
