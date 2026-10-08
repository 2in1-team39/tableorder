from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from .models import Table
from orders.models import Order

def table_dashboard(request):
    tables = Table.objects.all().order_by('number')
    return render(request, 'tables/dashboard.html', {'tables': tables})

def table_status_api(request):
    tables = Table.objects.all().order_by('number')
    tables_data = []
    
    for table in tables:
        group = table.get_group()

        # 상태는 사용자가 직접 변경한 값을 그대로 반환한다. 과거 결제 기록이
        # 남아 있더라도 빈 테이블로 바꾼 상태를 결제 완료로 되돌리지 않는다.
        tables_data.append({
            'id': table.id,
            'number': table.number,
            'status': table.status,
            'seats': table.seats,
            'memo': table.memo,
            'layout_x': table.layout_x,
            'layout_y': table.layout_y,
            'layout_width': table.layout_width,
            'layout_height': table.layout_height,
            'layout_shape': table.layout_shape,
            'group_name': group.name if group else None,
            'group_id': group.id if group else None
        })
    
    return JsonResponse(tables_data, safe=False)

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

@csrf_exempt
@require_http_methods(["POST"])
def update_table_memo(request, table_id):
    table = get_object_or_404(Table, id=table_id)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '요청 형식이 올바르지 않습니다.'}, status=400)

    memo = data.get('memo', '')
    if not isinstance(memo, str):
        return JsonResponse({'success': False, 'error': '테이블 메모 형식이 올바르지 않습니다.'}, status=400)

    memo = memo.strip()
    if len(memo) > 500:
        return JsonResponse({'success': False, 'error': '테이블 메모는 500자까지 입력할 수 있습니다.'}, status=400)

    table.memo = memo
    table.save(update_fields=['memo', 'updated_at'])
    return JsonResponse({'success': True, 'memo': table.memo})

@csrf_exempt
@require_http_methods(["POST"])
def update_table_layout(request, table_id):
    """테이블 현황 화면에서 편집한 위치와 모양을 저장한다."""
    table = get_object_or_404(Table, id=table_id)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '요청 형식이 올바르지 않습니다.'}, status=400)

    fields = {
        'layout_x': (0, 100),
        'layout_y': (0, 100),
        'layout_width': (100, 320),
        'layout_height': (80, 240),
    }
    updates = {}
    for field, (minimum, maximum) in fields.items():
        value = data.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            return JsonResponse({'success': False, 'error': '배치 값이 올바르지 않습니다.'}, status=400)
        updates[field] = value

    layout_shape = data.get('layout_shape')
    valid_shapes = dict(Table.TABLE_SHAPE_CHOICES)
    if layout_shape not in valid_shapes:
        return JsonResponse({'success': False, 'error': '테이블 모양이 올바르지 않습니다.'}, status=400)

    for field, value in updates.items():
        setattr(table, field, value)
    table.layout_shape = layout_shape
    table.save(update_fields=[*updates.keys(), 'layout_shape', 'updated_at'])
    return JsonResponse({'success': True, **updates, 'layout_shape': table.layout_shape})

