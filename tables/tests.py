from django.test import TestCase
from django.urls import reverse
import json

from orders.models import Order
from .models import Table, TableGroup


class TableStatusApiTests(TestCase):
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
