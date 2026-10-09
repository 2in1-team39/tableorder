from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .models import Table, TableGroup, TableLayoutConfig

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'seats', 'status', 'layout_row', 'layout_column', 'memo', 'created_at']
    list_filter = ['status', 'seats']
    search_fields = ['number']
    ordering = ['number']
    readonly_fields = ['created_at', 'updated_at']
    change_list_template = 'admin/tables/table/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('layout-editor/', self.admin_site.admin_view(self.layout_editor), name='tables_table_layout_editor'),
        ]
        return custom_urls + urls

    def layout_editor(self, request):
        config, _ = TableLayoutConfig.objects.get_or_create()
        tables = list(Table.objects.order_by('number'))

        if request.method == 'POST':
            try:
                rows = int(request.POST.get('rows', config.rows))
                columns = int(request.POST.get('columns', config.columns))
            except (TypeError, ValueError):
                messages.error(request, '행과 열 수는 숫자로 입력해주세요.')
                return redirect(reverse('admin:tables_table_layout_editor'))

            if not 1 <= rows <= 20 or not 1 <= columns <= 12:
                messages.error(request, '행은 1~20, 열은 1~12 사이로 지정해주세요.')
                return redirect(reverse('admin:tables_table_layout_editor'))

            assignments = {}
            selected_table_ids = set()
            for row in range(1, rows + 1):
                for column in range(1, columns + 1):
                    value = request.POST.get(f'cell_{row}_{column}', '')
                    if not value:
                        continue
                    try:
                        table_id = int(value)
                    except ValueError:
                        messages.error(request, '잘못된 테이블 선택입니다.')
                        return redirect(reverse('admin:tables_table_layout_editor'))
                    if table_id in selected_table_ids:
                        messages.error(request, '하나의 테이블은 한 칸에만 배치할 수 있습니다.')
                        return redirect(reverse('admin:tables_table_layout_editor'))
                    selected_table_ids.add(table_id)
                    assignments[table_id] = (row, column)

            valid_table_ids = {table.id for table in tables}
            if not selected_table_ids.issubset(valid_table_ids):
                messages.error(request, '존재하지 않는 테이블이 선택되었습니다.')
                return redirect(reverse('admin:tables_table_layout_editor'))

            config.rows = rows
            config.columns = columns
            config.save(update_fields=['rows', 'columns'])
            Table.objects.update(layout_row=None, layout_column=None)
            for table_id, (row, column) in assignments.items():
                Table.objects.filter(pk=table_id).update(layout_row=row, layout_column=column)

            messages.success(request, '테이블 배치를 저장했습니다.')
            return redirect(reverse('admin:tables_table_layout_editor'))

        table_by_cell = {(table.layout_row, table.layout_column): table.id for table in tables if table.layout_row and table.layout_column}
        grid = [
            [
                {'row': row, 'column': column, 'table_id': table_by_cell.get((row, column))}
                for column in range(1, config.columns + 1)
            ]
            for row in range(1, config.rows + 1)
        ]
        context = {
            **self.admin_site.each_context(request),
            'title': '테이블 배치 편집',
            'config': config,
            'grid': grid,
            'tables': tables,
            'opts': self.model._meta,
        }
        return render(request, 'admin/tables/table/layout_editor.html', context)

@admin.register(TableGroup)
class TableGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    filter_horizontal = ['tables']


@admin.register(TableLayoutConfig)
class TableLayoutConfigAdmin(admin.ModelAdmin):
    list_display = ['rows', 'columns']

    def has_add_permission(self, request):
        return not TableLayoutConfig.objects.exists()
