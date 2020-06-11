from django.urls import path

from . import views

urlpatterns = [
    # ex: /session/
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('resources/materials/', views.MaterialsView.as_view(), name='material_manager'),
    path('resources/materials/new/', views.material_form, name='material_form'),
    path('resources/materials/<pk>/', views.MaterialView.as_view(), name='material_detail'),
    path('resources/materials/<pk>/delete', views.MaterialDelete.as_view(), name='material_delete'),

    path('resources/machines/', views.MachinesView.as_view(), name='machine_manager'),
    path('resources/machines/new/', views.machine_form, name='machine_form'),
    path('resources/machines/<pk>/', views.machine_edit_view, name='machine_detail'),
    path('resources/machines/<pk>/delete', views.MachineDelete.as_view(), name='machine_delete'),
    path('resources/machines/sample/<int:pk>/', views.sample_machine_data, name='machine_sample'),

    path('sessions/', views.SessionListView.as_view(), name="session_manager"),
    path('sessions/<int:pk>/', views.session_dispatcher, name='session_detail'),
    path('sessions/<int:pk>/json', views.session_json, name='session_json'),
    path('sessions/<int:pk>/test_info', views.session_test_info, name='session__test_info'),
    path('sessions/<int:pk>/back/', views.session_validate_undo, name='session_validate_back'),
    path('sessions/<int:pk>/revert/', views.session_validate_revert, name='revert_to_test'),
    path('sessions/<int:pk>/next/<str:priority>', views.next_test_switch, name='session_next_test'),
    path('sessions/<int:pk>/gcode/', views.serve_gcode, name='gcode'),
    path('sessions/<int:pk>/config/<str:slicer>', views.serve_config, name='config'),
    path('sessions/<int:pk>/report/', views.serve_report, name='report'),
    path('sessions/<int:pk>/delete/', views.SessionDelete.as_view(), name='session_delete'),
    path('sessions/<int:pk>/overview/', views.overview_dispatcher, name='session_overview'),
    path('sessions/<int:pk>/switch/<str:number>/', views.test_switch, name='test_switch'),
    path('sessions/<int:pk>/rename/', views.session_rename, name='session_rename'),
    path('sessions/new/', views.new_session, name='new_session'),
    path('team_stats/', views.TeamStatsView.as_view(), name='team_stats'),

    path('help/FAQ/', views.faq, name="faq"),
    path('help/quick_start/', views.quick_start, name="quickstart"),
    path('help/support/', views.support, name="support"),
    path('help/terms_of_use/', views.terms_of_use, name="terms_of_use"),

    path('stats/', views.stats_view, name="stats"),

    path('testing_session', views.testing_session, name="testing_session"),
    path('health_check', views.session_health_check, name='health_check'),
    path('privacy', views.privacy_statement, name='privacy_statement')
]
