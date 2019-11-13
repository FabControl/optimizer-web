from django.urls import path

from . import views

urlpatterns = [
    path('plans/', views.PaymentPlansView.as_view(), name='plans'),
    path('checkout_completed/<checkout_id>', views.checkout_completed, name='checkout_completed'),
    path('checkout_cancelled/<checkout_id>', views.checkout_cancelled, name='checkout_cancelled'),
    path('confirm_payment/', views.confirm_payment, name='confirm_payment'),
]
