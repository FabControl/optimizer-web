from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings


class PasswordResetViewsTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.test_client = Client(HTTP_HOST=settings.ALLOWED_HOSTS[0])
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 password='SomeSecretPassword')

    @classmethod
    def tearDownClass(self):
        self.user.delete()


    def test_account_email_leak(self):
        reset_url = reverse('password_reset')
        known_response = self.test_client.post(reset_url, {'email':'known_user@somewhere.com'},
                                          follow=True)
        unknown_response = self.test_client.post(reset_url, {'email':'other_user@somewhere.com'},
                                          follow=True)

        # Both requests should have equal behavior
        self.assertEqual(known_response.status_code, unknown_response.status_code)
        self.assertEqual(known_response.redirect_chain, unknown_response.redirect_chain)
        self.assertEqual(known_response.content, unknown_response.content)

