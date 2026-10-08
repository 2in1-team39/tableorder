from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('tables', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='table',
            name='qr_code',
        ),
    ]
