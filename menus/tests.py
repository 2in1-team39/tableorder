from django.test import TestCase
from django.urls import reverse

from .models import Menu


class MenuSoldOutTests(TestCase):
    def setUp(self):
        self.menu = Menu.objects.create(name='칼국수', price=9000)

    def test_sold_out_toggle_is_reflected_in_orderable_menu_api(self):
        response = self.client.post(reverse('menus:toggle_sold_out', args=[self.menu.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_sold_out'])

        menu_response = self.client.get(reverse('menus:orderable_menus_api'))
        self.assertEqual(menu_response.status_code, 200)
        self.assertTrue(menu_response.json()[0]['is_sold_out'])

    def test_orderable_menu_api_uses_configured_sort_order(self):
        later_menu = Menu.objects.create(name='나중 메뉴', price=8000, sort_order=20)
        first_menu = Menu.objects.create(name='먼저 메뉴', price=7000, sort_order=10)

        response = self.client.get(reverse('menus:orderable_menus_api'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [menu['id'] for menu in response.json()],
            [first_menu.id, later_menu.id, self.menu.id],
        )
