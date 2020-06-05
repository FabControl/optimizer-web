from django.urls import path

from . import views

urlpatterns = [
    path('plans/', views.PaymentPlansView.as_view(), name='plans'),
    path('plans/<section>/', views.PaymentPlansView.as_view(), name='plans_section'),
    path('checkout_completed/<checkout_id>', views.checkout_completed, name='checkout_completed'),
    path('checkout_cancelled/<checkout_id>', views.checkout_cancelled, name='checkout_cancelled'),
    path('cancel_subscription/<subscription_id>', views.cancel_subscription, name='cancel_subscription'),
    path('update_payment_method/<subscription_id>', views.update_payment_method, name='update_payment_method'),
    path('card_details_updated/<checkout_id>', views.card_details_updated, name='card_details_updated'),
    path('card_details_unchanged/<checkout_id>', views.card_details_unchanged, name='card_details_unchanged'),
    path('handle_stripe_event/', views.handle_stripe_event, name='handle_stripe_event'),
    path('invoices/', views.InvoicesView.as_view(), name='invoices'),
    path('invoices/pdf/<invoice_id>', views.InvoicePdfDownload.as_view(), name='download_invoice'),
    path('invoices/html/<invoice_id>', views.InvoiceHtmlView.as_view(), name='view_invoice'),
    path('redeem_voucher', views.redeem_voucher, name='redeem_voucher'),
]
