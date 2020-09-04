"""Optimizer3D URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib import admin
from django.urls import include, path
from .views import index
from django.conf import settings
from django.conf.urls.static import static
from rosetta import urls as rosetta_urls
from .views import CustomTranslationFormView

# A bit of a hack to override specific view from another app
for u in rosetta_urls.urlpatterns:
    if u.name == "rosetta-form":
        u.callback = CustomTranslationFormView.as_view()
        break

urlpatterns = [
                  path('', include('session.urls')),
                  path('', include('authentication.urls')),
                  path('admin/', admin.site.urls),
                  # path('', index, name='index')
                  path('', include('payments.urls')),
                  path('rosetta/', include('rosetta.urls')),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'session.views.error_404_view'
handler500 = 'session.views.error_500_view'
