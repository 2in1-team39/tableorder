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

    def test_order_details_export_contains_order_and_item_information(self):
        self.table.memo = '창가 테이블'
        self.table.save()
        order = self.create_order('paid', 2, '고객 요청 사항')
        item = order.items.get()
        item.options = ['곱빼기', '김치 많이']
        item.save()

        response = self.client.get(reverse('reports:order_details_export'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8-sig')
        content = response.content.decode('utf-8-sig')
        self.assertIn('주문번호', content)
        self.assertIn(str(order.id), content)
        self.assertIn('창가 테이블', content)
        self.assertIn('고객 요청 사항', content)
        self.assertIn('칼국수', content)
        self.assertIn('곱빼기, 김치 많이', content)
