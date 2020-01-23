from django.template.loader import get_template
#from django.template import Context
from django.core.mail import send_mail
from django.conf import settings
from django.http.request import HttpRequest

_HTML_TEMPLATE = 'email/{0}.html'
_PLAIN_TEMPLATE = 'email/{0}.txt'
_SUBJECTS = {
        'password_recovery_failure': 'Password recovery',
        'password_recovery': 'Password recovery',
        'register_complete': 'Account activation',
        'account_activated': 'New account activated',
        'register_with_known_email': 'Account registration'
        }


def send_to_single(to_address:str, message_type:str, request:HttpRequest, **context_kw):
    send_to_multi([to_address], message_type, request, **context_kw)

"""
This will send single message to all recipients
Remember that recipients will see each others email address
"""
def send_to_multi(recipients:list, message_type:str, request:HttpRequest, **context):
    context['application_url'] = 'https://' + request.META['HTTP_HOST']
#    context = Context(context_kw)
    plain = get_template(_PLAIN_TEMPLATE.format(message_type)).render(context)
    html = get_template(_HTML_TEMPLATE.format(message_type)).render(context)

    send_mail(_SUBJECTS[message_type], plain, settings.EMAIL_SENDER_ADDRESS,
                recipients, html_message=html)