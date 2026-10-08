# Generated manually to make the legacy JSON options field optional in admin.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menus', '0002_menu_requires_cooking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menu',
            name='options',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='선택 사항입니다. 예: ["고추빼고", "면 많이"]',
                verbose_name='옵션',
            ),
        ),
    ]
