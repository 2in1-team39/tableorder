import os
import django
import qrcode
from PIL import Image, ImageDraw, ImageFont

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_system.settings')
django.setup()

from tables.models import Table

def generate_qr_codes():
    # QR코드 저장 디렉토리 생성
    qr_dir = 'qr_codes'
    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)
    
    tables = Table.objects.all()
    
    for table in tables:
        # QR코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # 고객 주문 페이지 URL
        order_url = f'http://localhost:8000/order/table/{table.number}/'
        qr.add_data(order_url)
        qr.make(fit=True)
        
        # QR코드 이미지 생성 및 저장
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # 파일 저장
        filename = f'{qr_dir}/table_{table.number}_qr.png'
        qr_img.save(filename, 'PNG')
        print(f'테이블 {table.number}번 QR코드 생성: {filename}')
    
    print(f'\n총 {len(tables)}개 테이블의 QR코드가 생성되었습니다.')
    print(f'QR코드 파일들은 {qr_dir} 폴더에 저장되었습니다.')

if __name__ == '__main__':
    generate_qr_codes()