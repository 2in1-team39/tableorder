from django.db import migrations, models
from django.db.models import Q


def create_grid_layout(apps, schema_editor):
    Table = apps.get_model('tables', 'Table')
    TableLayoutConfig = apps.get_model('tables', 'TableLayoutConfig')
    table_count = Table.objects.count()
    columns = 4
    rows = max(1, (table_count + columns - 1) // columns)
    TableLayoutConfig.objects.get_or_create(pk=1, defaults={'rows': rows, 'columns': columns})
    for index, table in enumerate(Table.objects.order_by('number')):
        table.layout_row = index // columns + 1
        table.layout_column = index % columns + 1
        table.save(update_fields=['layout_row', 'layout_column'])


class Migration(migrations.Migration):

    dependencies = [
        ('tables', '0004_table_layout'),
    ]

    operations = [
        migrations.CreateModel(
            name='TableLayoutConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rows', models.PositiveSmallIntegerField(default=5, verbose_name='행 수')),
                ('columns', models.PositiveSmallIntegerField(default=4, verbose_name='열 수')),
            ],
            options={
                'verbose_name': '테이블 배치 설정',
                'verbose_name_plural': '테이블 배치 설정',
            },
        ),
        migrations.AddField(
            model_name='table',
            name='layout_column',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='배치 열'),
        ),
        migrations.AddField(
            model_name='table',
            name='layout_row',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='배치 행'),
        ),
        migrations.RunPython(create_grid_layout, migrations.RunPython.noop),
        migrations.RemoveField(model_name='table', name='layout_height'),
        migrations.RemoveField(model_name='table', name='layout_shape'),
        migrations.RemoveField(model_name='table', name='layout_width'),
        migrations.RemoveField(model_name='table', name='layout_x'),
        migrations.RemoveField(model_name='table', name='layout_y'),
        migrations.AddConstraint(
            model_name='table',
            constraint=models.UniqueConstraint(
                condition=Q(layout_column__isnull=False, layout_row__isnull=False),
                fields=('layout_row', 'layout_column'),
                name='unique_table_layout_cell',
            ),
        ),
    ]
