from django.core.exceptions import MiddlewareNotUsed
from django_ip_geolocation.middleware import IpGeolocationMiddleware
from django.conf import settings
from django.core.exceptions import PermissionDenied
import logging

# In settings.py
#GEO_RESTRICTION_WHITELIST = ['RU']
#GEO_RESTRICTION_BLACKLIST = ['RU']
# If both exist, then ONLY whitelist is used
# Country codes available https://en.wikipedia.org/wiki/ISO_3166-1

def geoRestrictExempt(viewFunc):
    viewFunc.geo_restrict_exempt = True
    return viewFunc


# disable error messages from django_ip_geolocation module
class _Geoip_spam_filter(logging.Filter):
    def filter(self, record):
        if not record.pathname:
            return 1
        if not record.pathname.endswith('/django_ip_geolocation/middleware.py'):
            return 1
        if record.msg != "Couldn't geolocate ip":
            return 1
        record.exc_info = None
        return 1

logging.getLogger().addFilter(_Geoip_spam_filter())

class GeoRestrictAccessMiddleware(IpGeolocationMiddleware):
    def __init__(self, get_response=None):
        if getattr(settings, 'GEO_RESTRICTION_DISABLED', None) is not None:
            raise MiddlewareNotUsed()

        self.has_whitelist = False
        self.has_blacklist = False
        if hasattr(settings, 'GEO_RESTRICTION_WHITELIST'):
            self.has_whitelist = settings.GEO_RESTRICTION_WHITELIST is not None

        if hasattr(settings, 'GEO_RESTRICTION_BLACKLIST'):
            self.has_blacklist = settings.GEO_RESTRICTION_BLACKLIST is not None

        super(GeoRestrictAccessMiddleware, self).__init__(get_response)


    def process_view(self, request, view_func, view_args, view_kwargs):
        if getattr(view_func, 'geo_restrict_exempt', False) == True:
            return None

        if not hasattr(request, 'geolocation'):
            return None

        country = request.geolocation['county']['code']

        if self.has_whitelist:
            if country in settings.GEO_RESTRICTION_WHITELIST:
                return None
            else:
                raise PermissionDenied()

        if self.has_blacklist:
            if country in settings.GEO_RESTRICTION_BLACKLIST:
                raise PermissionDenied()


    def process_response(self, request, response):
        return response
