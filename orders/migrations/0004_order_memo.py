from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_discount_paymentmethod_order_group_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='memo',
            field=models.TextField(blank=True, default='', max_length=500, verbose_name='주문 메모'),
        ),
    ]
