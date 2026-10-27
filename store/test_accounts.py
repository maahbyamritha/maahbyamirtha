from django.test import SimpleTestCase, override_settings
from .account_views import account_url


@override_settings(SHOPIFY_STORE_DOMAIN='maah-test.myshopify.com', SHOPIFY_CUSTOMER_ACCOUNT_URL='')
class ShopifyAccountTests(SimpleTestCase):
    def test_login_page_is_ready_and_links_to_shopify_entry(self):
        response = self.client.get('/account/')
        self.assertContains(response, 'Welcome back')
        self.assertContains(response, 'href="/account/login/"')
        self.assertContains(response, 'one-time code')
        self.assertNotContains(response, 'type="password"')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.client.get('/login/').status_code, 200)

    def test_redirect_ignores_untrusted_urls_and_email(self):
        response = self.client.get('/account/login/?next=https://untrusted.example/&email=private@example.com')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://maah-test.myshopify.com/account')
        self.assertNotIn('sessionid', response.cookies)

    def test_methods_do_not_accept_credentials(self):
        self.assertEqual(self.client.post('/account/login/', {'password': 'test'}).status_code, 405)

    @override_settings(SHOPIFY_CUSTOMER_ACCOUNT_URL='https://account.example.com/')
    def test_branded_account_url_from_server_configuration(self):
        self.assertEqual(self.client.get('/account/login/')['Location'], 'https://account.example.com/')

    @override_settings(SHOPIFY_STORE_DOMAIN='')
    def test_missing_settings_offer_shopping_not_broken_login(self):
        response = self.client.get('/account/login/')
        self.assertContains(response, 'temporarily unavailable', status_code=503)
        self.assertNotContains(response, 'Continue to sign in', status_code=503)

    def test_invalid_configuration_rejected(self):
        for domain in ['https://store.myshopify.com', 'store.myshopify.com/evil', 'store.myshopify.com@evil.example']:
            with self.settings(SHOPIFY_STORE_DOMAIN=domain):
                self.assertIsNone(account_url())
        for url in ['http://account.example.com', 'javascript:alert(1)', 'https://user:password@example.com']:
            with self.settings(SHOPIFY_CUSTOMER_ACCOUNT_URL=url):
                self.assertIsNone(account_url())
