from django.contrib import admin
from django.urls import path
from django.conf import settings

class OptimizerAdminSite(admin.AdminSite):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_template = 'administration/admin_index.html'
        self._custom_urls = {}


    def get_urls(self):
        urls = super().get_urls()
        return urls + list(self._custom_urls.values())


    def register_custom_view(self, pattern, view, **kwargs):
        name = 'custom-admin-page-' + pattern
        if pattern in self._custom_urls:
            msg = 'View "{0}" already exists in custom wiews: {1}'.format(pattern, self._custom_urls[name])
            raise Exception(msg)
        self._custom_urls[pattern] = path('custom_pages/'+pattern,
                                          self.admin_view(view), 
                                          name=name,
                                          **kwargs)


    def each_context(self, *a, **k):
        context = super().each_context(*a, **k)

        custom_views = {'admin:custom-admin-page-'+k:k.replace('_', ' ') for k in self._custom_urls.keys()}
        context['custom_views'] = custom_views

        if hasattr(settings, 'ROSETTA_SHOW_AT_CUSTOM_ADMIN_PANEL'):
            context['show_rosetta_link'] = settings.ROSETTA_SHOW_AT_CUSTOM_ADMIN_PANEL
        return context



