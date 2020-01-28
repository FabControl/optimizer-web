from django.core.exceptions import MiddlewareNotUsed
from django_ip_geolocation.middleware import IpGeolocationMiddleware
from django.conf import settings
from django.core.exceptions import PermissionDenied

# In settings.py
#GEO_RESTRICTION_WHITELIST = ['RU']
#GEO_RESTRICTION_BLACKLIST = ['RU']
# If both exist, then ONLY whitelist is used
# Country codes available https://en.wikipedia.org/wiki/ISO_3166-1

class GeoRestrictAccessMiddleware(IpGeolocationMiddleware):
    def __init__(self, get_response=None):
        self.has_whitelist = False
        self.has_blacklist = False
        if hasattr(settings, 'GEO_RESTRICTION_WHITELIST'):
            self.has_whitelist = settings.GEO_RESTRICTION_WHITELIST is not None

        if hasattr(settings, 'GEO_RESTRICTION_BLACKLIST'):
            self.has_blacklist = settings.GEO_RESTRICTION_BLACKLIST is not None

        if not (self.has_blacklist or self.has_whitelist):
            raise MiddlewareNotUsed()

        super(GeoRestrictAccessMiddleware, self).__init__(get_response)


    def process_request(self, request):
        # Uncomment for testing purpose on localhost
        # get addresses here https://lite.ip2location.com/ip-address-ranges-by-country
        #request.META['HTTP_X_FORWARDED_FOR'] = '5.182.84.0,'
        super(GeoRestrictAccessMiddleware, self).process_request(request)
        if not hasattr(request, 'geolocation'):
            return

        country = request.geolocation['county']['code']

        if self.has_whitelist:
            if country in settings.GEO_RESTRICTION_WHITELIST:
                return
            else:
                raise PermissionDenied()

        if self.has_blacklist:
            if country in settings.GEO_RESTRICTION_BLACKLIST:
                raise PermissionDenied()



    def process_response(self, request, response):
        return response
