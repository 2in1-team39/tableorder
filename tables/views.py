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
    from .models import TableGroup
    from orders.models import Order
    from django.utils import timezone
    
    tables = Table.objects.all().order_by('number')
    tables_data = []
    today = timezone.now().date()
    
    for table in tables:
        group = table.get_group()
        
        # 결제 완료된 주문이 있는지 확인
        has_paid_orders = table.orders.filter(
            status='paid',
            created_at__date=today
        ).exists()
        
        # 결제 완료된 주문이 있으면 paid 상태 유지
        if has_paid_orders and table.status != 'paid':
            table.status = 'paid'
            table.save()
        
        tables_data.append({
            'id': table.id,
            'number': table.number,
            'status': table.status,
            'seats': table.seats,
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
    try:
        table = get_object_or_404(Table, number=table_number)
        data = json.loads(request.body)
        
        items = data.get('items', [])
        if not items:
            return JsonResponse({'success': False, 'error': '주문 항목이 없습니다.'})
        
        # 새 주문 생성
        order = Order.objects.create(
            table=table,
            status='pending'
        )
        
        total_amount = 0
        from menus.models import Menu
        from orders.models import OrderItem
        
        # 주문 항목들 생성
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
                
            except (Menu.DoesNotExist, ValueError, KeyError) as e:
                continue
        
        if total_amount == 0:
            order.delete()
            return JsonResponse({'success': False, 'error': '유효한 주문 항목이 없습니다.'})
        
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
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def process_payment(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    data = json.loads(request.body)
    payment_method = data.get('payment_method')
    discount_id = data.get('discount_id')
    
    # 해당 테이블의 모든 미결제 주문들
    orders = Order.objects.filter(table=table).exclude(status='paid')
    
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
        order.status = 'paid'
        order.save()
    
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

@csrf_exempt
@require_http_methods(["POST"])
def generate_qr_code(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    
    try:
        table.generate_qr_code()
        table.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

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
            order.status = 'paid'
            order.save()
        
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
