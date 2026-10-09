from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from orders.models import Order
from .models import Table, TableGroup, TableLayoutConfig


class TableStatusApiTests(TestCase):
    def test_marking_table_paid_records_unpaid_orders_as_card_payments(self):
        table = Table.objects.create(number=1, status='ordered')
        order = Order.objects.create(table=table, status='cooking', total_amount=12000)

        response = self.client.post(
            reverse('tables:update_status', args=[table.id]),
            data=json.dumps({'status': 'paid'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        order.refresh_from_db()
        table.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        self.assertEqual(order.payment_method, '카드')
        self.assertIsNotNone(order.paid_at)
        self.assertEqual(table.status, 'paid')

    def test_admin_layout_editor_saves_grid_assignments(self):
        first_table = Table.objects.create(number=1)
        second_table = Table.objects.create(number=2)
        admin_user = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client.force_login(admin_user)

        response = self.client.post(
            reverse('admin:tables_table_layout_editor'),
            {'rows': 2, 'columns': 2, 'cell_1_1': second_table.id, 'cell_2_2': first_table.id},
        )

        self.assertEqual(response.status_code, 302)
        first_table.refresh_from_db()
        second_table.refresh_from_db()
        self.assertEqual((first_table.layout_row, first_table.layout_column), (2, 2))
        self.assertEqual((second_table.layout_row, second_table.layout_column), (1, 1))
        config = TableLayoutConfig.objects.get()
        self.assertEqual((config.rows, config.columns), (2, 2))

    def test_table_memo_can_be_saved_separately_from_orders(self):
        table = Table.objects.create(number=1)

        response = self.client.post(
            reverse('tables:update_memo', args=[table.id]),
            data=json.dumps({'memo': '창가 자리, 알레르기 안내 확인'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        table.refresh_from_db()
        self.assertEqual(table.memo, '창가 자리, 알레르기 안내 확인')

    def test_paid_order_does_not_override_an_empty_table_status(self):
        table = Table.objects.create(number=1)
        Order.objects.create(table=table, status='paid', total_amount=10000)
        table.status = 'empty'
        table.save()

        response = self.client.get(reverse('tables:status_api'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['status'], 'empty')
        table.refresh_from_db()
        self.assertEqual(table.status, 'empty')

    def test_group_payment_keeps_group_and_payment_history_after_group_delete(self):
        table = Table.objects.create(number=1)
        group = TableGroup.objects.create(name='단체손님 1')
        group.tables.add(table)
        order = Order.objects.create(table=table, status='cooking', total_amount=24000)

        response = self.client.post(
            reverse('tables:group_payment', args=[group.id]),
            data=json.dumps({'payment_method': '카드'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        self.assertEqual(order.payment_method, '카드')
        self.assertEqual(order.group_name, '단체손님 1')

        group.delete()
        order.refresh_from_db()
        self.assertEqual(order.group_name, '단체손님 1')

    def test_unpaid_order_can_be_deleted_from_table_detail(self):
        table = Table.objects.create(number=1, status='ordered')
        order = Order.objects.create(table=table, status='cooking', total_amount=10000)

        response = self.client.post(reverse('orders:delete', args=[order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(Order.objects.filter(pk=order.id).exists())
        table.refresh_from_db()
        self.assertEqual(table.status, 'empty')
