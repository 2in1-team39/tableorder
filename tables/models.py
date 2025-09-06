from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class Table(models.Model):
    STATUS_CHOICES = [
        ('empty', '빈 테이블'),
        ('ordered', '주문 완료'),
        ('cooking', '조리 완료'),
        ('paid', '결제 완료'),
    ]
    
    number = models.IntegerField(unique=True, verbose_name='테이블 번호')
    seats = models.IntegerField(default=4, verbose_name='좌석 수')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='empty', verbose_name='상태')
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, verbose_name='QR코드')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        verbose_name = '테이블'
        verbose_name_plural = '테이블'
        ordering = ['number']
    
    def __str__(self):
        return f'테이블 {self.number}번'
    
    def generate_qr_code(self):
        """테이블용 QR코드 생성"""
        from django.conf import settings
        
        # QR코드에 포함될 URL (고객 주문 페이지)
        qr_url = f"http://localhost:8000/order/{self.number}/"
        
        # QR코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # 이미지 생성
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # BytesIO로 저장
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # 파일로 저장
        filename = f'table_{self.number}_qr.png'
        self.qr_code.save(filename, File(buffer), save=False)
        buffer.close()
    
    def get_group(self):
        """테이블이 속한 그룹 반환"""
        try:
            return self.tablegroup_set.first()
        except:
            return None
    
    def save(self, *args, **kwargs):
        # 처음 생성시 QR코드 자동 생성
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new or not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])

class TableGroup(models.Model):
    name = models.CharField(max_length=100, verbose_name='그룹명')
    tables = models.ManyToManyField(Table, verbose_name='테이블들')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    
    class Meta:
        verbose_name = '테이블 그룹'
        verbose_name_plural = '테이블 그룹'
    
    def __str__(self):
        return self.name
