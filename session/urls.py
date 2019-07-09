from django.urls import path

from . import views

urlpatterns = [
    # ex: /session/
    path('', views.index, name='index'),
    path('<str:name>/', views.material, name='material')
]
