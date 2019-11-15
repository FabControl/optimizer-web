from django.contrib.auth import get_user_model
from django.core import mail
from authentication.forms import SignUpForm, ResetPasswordForm
from django.test import TestCase
import re


# Empty helper class
class FakeHttpRequest():
    pass


class SignUpFormTest(TestCase):
    activate_link_match = re.compile(re.escape('https://test.local.domain') +
            '/activate_account/[0-9a-zA-Z]{2}/[0-9a-z-]{24}/')

    def test_sugnup_message(self):
        req = FakeHttpRequest()
        req.META = {'HTTP_HOST':'test.local.domain'}

        SignUpForm({
            'email' : 'someone@somewhere.com',
            'first_name' : 'Someone',
            'last_name' : 'Unknown',
            'password1' : 'SomeVerySecretPassword',
            'password2' : 'SomeVerySecretPassword',
            'company' : 'Test',
            'termsofuse' : True
            }).save_and_notify(req)

        # should send single message to single recipent
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[-1]
        self.assertEqual(m.to, ['someone@somewhere.com'])
        self.assertEqual(m.subject, 'Account activation')
        # message should contain plain body and html alternative
        self.assertEqual(len(m.alternatives), 1)
        self.assertEqual(m.alternatives[0][1], 'text/html')
        # Message should address person by first and last names
        self.assertTrue('Someone Unknown' in m.body)
        self.assertTrue('Someone Unknown' in m.alternatives[0][0])
        # Password should never be included in message
        self.assertFalse('SomeVerySecretPassword' in m.body)
        self.assertFalse('SomeVerySecretPassword' in m.alternatives[0][0])
        # Email shold include account activateion link
        self.assertFalse(self.activate_link_match.search(m.body) is None)
        self.assertFalse(self.activate_link_match.search(m.alternatives[0][0]) is None)


class ResetPasswordFormTest(TestCase):
    req = FakeHttpRequest()
    req.META = {'HTTP_HOST':'test.local.domain'}
    reset_link_match = re.compile(re.escape('https://test.local.domain') +
            '/reset/[0-9a-zA-Z]{2}/[0-9a-z-]{24}/')


    def test_unknown_account_message(self):
        form = ResetPasswordForm({
            'email':'someone@somewhere.com'
            })

        form.full_clean()
        form.save(request=self.req)

        # should send single message to single recipent
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[-1]
        self.assertEqual(m.to, ['someone@somewhere.com'])
        self.assertEqual(m.subject, 'Password recovery')
        # message should contain plain body and html alternative
        self.assertEqual(len(m.alternatives), 1)
        self.assertEqual(m.alternatives[0][1], 'text/html')
        # If account was not in database, user email should be included
        self.assertTrue('someone@somewhere.com' in m.body)
        self.assertTrue('someone@somewhere.com' in m.alternatives[0][0])

    def test_known_account_message(self):
        user = get_user_model().objects.create_user(email='someone@somewhere.com',
                                 password='SomeSecretPassword')

        form = ResetPasswordForm({
            'email':'someone@somewhere.com'
            })

        form.full_clean()
        form.save(request=self.req)

        # should send single message to single recipent
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[-1]
        self.assertEqual(m.to, ['someone@somewhere.com'])
        self.assertEqual(m.subject, 'Password recovery')
        # message should contain plain body and html alternative
        self.assertEqual(len(m.alternatives), 1)
        self.assertEqual(m.alternatives[0][1], 'text/html')
        # If account is in database, user should receive recovery link
        self.assertFalse(self.reset_link_match.search(m.body) is None)
        self.assertFalse(self.reset_link_match.search(m.alternatives[0][0]) is None)
        # Password should never be included in message
        self.assertFalse('SomeVerySecretPassword' in m.body)
        self.assertFalse('SomeVerySecretPassword' in m.alternatives[0][0])
