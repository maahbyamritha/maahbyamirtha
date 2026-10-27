from unittest.mock import patch
from django.test import TestCase
from . import catalog
from .models import Category

NODE = {'id': 'gid://shopify/Product/1', 'title': 'Test saree', 'handle': 'test-saree',
        'description': '<script>not html</script>', 'availableForSale': True,
        'featuredImage': {'url': 'https://cdn.shopify.com/test.jpg'},
        'priceRange': {'minVariantPrice': {'amount': '999.0', 'currencyCode': 'INR'}}}


class ShopifyPagesTests(TestCase):
    def response_data(self, document, variables=None):
        if 'product(handle:' in document:
            return {'data': {'product': NODE if variables['handle'] == 'test-saree' else None}}
        connection = {'nodes': [NODE], 'pageInfo': {'hasNextPage': False, 'endCursor': None}}
        if 'collection(handle:' in document:
            return {'data': {'collection': None}}
        if 'collections(first:' in document:
            return {'data': {'collections': {'nodes': [], 'pageInfo': {'hasNextPage': False, 'endCursor': None}}}}
        return {'data': {'products': connection}}

    @patch('store.catalog.shopify_graphql')
    def test_live_product_renders_in_home_list_and_detail(self, api):
        api.side_effect = self.response_data
        for url in ['/', '/new-arrivals/', '/product/test-saree/']:
            response = self.client.get(url)
            self.assertContains(response, 'Test saree')
            if url == '/':
                self.assertNotContains(response, '₹999')
                self.assertContains(response, 'family=Poppins')
            else:
                self.assertContains(response, '₹999')
            self.assertContains(response, 'https://cdn.shopify.com/test.jpg')
        self.assertContains(self.client.get('/product/test-saree/'), '&lt;script&gt;')
        self.assertEqual(self.client.get('/product/missing/').status_code, 404)

    @patch('store.catalog.shopify_graphql')
    def test_uncreated_editorial_collection_is_empty_not_demo_catalog(self, api):
        api.side_effect = self.response_data
        Category.objects.get_or_create(slug='silk', defaults={'name': 'Silk'})
        self.assertContains(self.client.get('/collections/silk/'), 'No sarees in this collection yet')
        self.assertContains(self.client.get('/collections/'), 'Shop all sarees')
        self.assertEqual(self.client.get('/collections/missing/').status_code, 404)

    @patch('store.catalog.shopify_graphql', return_value={'errors': [{'message': 'ACCESS_DENIED'}]})
    def test_upstream_failure_is_not_reported_as_empty_or_missing(self, api):
        for url in ['/new-arrivals/', '/collections/', '/collections/silk/', '/product/test-saree/']:
            self.assertContains(self.client.get(url), 'temporarily unavailable', status_code=503)
        self.assertContains(self.client.get('/'), 'temporarily unavailable')

    @patch('store.catalog.shopify_graphql')
    def test_collection_mapping_and_pagination(self, api):
        api.return_value = {'data': {'collection': {'title': 'Silk', 'handle': 'silk', 'description': 'Silk sarees', 'products': {'nodes': [NODE], 'pageInfo': {'hasNextPage': True, 'endCursor': 'next=='}}}}}
        response = self.client.get('/collections/silk/?after=previous')
        self.assertContains(response, 'Test saree')
        self.assertContains(response, 'next%3D%3D')
        self.assertEqual(api.call_args.args[1]['after'], 'previous')
        self.assertEqual(api.call_args.args[1]['handle'], 'silk')

    def test_money_preserves_fractional_prices_and_currency(self):
        node = {**NODE, 'priceRange': {'minVariantPrice': {'amount': '1234.50', 'currencyCode': 'USD'}}}
        self.assertEqual(catalog.product_data(node)['price_display'], 'USD 1,234.50')

    @patch('store.catalog.shopify_graphql')
    def test_restored_product_details_and_collection_links(self, api):
        api.return_value = {'data': {'product': {**NODE,
            'productType': 'Silk', 'tags': ['New'],
            'collections': {'nodes': [{'title': 'New arrivals', 'handle': 'new-arrivals'},
                                      {'title': 'Silk', 'handle': 'silk'}]},
            'fabric': {'value': 'Pure silk'}, 'length': {'value': '5.5 m with blouse piece'},
            'care': {'value': 'Dry clean recommended'},
        }}}
        response = self.client.get('/product/test-saree/')
        for text in ['Pure silk', '5.5 m with blouse piece', 'Dry clean recommended',
                     'Back to silk', 'href="/collections/silk/"', '<span class="badge">new</span>']:
            self.assertContains(response, text)
        self.assertNotContains(response, 'aria-label="Breadcrumb"')
        self.assertIn('metafield(namespace: "custom", key: "fabric")', api.call_args.args[0])

    @patch('store.catalog.shopify_graphql')
    def test_missing_optional_details_and_sold_out_product(self, api):
        api.return_value = {'data': {'product': {**NODE, 'availableForSale': False,
            'tags': [], 'collections': {'nodes': []}, 'fabric': None, 'length': None, 'care': None}}}
        response = self.client.get('/product/test-saree/')
        self.assertContains(response, 'Sold out')
        self.assertContains(response, 'Back to sarees')
        self.assertNotContains(response, '<dl')
        self.assertNotContains(response, '<span class="badge">new</span>')
