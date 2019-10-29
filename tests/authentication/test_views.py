from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.core import mail
import re


class PasswordChangeViewTest(TestCase):
    test_url = reverse('password_change')
    @classmethod
    def setUpClass(self):
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 password='SomeSecretPassword')

    @classmethod
    def tearDownClass(self):
        self.user.delete()

    def test_only_logged_in_users(self):
        # make sure client is logged out
        self.client.logout()
        resp = self.client.get(self.test_url, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.redirect_chain) > 0)
        redirected = re.match(r'((?:[/\w-])+)\??', resp.redirect_chain[-1][0])
        self.assertEqual(redirected.group(1), reverse('login'))

    def test_confirm_with_current_password(self):
        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))
        # Password change must be confirmed with current password
        resp = self.client.post(self.test_url, {
                    'old_password':'ThisIsNotCurrentPassword',
                    'new_password1':'somenewpass',
                    'new_password2':'somenewpass'
                },
                follow=True)
        # Failed password change does not redirect
        self.assertEqual(len(resp.redirect_chain), 0)
        self.assertEqual(resp.status_code, 200)


    def test_password_is_actually_changed(self):
        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))
        resp = self.client.post(self.test_url, {
                    'old_password':'SomeSecretPassword',
                    'new_password1':'somenewpass',
                    'new_password2':'somenewpass'
                },
                follow=True)
        self.assertEqual(resp.status_code, 200)
        # Successful password change should redirect
        self.assertTrue(len(resp.redirect_chain) > 0)
        # make sure old password no longer valid
        self.client.logout()
        self.assertFalse(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))
        # make sure new password works
        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='somenewpass'))
        # restore previous password for other tests
        self.user.set_password('SomeSecretPassword')
        self.user.save()


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


class LoginViewTest(TestCase):
    test_url = reverse('login')

    @classmethod
    def setUpClass(self):
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 password='SomeSecretPassword')

    @classmethod
    def tearDownClass(self):
        self.user.delete()


    def test_recovery_and_register_in_login_page(self):
        # login page should conatain links to password recovery and registration
        resp = self.client.get(self.test_url)

        self.assertEqual(resp.status_code, 200)

        signup_link = '<a href="{}">Sign up</a>'.format(reverse('signup'))
        self.assertTrue(bytes(signup_link, 'utf-8') in resp.content)

        recovery_link = '<a href="{}">Recover password</a>'.format(reverse('password_reset'))
        self.assertTrue(bytes(recovery_link, 'utf-8') in resp.content)


    def test_only_registred_users(self):
        # only valid users should be able to log in
        self.client.logout()
        resp = self.client.post(self.test_url, {
                                    'email': 'known_user@somewhere.com',
                                    'password' : 'ThisShouldFail'
                                }, follow=True)

        # failed logins redirect back to login page
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertEqual(resp.redirect_chain[-1][0], self.test_url)

        resp = self.client.post(self.test_url, {
                                    'email': 'known_user@somewhere.com',
                                    'password' : 'SomeSecretPassword'
                                }, follow=True)

        # successful logins redirect to dashboard
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertEqual(resp.redirect_chain[-1][0], reverse('dashboard'))


    def test_view_only_logged_out(self):
        # login page should be available only for logged out sessions
        self.assertTrue(self.client.login(email='known_user@somewhere.com',
                                            password='SomeSecretPassword'))

        resp = self.client.get(self.test_url, follow=True)
        # logged in users get redirected to dashboard
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertEqual(resp.redirect_chain[-1][0], reverse('dashboard'))


        self.client.logout()
        resp = self.client.get(self.test_url)

        # unknown sessions are not redirected from login page
        self.assertEqual(resp.status_code, 200)


