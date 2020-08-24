from django.middleware.locale import LocaleMiddleware

class SiteLocaleMiddleware(LocaleMiddleware):
    def process_request(self, request):
        if not request.path.startswith('/admin/'):
            return super().process_request(request)

    def process_response(self, request, response):
        if not request.path.startswith('/admin/'):
            return super().process_response(request, response)
        return response
