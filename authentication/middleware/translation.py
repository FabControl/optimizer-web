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
