from django.utils import timezone
from django.contrib import messages


def enforce_subscription_middleware(get_response):
    # One-time configuration and initialization.
    # Executed when server is launched

    def middleware(request):
        now = timezone.now()
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if request.user.is_authenticated:
            if request.user.plan == 'premium':
                if request.user.subscription_expiration < now:
                    print("expiring")
                    request.user.expire()
                    messages.warning(request, "Your subscription has expired.")
            else:
                if request.user.subscription_expiration > now:
                    request.user.plan = 'premium'
            request.user.last_active = timezone.now()
            request.user.save()

        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware
