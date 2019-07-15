from django.urls import path

from . import views

urlpatterns = [
    # ex: /session/
    path('', views.index, name='index'),
    path('<str:name>/', views.material, name='material'),
    path('session_manager/<int:session_number>', views.new_session, name='new_session')
    ]
