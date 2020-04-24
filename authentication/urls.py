from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import PasswordSetForm
from . import views

urlpatterns = [
    # ex: /authentication/
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='signout'),
    path('signup/', views.user_signup, name='signup'),
    path('onboarding_toggler/', views.onboarding_toggler, name='onboarding_toggler'),
    path('onboarding/', views.onboarding_disable, name='disable_onboarding'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
                template_name='authentication/password_reset_done.html'),
            name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
                form_class=PasswordSetForm,
                post_reset_login=True, # comment this line to disable automatic login
                                    # after password change
                template_name='authentication/password_reset_confirm.html'),
            name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(
                template_name='authentication/password_reset_complete.html'),
            name='password_reset_complete'),
    path('password_change/', views.PasswordChangeView.as_view(),
            name='password_change'),
    path('activate_account/<uidb64>/<token>/', views.activate_account, name='activate_account'),
    path('account_legal_info/', views.legal_information_view, name='account_legal_info'),
    ]
