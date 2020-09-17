from django.middleware.locale import LocaleMiddleware
from django.utils.translation import deactivate as deactivate_lang

class SiteLocaleMiddleware(LocaleMiddleware):
    def process_request(self, request):
        if (request.path.startswith('/admin/')
                or request.path.startswith('/rosetta/')):
            deactivate_lang()
            return None

        return super().process_request(request)

    def process_response(self, request, response):
        if (request.path.startswith('/admin/')
                or request.path.startswith('/rosetta/')):
            return response

        return super().process_response(request, response)

class IgnoreBrowserLanguageSetting:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'HTTP_ACCEPT_LANGUAGE' in request.META:
            del request.META['HTTP_ACCEPT_LANGUAGE']
        return self.get_response(request)

