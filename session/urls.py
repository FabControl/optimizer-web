from django.urls import path

from . import views

urlpatterns = [
    # ex: /session/
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('session_manager/<str:name>/', views.material, name='material'),
    path('session_manager/', views.session_manager, name="session_manager"),
    path('session_manager/<int:session_number>', views.new_session, name='session'),
    path('new_session/', views.new_session, name="new_session")
    ]
