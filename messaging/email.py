from django.template.loader import get_template
#from django.template import Context
from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives
from django.conf import settings
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.safestring import mark_safe

_HTML_TEMPLATE = 'email/{0}.html'
_PLAIN_TEMPLATE = 'email/{0}.txt'
_SUBJECTS = {
        'password_recovery_failure': 'Password recovery',
        'password_recovery': 'Password recovery',
        'affiliate_invitation': 'Invitation to 3DOptimizer',
        'affiliate_confirmed': 'Thanks for your 3DOptimizer referral',
        'register_complete': 'Account activation',
        'register_with_known_email': 'Account registration',
        'translation_updated': 'Translation updated'
        }


def send_to_single(to_address:str, message_type:str, request:HttpRequest, **context_kw):
    send_to_multi([to_address], message_type, request, [], **context_kw)


def send_to_devs(message_type:str, request:HttpRequest, attachments:list=[], **context_kw):
    send_to_multi(settings.DEVELOPERS, message_type, request, attachments, **context_kw)

"""
This will send single message to all recipients
Remember that recipients will see each others email address
"""
def send_to_multi(recipients:list,
                  message_type:str,
                  request:HttpRequest,
                  attachments:list,
                  **context):
    context['application_url'] = 'https://' + request.META['HTTP_HOST']
    context['index_url'] = context['application_url'] + reverse('index')
#    context = Context(context_kw)
    plain = get_template(_PLAIN_TEMPLATE.format(message_type)).render(context)
    html = get_template(_HTML_TEMPLATE.format(message_type)).render(context)

    connection = get_connection()
    mail = EmailMultiAlternatives(_SUBJECTS[message_type],
                                  plain,
                                  settings.EMAIL_SENDER_ADDRESS,
                                  recipients,
                                  attachments=attachments,
                                  connection=connection)
    mail.attach_alternative(html, 'text/html')

    mail.send()
