from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six


class ActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                six.text_type(user.pk) + six.text_type(timestamp) +
                six.text_type(user.is_active)
                )

class AffiliateTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, affiliate, timestamp):
        # should be valid forever, so ignore timestamp
        return (
                six.text_type(affiliate.date_created) +
                six.text_type(affiliate.email) +
                six.text_type(affiliate.receiver) +
                six.text_type(affiliate.date_registered)
                )


account_activation_token = ActivationTokenGenerator()
affiliate_token_generator = AffiliateTokenGenerator()
