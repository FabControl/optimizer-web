from django.core import mail
from authentication.forms import SignUpForm
from django.test import TestCase


# Empty helper class
class FakeHttpRequest():
    pass


class SignUpFormTest(TestCase):
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
        self.assertEqual(m.subject, 'Account registration')
        # message should contain plain body and html alternative
        self.assertEqual(len(m.alternatives), 1)
        self.assertEqual(m.alternatives[0][1], 'text/html')
        # Message should address person by first and last names
        self.assertTrue('Someone Unknown' in m.body)
        self.assertTrue('Someone Unknown' in m.alternatives[0][0])
        # Password should never be included in message
        self.assertFalse('SomeVerySecretPassword' in m.body)
        self.assertFalse('SomeVerySecretPassword' in m.alternatives[0][0])

