from django.urls import path

from . import views

urlpatterns = [
    # ex: /session/
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('resources/materials/', views.MaterialsView.as_view(), name='material_manager'),
    path('resources/materials/new/', views.material_form, name='material_form'),
    path('resources/materials/<pk>/', views.MaterialView.as_view(), name='material_detail'),

    path('resources/machines/', views.MachinesView.as_view(), name='machine_manager'),
    path('resources/machines/new/', views.machine_form, name='machine_form'),
    path('resources/machines/<pk>/', views.MachineView.as_view(), name='machine_detail'),

    path('resources/settings/', views.SettingsView.as_view(), name='setting_manager'),
    path('resources/settings/<pk>/', views.SettingView.as_view(), name='settings_detail'),

    path('sessions/', views.SessionListView.as_view(), name="session_manager"),
    path('sessions/<int:pk>/', views.generate_or_validate, name='session_detail'),
    path('sessions/<int:pk>/back/', views.session_validate_undo, name='session_validate_back'),
    path('sessions/<int:pk>/next/<str:priority>', views.next_test_switch, name='session_next_test'),
    path('sessions/<int:pk>/gcode/', views.serve_gcode, name='gcode'),
    path('sessions/<int:pk>/delete/', views.SessionDelete.as_view(), name='session_delete'),
    path('sessions/<int:pk>/<str:number>/', views.test_switch, name='test_switch'),
    path('sessions/new/', views.new_session, name='new_session'),

    path('help/FAQ/', views.faq, name="faq"),
    path('help/quick_start/', views.quick_start, name="quickstart"),
    path('help/support/', views.support, name="support"),
    path('help/guide/', views.guide, name="guide"),

    path('testing_session', views.testing_session, name="testing_session")
    ]
