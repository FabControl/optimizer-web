from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.core import mail
import re


class PasswordResetViewsTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.test_client = Client(HTTP_HOST=settings.ALLOWED_HOSTS[0])
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 password='SomeSecretPassword')

        self.reset_link_match = re.compile('https://' +
                                        re.escape(settings.ALLOWED_HOSTS[0]) +
                                        '(/reset/[0-9a-zA-Z]{2}/[0-9a-z-]{24}/)')

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


    def test_password_reset_link(self):
        # request password recovery
        reset_url = reverse('password_reset')
        known_response = self.test_client.post(reset_url, {'email':'known_user@somewhere.com'},
                                          follow=True)
        self.assertEqual(known_response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        # extract link from email
        recovery_url = self.reset_link_match.search(mail.outbox[0].body).group(1)

        # check if link is valid
        pw_reset_page = self.test_client.get(recovery_url, follow=True)
        self.assertEqual(pw_reset_page.status_code, 200)
        # valid link should redirect to change password page
        self.assertEqual(pw_reset_page.redirect_chain[0][1], 302)

        # check if new password can be set successfully
        pw_changed_page = self.test_client.post(pw_reset_page.redirect_chain[-1][0],
                                            {
                                                'new_password1':'newSecretPassword',
                                                'new_password2':'newSecretPassword'
                                            },
                                            follow=True)
        self.assertEqual(pw_changed_page.status_code, 200)
        self.assertEqual(pw_changed_page.redirect_chain[0][1], 302)

        # Make sure that recovery link is no longer valid
        pw_reset_page = self.test_client.get(recovery_url)
        # invalid links doesn't redirect
        self.assertEqual(pw_reset_page.status_code, 200)
