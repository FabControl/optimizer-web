from django.urls import path

from . import views

urlpatterns = [
    path('plans/', views.PaymentPlansView.as_view(), name='plans'),
    path('checkout_completed/<checkout_id>', views.checkout_completed, name='checkout_completed'),
    path('checkout_cancelled/<checkout_id>', views.checkout_cancelled, name='checkout_cancelled'),
    path('handle_stripe_event/', views.handle_stripe_event, name='handle_stripe_event'),
    path('invoices/', views.InvoicesView.as_view(), name='invoices'),
    path('invoices/pdf/<invoice_id>', views.InvoicePdfDownload.as_view(), name='download_invoice'),
    path('invoices/html/<invoice_id>', views.InvoiceHtmlView.as_view(), name='view_invoice'),
]
