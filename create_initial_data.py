import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_system.settings')
django.setup()

from tables.models import Table
from menus.models import Menu
from django.contrib.auth import get_user_model


def create_or_update_admin():
    """Vercel 환경변수로 지정한 관리자 계정을 생성하거나 비밀번호를 갱신한다."""
    username = os.environ.get('DJANGO_ADMIN_USERNAME')
    password = os.environ.get('DJANGO_ADMIN_PASSWORD')

    if not username or not password:
        print('관리자 계정 환경변수가 없어 생성을 건너뜁니다.')
        return

    user_model = get_user_model()
    user, created = user_model.objects.get_or_create(username=username)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password(password)
    user.save()
    action = '생성' if created else '비밀번호 갱신'
    print(f'관리자 계정 {action} 완료: {username}')

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

create_or_update_admin()
print('초기 데이터 생성 완료!')