def table_detail(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    orders = Order.objects.filter(table=table).exclude(status='paid').order_by('-created_at')
    from menus.models import Menu
    menus = Menu.objects.filter(is_active=True)
    
    # 총 금액 계산
    total_amount = sum(order.get_final_amount() for order in orders)

    group = table.get_group()
    group_total_amount = None
    if group:
        group_orders = Order.objects.filter(
            table__in=group.tables.all()
        ).exclude(status='paid')
        group_total_amount = sum(order.get_final_amount() for order in group_orders)
    
    return render(request, 'tables/detail.html', {
        'table': table, 
        'orders': orders, 
        'menus': menus,
        'total_amount': total_amount,
        'group': group,
        'group_total_amount': group_total_amount,
    })

@csrf_exempt
@require_http_methods(["POST"])
def process_payment(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    data = json.loads(request.body)
    payment_method = data.get('payment_method')
    discount_id = data.get('discount_id')
    
    # 해당 테이블의 모든 미결제 주문들
    orders = Order.objects.filter(table=table).exclude(status='paid')
    group = table.get_group()
    
    # 할인 적용
    if discount_id:
        from orders.models import Discount
        try:
            discount = Discount.objects.get(id=discount_id, is_active=True)
            for order in orders:
                discount_amount = discount.calculate_discount(order.total_amount)
                order.discount = discount_amount
                order.save()
        except Discount.DoesNotExist:
            pass
    
    total_amount = sum(order.get_final_amount() for order in orders)
    
    for order in orders:
        if group:
            order.group_name = group.name
        order.payment_method = payment_method or ''
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.save(update_fields=['group_name', 'payment_method', 'status', 'paid_at', 'updated_at'])
    
    # 테이블 상태를 '결제 완료'로 변경 (유지)
    table.status = 'paid'
    table.save()
    
    return JsonResponse({
        'success': True,
        'payment_method': payment_method,
        'total_amount': total_amount,
        'message': f'{payment_method} 결제가 완료되었습니다.'
    })

def discounts_api(request):
    """할인 목록 API"""
    try:
        from orders.models import Discount
        
        discounts = Discount.objects.filter(is_active=True)
        discounts_data = []
        
        for discount in discounts:
            discounts_data.append({
                'id': discount.id,
                'name': discount.name,
                'discount_type': discount.discount_type,
                'value': discount.value
            })
        
        return JsonResponse(discounts_data, safe=False)
        
    except Exception as e:
        # 할인 모델이 없거나 오류가 발생하면 빈 리스트 반환
        return JsonResponse([], safe=False)

def payment_methods_api(request):
    """결제 방식 목록 API"""
    try:
        from orders.models import PaymentMethod
        methods = PaymentMethod.objects.filter(is_active=True)
        methods_data = []
        
        for method in methods:
            methods_data.append({
                'id': method.id,
                'name': method.name,
                'code': method.code
            })
        
        return JsonResponse(methods_data, safe=False)
    except:
        # 기본 결제 방식 반환
        return JsonResponse([
            {'id': 1, 'name': '카드', 'code': 'card'},
            {'id': 2, 'name': '현금', 'code': 'cash'}
        ], safe=False)

def groups_api(request):
    """그룹 목록 API"""
    from .models import TableGroup
    
    groups = TableGroup.objects.all().prefetch_related('tables')
    groups_data = []
    
    for group in groups:
        tables_data = [{'id': t.id, 'number': t.number, 'seats': t.seats} for t in group.tables.all()]
        groups_data.append({
            'id': group.id,
            'name': group.name,
            'tables': tables_data,
            'created_at': group.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return JsonResponse(groups_data, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def create_group(request):
    """그룹 생성 API"""
    from .models import TableGroup
    
    try:
        data = json.loads(request.body)
        table_ids = data.get('table_ids', [])
        
        if not table_ids:
            return JsonResponse({'success': False, 'error': '테이블을 선택해주세요.'})
        
        # 자동 그룹명 생성
        existing_groups_count = TableGroup.objects.count()
        group_name = f'단체손님 {existing_groups_count + 1}'
        
        # 그룹 생성
        group = TableGroup.objects.create(name=group_name)
        
        # 테이블 추가
        tables = Table.objects.filter(id__in=table_ids)
        group.tables.set(tables)
        # 그룹 지정 전에 생성된 미결제 주문에도 단체손님 이력을 남긴다.
        Order.objects.filter(table__in=tables).exclude(status='paid').update(group_name=group_name)
        
        return JsonResponse({
            'success': True, 
            'group_id': group.id,
            'group_name': group_name
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def delete_group(request, group_id):
    """그룹 삭제 API"""
    from .models import TableGroup
    
    try:
        group = get_object_or_404(TableGroup, id=group_id)
        group.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def group_orders_api(request, group_id):
    """그룹 주문 조회 API"""
    from .models import TableGroup
    
    try:
        group = get_object_or_404(TableGroup, id=group_id)
        
        # 그룹에 속한 테이블들의 모든 주문 조회 (결제 완료 제외)
        group_tables = group.tables.all()
        orders = Order.objects.filter(
            table__in=group_tables
        ).exclude(status='paid').order_by('table__number', '-created_at')
        
        orders_data = []
        total_amount = 0
        
        for order in orders:
            items_data = []
            for item in order.items.all():
                items_data.append({
                    'menu_name': item.menu.name,
                    'quantity': item.quantity,
                    'options': item.options or [],
                    'total_price': item.get_total_price(),
                    'status': item.status if hasattr(item, 'status') else 'cooking'
                })
            
            order_amount = order.get_final_amount()
            total_amount += order_amount
            
            orders_data.append({
                'id': order.id,
                'table_number': order.table.number,
                'status': order.status,
                'status_display': order.get_status_display(),
                'total_amount': order_amount,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'items': items_data
            })
        
        group_data = {
            'id': group.id,
            'name': group.name,
            'tables': [{'id': t.id, 'number': t.number} for t in group.tables.all()]
        }
        
        return JsonResponse({
            'success': True,
            'group': group_data,
            'orders': orders_data,
            'total_amount': total_amount
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def group_payment(request, group_id):
    """그룹 결제 처리 API"""
    from .models import TableGroup
    
    try:
        group = get_object_or_404(TableGroup, id=group_id)
        data = json.loads(request.body)
        payment_method = data.get('payment_method', '카드')
        discount_id = data.get('discount_id')
        
        # 그룹에 속한 모든 테이블의 미결제 주문들
        group_tables = group.tables.all()
        orders = Order.objects.filter(
            table__in=group_tables
        ).exclude(status='paid')
        
        # 그룹 할인 적용
        if discount_id:
            from orders.models import Discount
            try:
                discount = Discount.objects.get(id=discount_id, is_active=True)
                for order in orders:
                    discount_amount = discount.calculate_discount(order.total_amount)
                    order.discount = discount_amount
                    order.save()
            except Discount.DoesNotExist:
                pass
        
        total_amount = sum(order.get_final_amount() for order in orders)
        
        # 모든 주문을 결제 완료로 변경
        for order in orders:
            order.group_name = group.name
            order.payment_method = payment_method
            order.status = 'paid'
            order.paid_at = timezone.now()
            order.save(update_fields=['group_name', 'payment_method', 'status', 'paid_at', 'updated_at'])
        
        # 모든 테이블 상태를 결제 완료로 변경 (유지)
        for table in group_tables:
            table.status = 'paid'
            table.save()
        
        return JsonResponse({
            'success': True,
            'payment_method': payment_method,
            'total_amount': total_amount,
            'message': f'{payment_method} 그룹 결제가 완료되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
