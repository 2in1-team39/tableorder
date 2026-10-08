from django.db import migrations, models


def set_initial_layout(apps, schema_editor):
    Table = apps.get_model('tables', 'Table')
    for index, table in enumerate(Table.objects.order_by('number')):
        table.layout_x = 4 + (index % 4) * 24
        table.layout_y = 4 + (index // 4) * 20
        table.save(update_fields=['layout_x', 'layout_y'])


class Migration(migrations.Migration):

    dependencies = [
        ('tables', '0003_table_memo'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='layout_x',
            field=models.PositiveSmallIntegerField(default=4, verbose_name='배치 가로 위치(%)'),
        ),
        migrations.AddField(
            model_name='table',
            name='layout_y',
            field=models.PositiveSmallIntegerField(default=4, verbose_name='배치 세로 위치(%)'),
        ),
        migrations.AddField(
            model_name='table',
            name='layout_width',
            field=models.PositiveSmallIntegerField(default=180, verbose_name='배치 너비'),
        ),
        migrations.AddField(
            model_name='table',
            name='layout_height',
            field=models.PositiveSmallIntegerField(default=120, verbose_name='배치 높이'),
        ),
        migrations.AddField(
            model_name='table',
            name='layout_shape',
            field=models.CharField(choices=[('rounded', '둥근 사각형'), ('rectangle', '사각형'), ('circle', '원형')], default='rounded', max_length=10, verbose_name='테이블 모양'),
        ),
        migrations.RunPython(set_initial_layout, migrations.RunPython.noop),
    ]
