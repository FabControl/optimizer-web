from django.conf import settings
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.views.generic.edit import BaseFormView
from django.views.generic import ListView, TemplateView
from .models import Plan, Checkout, Invoice, TaxationCountry
from django.urls import reverse
from .forms import PaymentPlanForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponse
import stripe
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django_weasyprint.views import WeasyTemplateResponseMixin
from decimal import Decimal
from django.template.loader import get_template

# Create your views here.

stripe.api_key = settings.STRIPE_API_KEY

class PaymentPlansView(BaseFormView):
    form_class = PaymentPlanForm

    def get(self, request, *a, **k):
        plans = Plan.objects.filter(type='premium').order_by('price')

        context = {'plans': plans,
                # Should work correctly if database contains
                #   only one instance of Plan with type 'basic'
                'core': Plan.objects.get(type='basic')}
        if request.user.is_authenticated:
            days_remaining = request.user.subscription_expiration - timezone.now()
            context['expiration'] = days_remaining.days + 1

        return render(request, 'payments/plans.html', context)

    @method_decorator(login_required)
    def post(self, request, *a, **k):
        form = self.get_form()
        if form.is_valid():
            checkout_id = form.create_invoice(request.user, request)
            return render(request,
                          'payments/checkout.html',
                          {'checkout_id': checkout_id,
                              'stripe_public_key': settings.STRIPE_PUBLIC_KEY })
        else:
            return self.get(request)


def _decorate_checkout(method):
    @login_required
    def _method(request, checkout_id):
        checkout = get_object_or_404(Checkout, pk=checkout_id)

        if checkout.user != request.user:
            raise Http404()

        if checkout.is_expired:
            messages.error(request, 'Your checkout session has expired')
        else:
            method(request, checkout)

        if checkout.is_cancelled:
            messages.error(request, 'Your checkout was cancelled')

        return redirect(reverse('plans'))

    return _method


@_decorate_checkout
def checkout_completed(request, checkout):
    if checkout.is_paid:
        messages.success(request,
                        'Your full access was extended for {0.days} days'.format(checkout.payment_plan.subscription_period))

    # this should never happen in real life with webhooks, but better safe than sorry
    else:
        messages.warning(request,
                        'We haven\'t received your payment yet. Please check after few minutes')


@_decorate_checkout
def checkout_cancelled(request, checkout):
    if not checkout.is_paid and not checkout.is_expired:
        checkout.cancel()


@csrf_exempt
def handle_stripe_event(request):
    payload = request.body
    try:
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    except KeyError:
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(payload,
                                               sig_header,
                                               settings.STRIPE_ENDPOINT_SECRET)
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    event_type = event['type']
    event_object = event['data']['object']

    # handlers start here
    if event_type == 'checkout.session.completed':
        checkout = Checkout.objects.get(pk=event_object['client_reference_id'])
        checkout.confirm_payment()

    elif event_type in ('plan.created','plan.updated','plan.deleted'):
        if event_object['product'] == settings.STRIPE_SUBSCRIPTION_PRODUCT_ID:
            if event_type == 'plan.deleted':
                try:
                    Plan.objects.get(stripe_plan_id=event_object['id']).delete()
                except Plan.DoesNotExist:
                    pass

            else:
                plan = Plan.from_stripe(event_object)
                if plan.has_changed:
                    plan.save()

    else:
        # if event not handled by server
        return HttpResponse(status=400)

    return HttpResponse(status=200)


class InvoicesView(LoginRequiredMixin, ListView):
    template_name = "payments/invoices.html"
    context_object_name = 'invoices'

    def get_queryset(self):
        if not self.request.user.can_collect_invoices:
            raise Http404()
        return Invoice.objects.filter(user=self.request.user)


class InvoiceHtmlView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/invoice_pdf.html'

    def get_context_data(self, **kwargs):
        query = dict(pk=self.kwargs['invoice_id'])
        if not self.request.user.is_staff:
            if not self.request.user.can_collect_invoices:
                raise Http404()
            query['user'] = self.request.user

        context = super().get_context_data(**kwargs)

        invoice = get_object_or_404(Invoice, **query)
        context['invoice'] = invoice

        user = invoice.user
        country = TaxationCountry.objects.filter(name=user.company_country)[0]
        if country.exclude_vat and user.company_vat_number != '':
            tax = Decimal('0.00')
            context['tax_name'] = 'VAT tax for invoices between companies in European Union (reverse charge)'
        else:
            tax = invoice.payment_plan.price * country.vat_charge / 100
            context['tax_name'] = 'VAT {}%'.format(country.vat_charge)
        context['tax_amount'] = tax
        context['calculated_price'] = invoice.payment_plan.price - tax
        # service provider
        context['provider_name'] = settings.PAYMENTS_COMPANY_NAME
        context['provider_reg_number'] = settings.PAYMENTS_COMPANY_REG_NUMBER
        context['provider_vat'] = settings.PAYMENTS_COMPANY_VAT_NUMBER
        context['provider_address'] = settings.PAYMENTS_COMPANY_ADDRESS
        context['provider_bank'] = settings.PAYMENTS_COMPANY_BANK
        context['provider_swift'] = settings.PAYMENTS_COMPANY_SWIFT
        context['provider_account'] = settings.PAYMENTS_COMPANY_ACCOUNT
        # client legal address split into line array
        address = [x.strip() for x in user.company_legal_address.split('\n') if x.strip() != '']
        address.append(country.long_name)
        context['client_address'] = address

        invoice.store_backup(get_template(self.template_name).render(context))
        return context


class InvoicePdfDownload(WeasyTemplateResponseMixin, InvoiceHtmlView):
    def get_pdf_filename(self):
        return Invoice.objects.get(pk=self.kwargs['invoice_id']).invoice_number + '.pdf'


