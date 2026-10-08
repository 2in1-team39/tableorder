import json

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from menus.models import Menu
from tables.models import Table
from .models import Order, OrderItem


class KitchenOrderManagementTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(number=1)
        self.cooked_menu = Menu.objects.create(name='찌개', price=9000, requires_cooking=True)
        self.drink_menu = Menu.objects.create(name='음료', price=2000, requires_cooking=False)

    def create_order(self, status='cooking', menu=None):
        order = Order.objects.create(table=self.table, status=status, total_amount=9000)
        OrderItem.objects.create(
            order=order,
            menu=menu or self.cooked_menu,
            quantity=1,
            unit_price=(menu or self.cooked_menu).price,
        )
        return order

    def test_completed_filter_does_not_change_active_orders_to_paid(self):
        active_order = self.create_order(status='cooking')
        paid_order = self.create_order(status='paid')

        response = self.client.get(reverse('orders:list'), {'status': 'completed'})

        self.assertEqual(response.status_code, 200)
        active_order.refresh_from_db()
        self.assertEqual(active_order.status, 'cooking')
        self.assertContains(response, f'data-order-id="{paid_order.id}"')
        self.assertNotContains(response, f'data-order-id="{active_order.id}"')

    def test_kitchen_opens_on_cooking_tab_by_default(self):
        cooking_order = self.create_order(status='cooking')
        ready_order = self.create_order(status='ready')

        response = self.client.get(reverse('orders:list'))

        self.assertEqual(response.context['status_filter'], 'cooking')
        self.assertContains(response, f'data-order-id="{cooking_order.id}"')
        self.assertNotContains(response, f'data-order-id="{ready_order.id}"')

    def test_reopening_a_completed_item_reopens_its_order(self):
        order = self.create_order(status='ready')
        item = order.items.get()
        item.status = 'ready'
        item.save()

        response = self.client.post(
            reverse('orders:update_menu_status', args=[item.id]),
            data=json.dumps({'status': 'cooking'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['order_status'], 'cooking')
        order.refresh_from_db()
        self.assertEqual(order.status, 'cooking')

    def test_table_is_ready_only_after_all_its_cooking_items_are_ready(self):
        second_menu = Menu.objects.create(name='만두', price=5000, requires_cooking=True)
        order = Order.objects.create(table=self.table, status='cooking', total_amount=14000)
        first_item = OrderItem.objects.create(
            order=order, menu=self.cooked_menu, quantity=1, unit_price=9000
        )
        second_item = OrderItem.objects.create(
            order=order, menu=second_menu, quantity=1, unit_price=5000
        )

        first_response = self.client.post(
            reverse('orders:update_menu_status', args=[first_item.id]),
            data=json.dumps({'status': 'ready'}),
            content_type='application/json',
        )

        self.assertEqual(first_response.json()['order_status'], 'cooking')
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'ordered')

        second_response = self.client.post(
            reverse('orders:update_menu_status', args=[second_item.id]),
            data=json.dumps({'status': 'ready'}),
            content_type='application/json',
        )

        self.assertEqual(second_response.json()['order_status'], 'ready')
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'cooking')

    def test_kitchen_counts_include_today_paid_orders_but_exclude_non_kitchen_orders(self):
        self.create_order(status='cooking')
        self.create_order(status='ready')
        self.create_order(status='paid')
        self.create_order(status='paid', menu=self.drink_menu)

        response = self.client.get(reverse('orders:kitchen_status_api'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cooking_count'], 1)
        self.assertEqual(response.json()['ready_count'], 1)
        self.assertEqual(response.json()['completed_count'], 1)
        self.assertEqual(response.json()['total_count'], 3)

    def test_order_memo_is_saved_with_a_new_order(self):
        response = self.client.post(
            reverse('orders:save', args=[self.table.id]),
            data=json.dumps({
                'items': [{'menu_id': self.cooked_menu.id, 'quantity': 1, 'options': []}],
                'memo': '덜 맵게 부탁드립니다',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        order_id = response.json()['order_id']
        self.assertEqual(Order.objects.get(id=order_id).memo, '덜 맵게 부탁드립니다')

        report_response = self.client.get(reverse('reports:dashboard'))
        self.assertContains(report_response, f'#{order_id}')
        self.assertContains(report_response, '미결제')

    def test_sold_out_menu_cannot_be_saved_as_an_order(self):
        self.cooked_menu.is_sold_out = True
        self.cooked_menu.save()

        response = self.client.post(
            reverse('orders:save', args=[self.table.id]),
            data=json.dumps({
                'items': [{'menu_id': self.cooked_menu.id, 'quantity': 1, 'options': []}],
            }),
            content_type='application/json',
        )

        self.assertFalse(response.json()['success'])
        self.assertIn('품절', response.json()['error'])
        self.assertFalse(Order.objects.exists())


class OrderAdminTests(TestCase):
    def test_order_change_page_renders_order_item_total(self):
        table = Table.objects.create(number=1)
        menu = Menu.objects.create(name='칼국수', price=9000)
        order = Order.objects.create(table=table, total_amount=9000)
        OrderItem.objects.create(order=order, menu=menu, quantity=1, unit_price=9000)
        admin_user = get_user_model().objects.create_superuser(
            username='admin', password='password'
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse('admin:orders_order_change', args=[order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '9,000')
