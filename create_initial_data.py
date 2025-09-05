import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_system.settings')
django.setup()

from tables.models import Table
from menus.models import Menu

# 테이블 생성 (1~20번)
for i in range(1, 21):
    table, created = Table.objects.get_or_create(
        number=i,
        defaults={'seats': 4 if i <= 15 else 6}
    )
    if created:
        print(f'테이블 {i}번 생성됨')

# 메뉴 생성
menus_data = [
    {
        'name': '해물칼국수',
        'price': 10000,
        'description': '신선한 해물이 들어간 칼국수',
        'options': ['고추빼고', '면 많이'],
        'min_order': 1
    },
    {
        'name': '비빔칼국수',
        'price': 8000,
        'description': '매콤달콤한 비빔칼국수',
        'options': [],
        'min_order': 2
    },
    {
        'name': '공기밥',
        'price': 1000,
        'description': '갓 지은 따뜻한 밥',
        'options': [],
        'min_order': 1
    },
    {
        'name': '도토리묵',
        'price': 8000,
        'description': '쫄깃한 도토리묵',
        'options': [],
        'min_order': 1
    },
    {
        'name': '편육',
        'price': 12000,
        'description': '부드러운 수육',
        'options': [],
        'min_order': 1
    }
]

for menu_data in menus_data:
    menu, created = Menu.objects.get_or_create(
        name=menu_data['name'],
        defaults=menu_data
    )
    if created:
        print(f'메뉴 {menu_data["name"]} 생성됨')

print('초기 데이터 생성 완료!')