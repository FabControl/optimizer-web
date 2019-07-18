from django.urls import path

from . import views

urlpatterns = [
    # ex: /session/
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('materials/<pk>/', views.MaterialView.as_view(), name='material_detail'),
    path('machines/<pk>', views.MachineView.as_view(), name='machine_detail'),
    path('sessions/', views.SessionListView.as_view(), name="session_manager"),
    path('sessions/<int:pk>/', views.SessionView.as_view(), name='session_detail'),
    path('sessions/new/', views.new_session, name='new_session'),
    path('help/FAQ/', views.faq, name="faq"),
    path('help/quick_start/', views.quick_start, name="quickstart"),
    path('help/support/', views.support, name="support"),
    path('help/guide/', views.guide, name="guide")
    ]
