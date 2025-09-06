from django.db import models
from tables.models import Table
from menus.models import Menu

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='결제 방식명')
    code = models.CharField(max_length=20, unique=True, verbose_name='코드')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    
    class Meta:
        verbose_name = '결제 방식'
        verbose_name_plural = '결제 방식'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Discount(models.Model):
    DISCOUNT_TYPES = [
        ('amount', '정액 할인'),
        ('percent', '정률 할인'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='할인명')
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, verbose_name='할인 유형')
    value = models.IntegerField(verbose_name='할인값')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    
    class Meta:
        verbose_name = '할인'
        verbose_name_plural = '할인'
    
    def __str__(self):
        if self.discount_type == 'amount':
            return f'{self.name} ({self.value:,}원 할인)'
        else:
            return f'{self.name} ({self.value}% 할인)'
    
    def calculate_discount(self, amount):
        """할인 금액 계산"""
        if self.discount_type == 'amount':
            return min(self.value, amount)
        else:
            return int(amount * self.value / 100)

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '주문 대기'),
        ('confirmed', '주문 확인'),
        ('cooking', '조리 중'),
        ('ready', '조리 완료'),
        ('served', '서빙 완료'),
        ('paid', '결제 완료'),
    ]
    
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders', verbose_name='테이블')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='상태')
    total_amount = models.IntegerField(default=0, verbose_name='총 금액')
    discount = models.IntegerField(default=0, verbose_name='할인 금액')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='주문일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        verbose_name = '주문'
        verbose_name_plural = '주문'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'테이블 {self.table.number} - {self.get_status_display()}'
    
    def get_final_amount(self):
        return self.total_amount - self.discount

class OrderItem(models.Model):
    STATUS_CHOICES = [
        ('cooking', '조리 중'),
        ('ready', '조리 완료'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='주문')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, verbose_name='메뉴')
    quantity = models.IntegerField(default=1, verbose_name='수량')
    options = models.JSONField(default=list, verbose_name='옵션', help_text='선택된 옵션 목록')
    unit_price = models.IntegerField(verbose_name='단가')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='cooking', verbose_name='조리 상태')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    
    class Meta:
        verbose_name = '주문 상세'
        verbose_name_plural = '주문 상세'
    
    def __str__(self):
        return f'{self.menu.name} x {self.quantity}'
    
    def get_total_price(self):
        return self.unit_price * self.quantity
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.menu.price
        super().save(*args, **kwargs)