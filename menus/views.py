from django.shortcuts import render
from .models import Menu

def menu_list(request):
    menus = Menu.objects.filter(is_active=True)
    return render(request, 'menus/list.html', {'menus': menus})
