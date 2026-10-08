from django.db import migrations, models
from django.db.models import F


def set_paid_at_for_existing_orders(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    Order.objects.filter(status='paid', paid_at__isnull=True).update(paid_at=F('updated_at'))


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0004_order_memo'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='결제일시'),
        ),
        migrations.RunPython(set_paid_at_for_existing_orders, migrations.RunPython.noop),
    ]
