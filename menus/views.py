from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Menu

def menu_list(request):
    menus = Menu.objects.filter(is_active=True)
    return render(request, 'menus/list.html', {'menus': menus})


@csrf_exempt
@require_http_methods(['POST'])
def toggle_sold_out(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id, is_active=True)
    menu.is_sold_out = not menu.is_sold_out
    menu.save(update_fields=['is_sold_out', 'updated_at'])
    return JsonResponse({'success': True, 'is_sold_out': menu.is_sold_out})


def orderable_menus_api(request):
    """주문 화면용 메뉴 목록. 품절 메뉴도 표시하되 선택은 막는다."""
    menus = Menu.objects.filter(is_active=True).order_by('name')
    return JsonResponse([
        {
            'id': menu.id,
            'name': menu.name,
            'price': menu.price,
            'description': menu.description,
            'options': menu.options or [],
            'min_order': menu.min_order,
            'is_sold_out': menu.is_sold_out,
        }
        for menu in menus
    ], safe=False)
