from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SessionViewsTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 is_active=True,
                                 password='SomeSecretPassword')

    @classmethod
    def tearDownClass(self):
        self.user.delete()

    def test_index_page(self):
        self.client.logout()
        resp = self.client.get('', follow=True)
        # logged out sessions redirect to login page
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertFalse(resp.redirect_chain[-1][0] == reverse('dashboard'))

        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        resp = self.client.get('', follow=True)
        # dashboard should be used as index page
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertTrue(resp.redirect_chain[-1][0] == reverse('dashboard'))

