from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tables', '0002_remove_table_qr_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='memo',
            field=models.TextField(blank=True, default='', max_length=500, verbose_name='테이블 메모'),
        ),
    ]
