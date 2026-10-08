from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('menus', '0004_menu_is_sold_out'),
    ]

    operations = [
        migrations.AddField(
            model_name='menu',
            name='sort_order',
            field=models.PositiveIntegerField(default=0, verbose_name='표시 순서'),
        ),
        migrations.AlterModelOptions(
            name='menu',
            options={
                'ordering': ['sort_order', 'name'],
                'verbose_name': '메뉴',
                'verbose_name_plural': '메뉴',
            },
        ),
    ]
