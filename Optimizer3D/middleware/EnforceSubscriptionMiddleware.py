from django.utils import timezone
from django.contrib import messages
from django.conf import settings


def enforce_subscription_middleware(get_response):
    # One-time configuration and initialization.
    # Executed when server is launched
    tlp = settings.TIME_LIMITED_PLANS

    def middleware(request):
        # Time limited subscription types:
        now = timezone.now()
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if request.user.is_authenticated:
            user = request.user if request.user.member_of_corporation is None else request.user.member_of_corporation.owner
            if user.plan in tlp:
                if user.subscription_expiration < now:
                    print("expiring")
                    user.expire()
                    if user == request.user:
                        messages.warning(request, "Your subscription has expired.")
            else:
                if user.subscription_expiration > now and user.plan == 'basic':
                    user.plan = 'premium'
            request.user.last_active = timezone.now()
            request.user.save()
            user.save()

        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware
