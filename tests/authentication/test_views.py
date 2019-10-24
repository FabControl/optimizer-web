from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings


class PasswordResetViewsTest(TestCase):

    def set_up(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 password='SomeSecretPassword')

    def test_account_email_leak(self):
        reset_url = reverse('password_reset')
        known_response = self.client.post(reset_url, {'email':'known_user@somewhere.com'},
                                          follow=True,
                                          HTTP_HOST=settings.ALLOWED_HOSTS[0])
        unknown_response = self.client.post(reset_url, {'email':'other_user@somewhere.com'},
                                          follow=True,
                                          HTTP_HOST=settings.ALLOWED_HOSTS[0])

        # Both requests should have equal behavior
        self.assertEqual(known_response.status_code, unknown_response.status_code)
        self.assertEqual(known_response.redirect_chain, unknown_response.redirect_chain)
        self.assertEqual(known_response.content, unknown_response.content)

