from django.utils import timezone
from django.contrib import messages
from django.conf import settings


def enforce_subscription_middleware(get_response):
    # One-time configuration and initialization.
    # Executed when server is launched

    def middleware(request):
        # Time limited subscription types:
        tlp = settings.TIME_LIMITED_PLANS
        now = timezone.now()
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if request.user.is_authenticated:
            if request.user.plan in tlp:
                if request.user.subscription_expiration < now:
                    print("expiring")
                    request.user.expire()
                    messages.warning(request, "Your subscription has expired.")
            else:
                if request.user.subscription_expiration > now and request.user.plan == 'basic':
                    request.user.plan = 'premium'
            request.user.last_active = timezone.now()
            request.user.save()

        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware
