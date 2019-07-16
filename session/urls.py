from django.urls import path

from . import views

urlpatterns = [
    # ex: /session/
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('materials/<pk>/', views.MaterialView.as_view(), name='material_detail'),
    path('machines/<pk>', views.MachineView.as_view(), name='machine_detail'),
    path('session_manager/', views.SessionListView.as_view(), name="session_manager"),
    path('session_manager/<int:pk>/', views.SessionView.as_view(), name='session_detail'),
    path('new_session/', views.new_session, name="new_session")
    ]
