from django.db import models

class Menu(models.Model):
    name = models.CharField(max_length=100, verbose_name='메뉴명')
    price = models.IntegerField(verbose_name='가격')
    description = models.TextField(blank=True, verbose_name='설명')
    options = models.JSONField(default=list, verbose_name='옵션', help_text='예: ["고추빼고", "면 많이"]')
    min_order = models.IntegerField(default=1, verbose_name='최소 주문 수량')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    requires_cooking = models.BooleanField(default=True, verbose_name='주방 조리 필요')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        verbose_name = '메뉴'
        verbose_name_plural = '메뉴'
        ordering = ['name']
    
    def __str__(self):
        return f'{self.name} ({self.price:,}원)'

class MenuOption(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='menu_options', verbose_name='메뉴')
    name = models.CharField(max_length=50, verbose_name='옵션명')
    price = models.IntegerField(default=0, verbose_name='추가 가격')
    
    class Meta:
        verbose_name = '메뉴 옵션'
        verbose_name_plural = '메뉴 옵션'
    
    def __str__(self):
        return f'{self.menu.name} - {self.name}'
