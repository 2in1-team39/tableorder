from django.test import TestCase
from django.urls import reverse

from orders.models import Order
from .models import Table


class TableStatusApiTests(TestCase):
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
