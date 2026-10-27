from copy import deepcopy
from unittest.mock import patch
from django.test import SimpleTestCase, Client, override_settings
from django.http import HttpResponse
from . import cart, cart_views, catalog

VARIANT = {'id': 'gid://shopify/ProductVariant/1', 'title': 'Rose', 'available': True, 'price': '₹999'}
PRODUCT = {'variants': [VARIANT]}
MONEY = {'amount': '999.00', 'currencyCode': 'INR'}
CART = {'id': 'gid://shopify/Cart/test?key=private', 'totalQuantity': 1,
        'checkoutUrl': 'https://example.myshopify.com/checkouts/test',
        'cost': {'subtotalAmount': MONEY, 'totalAmount': MONEY},
        'lines': {'nodes': [{'id': 'line1', 'quantity': 1, 'cost': {'totalAmount': MONEY},
                            'merchandise': {'title': 'Rose', 'availableForSale': True,
                             'image': None, 'product': {'title': '<Saree>', 'handle': 'test'}}}],
                  'pageInfo': {'hasNextPage': False, 'endCursor': None}}}


class CartViewsTests(SimpleTestCase):
    def cookie(self, client=None):
        response = cart_views.remember(HttpResponse(), CART['id'])
        (client or self.client).cookies[cart_views.COOKIE] = response.cookies[cart_views.COOKIE]

    @patch('store.cart.shopify_graphql')
    def test_empty_and_tampered_cart_does_not_call_shopify(self, api):
        for value in ['', 'tampered']:
            self.client.cookies[cart_views.COOKIE] = value
            response = self.client.get('/cart/')
            self.assertContains(response, 'Your cart is empty')
            self.assertIn('no-store', response['Cache-Control'])
        api.assert_not_called()

    @patch('store.cart.get', return_value=None)
    @patch('store.catalog.product', return_value=PRODUCT)
    @patch('store.cart.mutate', return_value=(CART['id'], []))
    def test_add_creates_cart_and_protects_cookie(self, mutate, product, get):
        response = self.client.post('/cart/add/', {'handle': 'test', 'variant': VARIANT['id'], 'quantity': '2', 'price': '1'})
        self.assertRedirects(response, '/cart/', fetch_redirect_response=False)
        self.assertEqual(mutate.call_args.args[:2], ('cartCreate', {'input': {'lines': [{'merchandiseId': VARIANT['id'], 'quantity': 2}]}}))
        self.assertTrue(response.cookies['maah_cart']['httponly'])
        self.assertEqual(response.cookies['maah_cart']['samesite'], 'Lax')
        self.assertNotIn(CART['id'], response.content.decode())

    @patch('store.cart.get', return_value=CART)
    @patch('store.catalog.product', return_value=PRODUCT)
    @patch('store.cart.mutate', return_value=(CART['id'], []))
    def test_existing_cart_adds_line(self, mutate, product, get):
        self.cookie()
        self.client.post('/cart/add/', {'handle': 'test', 'variant': VARIANT['id'], 'quantity': 1})
        self.assertEqual(mutate.call_args.args[0], 'cartLinesAdd')
        self.assertEqual(mutate.call_args.args[1]['cartId'], CART['id'])

    @patch('store.cart.mutate')
    @patch('store.catalog.product', return_value=PRODUCT)
    def test_invalid_quantity_or_variant_never_mutates(self, product, mutate):
        for quantity in ['0', '-1', '100', 'abc', '1.5']:
            self.assertEqual(self.client.post('/cart/add/', {'quantity': quantity}).status_code, 400)
        response = self.client.post('/cart/add/', {'handle': 'test', 'quantity': 1, 'variant': 'other'})
        self.assertEqual(response.status_code, 400)
        product.return_value = {'variants': [{**VARIANT, 'available': False}]}
        self.assertEqual(self.client.post('/cart/add/', {'handle': 'test', 'quantity': 1, 'variant': VARIANT['id']}).status_code, 400)
        mutate.assert_not_called()

    @patch('store.cart.get', return_value=CART)
    @patch('store.cart.mutate', return_value=(CART['id'], []))
    def test_update_remove_and_foreign_line(self, mutate, get):
        self.cookie()
        response = self.client.post('/cart/change/', {'line': 'line1', 'action': 'update', 'quantity': 3})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mutate.call_args.args[0], 'cartLinesUpdate')
        self.assertEqual(mutate.call_args.args[1]['lines'][0]['quantity'], 3)
        self.client.post('/cart/change/', {'line': 'line1', 'action': 'remove'})
        self.assertEqual(mutate.call_args.args[0], 'cartLinesRemove')
        mutate.reset_mock()
        self.assertEqual(self.client.post('/cart/change/', {'line': 'foreign', 'action': 'remove'}).status_code, 400)
        mutate.assert_not_called()

    @patch('store.cart.get', return_value=CART)
    def test_checkout_uses_fresh_shopify_url_and_ignores_user_url(self, get):
        self.cookie()
        response = self.client.post('/cart/checkout/', {'checkoutUrl': 'https://untrusted.example/'})
        self.assertEqual(response['Location'], CART['checkoutUrl'])
        get.assert_called_once()
        get.return_value = {**CART, 'totalQuantity': 0}
        self.assertEqual(self.client.post('/cart/checkout/')['Location'], '/cart/')

    @patch('store.cart.get', side_effect=cart.CartError('Please try again.'))
    def test_upstream_failure_keeps_cart_cookie(self, get):
        self.cookie()
        response = self.client.get('/cart/')
        self.assertContains(response, 'Please try again.', status_code=503)
        self.assertNotContains(response, 'Your cart is empty', status_code=503)
        self.assertNotIn('maah_cart', response.cookies)

    @patch('store.cart.get', return_value=None)
    def test_expired_shopify_cart_clears_cookie(self, get):
        self.cookie()
        response = self.client.get('/cart/')
        self.assertEqual(response.cookies['maah_cart']['max-age'], 0)

    @patch('store.cart.get', return_value=CART)
    def test_cart_escapes_titles_and_uses_shopify_prices(self, get):
        self.cookie()
        response = self.client.get('/cart/')
        self.assertContains(response, '&lt;Saree&gt;')
        self.assertContains(response, '₹999')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_post_only_and_csrf(self):
        secure_client = Client(enforce_csrf_checks=True)
        for url in ['/cart/add/', '/cart/change/', '/cart/checkout/']:
            self.assertEqual(self.client.get(url).status_code, 405)
            self.assertEqual(secure_client.post(url, {}).status_code, 403)

    @override_settings(DEBUG=False)
    def test_production_cookie_secure(self):
        self.assertTrue(cart_views.remember(HttpResponse(), CART['id']).cookies['maah_cart']['secure'])


