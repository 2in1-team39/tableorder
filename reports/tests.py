from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from menus.models import Menu
from orders.models import Order, OrderItem
from tables.models import Table


class SalesDashboardOrderListTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(number=1)
        self.menu = Menu.objects.create(name='칼국수', price=9000)

    def create_order(self, status, quantity, memo=''):
        order = Order.objects.create(
            table=self.table,
            status=status,
            total_amount=9000 * quantity,
            memo=memo,
            payment_method='카드' if status == 'paid' else '',
            paid_at=timezone.now() if status == 'paid' else None,
        )
        OrderItem.objects.create(
            order=order,
            menu=self.menu,
            quantity=quantity,
            unit_price=9000,
        )
        return order

    def test_dashboard_lists_today_orders_regardless_of_payment_status(self):
        unpaid_order = self.create_order('cooking', 2, '면 많이')
        paid_order = self.create_order('paid', 1)

        response = self.client.get(reverse('reports:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['today_total_orders'], 2)
        self.assertContains(response, f'#{unpaid_order.id}')
        self.assertContains(response, f'#{paid_order.id}')
        self.assertContains(response, '결제완료')
        self.assertContains(response, '미결제')
        self.assertContains(response, '칼국수')

    def test_dashboard_uses_payment_date_not_order_creation_date(self):
        order = self.create_order('paid', 1)
        Order.objects.filter(pk=order.pk).update(
            created_at=timezone.now() - timedelta(days=1)
        )

        response = self.client.get(reverse('reports:dashboard'))

        self.assertContains(response, f'#{order.id}')
        self.assertEqual(response.context['today_orders'], 1)
