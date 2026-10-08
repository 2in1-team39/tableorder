# Generated manually to bring the database schema in line with the existing models.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0002_orderitem_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Discount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='할인명')),
                ('discount_type', models.CharField(choices=[('amount', '정액 할인'), ('percent', '정률 할인')], max_length=10, verbose_name='할인 유형')),
                ('value', models.IntegerField(verbose_name='할인값')),
                ('is_active', models.BooleanField(default=True, verbose_name='활성 상태')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
            ],
            options={
                'verbose_name': '할인',
                'verbose_name_plural': '할인',
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='결제 방식명')),
                ('code', models.CharField(max_length=20, unique=True, verbose_name='코드')),
                ('is_active', models.BooleanField(default=True, verbose_name='활성 상태')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
            ],
            options={
                'verbose_name': '결제 방식',
                'verbose_name_plural': '결제 방식',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='order',
            name='group_name',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='단체손님 이력'),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='결제 방법'),
        ),
        migrations.AlterField(
            model_name='order',
            name='table',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='tables.table', verbose_name='테이블'),
        ),
    ]