class CartApiTests(SimpleTestCase):
    @patch('store.cart.shopify_graphql')
    def test_paginated_lines(self, api):
        first = deepcopy(CART)
        first['lines']['pageInfo'] = {'hasNextPage': True, 'endCursor': 'next'}
        api.side_effect = [{'data': {'cart': first}}, {'data': {'cart': {'lines': CART['lines']}}}]
        result = cart.get(CART['id'])
        self.assertEqual(len(result['lines']['nodes']), 2)
        self.assertEqual(api.call_args.args[1]['after'], 'next')

    @patch('store.cart.shopify_graphql')
    def test_mutation_errors_warnings_and_timeout(self, api):
        api.return_value = {'data': {'cartCreate': {'cart': None, 'userErrors': [{'message': 'Not available'}], 'warnings': []}}}
        with self.assertRaisesMessage(cart.CartError, 'Not available'):
            cart.mutate('cartCreate', {'input': {}})
        api.return_value = {'data': {'cartCreate': {'cart': {'id': CART['id']}, 'userErrors': [], 'warnings': [{'message': 'Quantity adjusted'}]}}}
        self.assertEqual(cart.mutate('cartCreate', {'input': {}}), (CART['id'], ['Quantity adjusted']))
        api.reset_mock();api.side_effect = TimeoutError()
        with self.assertRaises(cart.CartError):
            cart.mutate('cartCreate', {'input': {}})
        self.assertEqual(api.call_count, 1)

    @patch('store.catalog.shopify_graphql')
    def test_variant_pagination_and_default_available_price(self, api):
        from .tests import NODE
        sold = {'id': 'sold', 'title': 'Blue', 'availableForSale': False, 'price': MONEY}
        available = {'id': 'available', 'title': 'Rose', 'availableForSale': True,
                     'price': {'amount': '1250', 'currencyCode': 'INR'}}
        api.side_effect = [
            {'data': {'product': {**NODE, 'variants': {'nodes': [sold], 'pageInfo': {'hasNextPage': True, 'endCursor': 'next'}}}}},
            {'data': {'product': {'variants': {'nodes': [available], 'pageInfo': {'hasNextPage': False, 'endCursor': None}}}}},
        ]
        item = catalog.product('test')
        self.assertEqual(len(item['variants']), 2)
        self.assertTrue(item['can_buy'])
        self.assertTrue(item['variants'][1]['selected'])
        self.assertEqual(item['price_display'], '₹1,250')

    @patch('store.cart.get', return_value=CART)
    @patch('store.catalog.product', return_value=PRODUCT)
    @patch('store.cart.mutate', return_value=(CART['id'], ['Quantity adjusted']))
    def test_inventory_warning_survives_redirect_once(self, mutate, product, get):
        response = self.client.post('/cart/add/', {'handle': 'test', 'quantity': 1, 'variant': VARIANT['id']})
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/cart/')
        self.assertContains(response, 'Quantity adjusted')
        self.assertNotContains(self.client.get('/cart/'), 'Quantity adjusted')
