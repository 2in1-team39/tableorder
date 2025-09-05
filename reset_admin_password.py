import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_system.settings')
django.setup()

from django.contrib.auth.models import User

# admin 사용자의 비밀번호를 'admin123'으로 설정
try:
    admin_user = User.objects.get(username='admin')
    admin_user.set_password('admin123')
    admin_user.save()
    print('관리자 비밀번호가 성공적으로 변경되었습니다.')
    print('사용자명: admin')
    print('비밀번호: admin123')
except User.DoesNotExist:
    print('admin 사용자가 존재하지 않습니다.')