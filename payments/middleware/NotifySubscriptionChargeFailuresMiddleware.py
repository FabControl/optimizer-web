from django.contrib import messages
from payments.models import Subscription
from django.shortcuts import reverse
from django.utils import safestring


def notify_failures_middleware(get_response):
    # One-time configuration and initialization.
    # Executed when server is launched

    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if request.user.is_authenticated:
            try:
                subscription = Subscription.objects.get(user=request.user,
                                                state=Subscription.CHARGE_FAILED)
            except Subscription.DoesNotExist:
                pass
            else:
                messages.warning(request, 
                                safestring.mark_safe(
                                        'Your subscription payment has failed.<br>Check e-mail for details or <a href="{}#subscription">Update card</a>.'.format(
                                                reverse('account_legal_info', kwargs={section:'subscription'}))))
                subscription.state = Subscription.FAILURE_NOTIFIED
                subscription.save()

        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware
