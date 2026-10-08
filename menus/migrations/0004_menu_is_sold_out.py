from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menus', '0003_alter_menu_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='menu',
            name='is_sold_out',
            field=models.BooleanField(default=False, verbose_name='품절'),
        ),
    ]
