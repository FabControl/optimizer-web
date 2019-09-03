from django.urls import path

from . import views

urlpatterns = [
    # ex: /authentication/
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    ]
