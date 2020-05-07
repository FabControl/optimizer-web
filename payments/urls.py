from django.urls import path

from . import views

urlpatterns = [
    path('plans/', views.PaymentPlansView.as_view(), name='plans'),
    path('plans/update_plan_changes/', views.store_plan_changes, name='plan_changes_hook'),
    path('checkout_completed/<checkout_id>', views.checkout_completed, name='checkout_completed'),
    path('checkout_cancelled/<checkout_id>', views.checkout_cancelled, name='checkout_cancelled'),
    path('confirm_payment/', views.confirm_payment, name='confirm_payment'),
    path('invoices/', views.InvoicesView.as_view(), name='invoices'),
    path('invoices/pdf/<checkout_id>', views.InvoicePdfDownload.as_view(), name='download_invoice'),
    path('invoices/html/<checkout_id>', views.InvoiceHtmlView.as_view(), name='view_invoice'),
]
