from django.db import models

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
    memo = models.TextField(blank=True, default='', max_length=500, verbose_name='테이블 메모')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        verbose_name = '테이블'
        verbose_name_plural = '테이블'
        ordering = ['number']
    
    def __str__(self):
        return f'테이블 {self.number}번'
    
    def get_group(self):
        """테이블이 속한 그룹 반환"""
        try:
            return self.tablegroup_set.first()
        except:
            return None
    
class TableGroup(models.Model):
    name = models.CharField(max_length=100, verbose_name='그룹명')
    tables = models.ManyToManyField(Table, verbose_name='테이블들')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    
    class Meta:
        verbose_name = '테이블 그룹'
        verbose_name_plural = '테이블 그룹'
    
    def __str__(self):
        return self.name
