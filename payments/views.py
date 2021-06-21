from django.conf import settings
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.views.generic.edit import BaseFormView
from django.views.generic import ListView, TemplateView
from .models import Plan, Checkout, Invoice, TaxationCountry, Subscription, Currency, Corporation
from django.urls import reverse
from .forms import PaymentPlanForm, VoucherRedeemForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponse
import stripe
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django_weasyprint.views import WeasyTemplateResponseMixin
from decimal import Decimal
from django.template.loader import get_template
from Optimizer3D.middleware.GeoRestrictAccessMiddleware import geoRestrictExempt
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import models
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

# Create your views here.

stripe.api_key = settings.STRIPE_API_KEY

class PaymentPlansView(LoginRequiredMixin, BaseFormView):
    form_class = PaymentPlanForm

    def get(self, request, *a, **k):
        if request.user.is_authenticated:
            country = request.user.company_country
            show_plans = not request.user.custom_payments
        else:
            country = ''

        if show_plans:
            if country == '' and hasattr(request, 'geolocation'):
                country = request.geolocation['county']['code']

            currencies = []
            if country != '':
                currencies = Currency.objects.filter(_countries__contains=country)

            if len(currencies) < 1:
                currencies = Currency.objects.filter(name='USD')

            plans = Plan.objects.filter(type='premium', currency__in=currencies).order_by('price')
            for plan in plans:
                plan.banner_image = static('payments/images/' + ('week' if plan.interval is '' else plan.interval) + '.png')
                if plan.interval == 'month':
                    plan.popular_badge = True

            corporation_plans = Plan.objects.filter(type='corporate',
                                                    currency__in=currencies
                                                    ).order_by('price').annotate(
                                                            popular_badge=models.Case(
                                                                        models.When(max_users_allowed=5,
                                                                                    interval='year',
                                                                                    then=True),
                                                                        default=False,
                                                                        output_field=models.BooleanField()))


            context = {'plans': plans,
                        'voucher_form': VoucherRedeemForm(),
                       'corporation_plans': corporation_plans}

            context['section'] = self.kwargs.get('section', None)
            context['active_subscriptions'] = request.user.active_subscriptions
        else:
            context = {}

        days_remaining = request.user.subscription_expiration - timezone.now()
        context['expiration'] = days_remaining.days + 1

        return render(request, 'payments/plans.html', context)

    @method_decorator(login_required)
    def post(self, request, *a, **k):
        if request.user.custom_payments:
            return Http404()
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

        landing_url,kwargs,section = method(request, checkout)

        if checkout.is_cancelled:
            messages.error(request, _('Your checkout was cancelled'))

        return redirect(reverse(landing_url, kwargs=kwargs) + section)

    return _method


@_decorate_checkout
def checkout_completed(request, checkout):
    if checkout.is_expired:
        messages.error(request, _('Your session has expired'))
    elif checkout.is_paid:
        if checkout.payment_plan.is_one_time:
            days = checkout.payment_plan.subscription_period.days
            msg = ngettext('Your full access was extended for %(day)d day',
                            'Your full access was extended for %(day)d days', days) % {'day':days}
            messages.success(request, msg)
        else:
            messages.success(request, _('Subscription successful'))
            if checkout.payment_plan.type == 'corporate':
                return 'account_legal_info', dict(category='corporation'), '#corporation'

    # this should never happen in real life with webhooks, but better safe than sorry
    else:
        messages.warning(request,
                        _('We haven\'t received your payment yet. Please check after few minutes'))

    return 'plans',None,''


@_decorate_checkout
def checkout_cancelled(request, checkout):
    if checkout.is_expired:
        messages.error(request, _('Your session has expired'))
    elif not checkout.is_paid:
        checkout.cancel()
    return 'plans',None,''

@login_required
def update_payment_method(request, subscription_id):
    subscription = get_object_or_404(Subscription, pk=subscription_id, user=request.user)
    checkout = Checkout(user=subscription.user,
                        payment_plan=subscription.payment_plan)

    base_url = 'https://' + request.META['HTTP_HOST']
    stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_id)
    stripe_checkout = stripe.checkout.Session.create(
                        customer=stripe_subscription['customer'],
                        payment_method_types=['card'],
                        client_reference_id=checkout.checkout_id,
                        mode='setup',
                        setup_intent_data={
                            'metadata': {
                                'subscription_id': subscription.stripe_id}},
                            success_url=base_url + reverse('card_details_updated', args=[checkout.checkout_id]),
                            cancel_url=base_url + reverse('card_details_unchanged', args=[checkout.checkout_id]),
                            )

    checkout.stripe_id = stripe_checkout['id']
    checkout.save()

    return render(request,
                  'payments/checkout.html',
                  {'checkout_id': stripe_checkout['id'],
                      'stripe_public_key': settings.STRIPE_PUBLIC_KEY })


@_decorate_checkout
def card_details_updated(request, checkout):
    if checkout.is_paid:
        messages.success(request, _('Subscription payment method changed!'))
        # checkout is no longer required
        checkout.delete()

    # this should never happen in real life with webhooks, but better safe than sorry
    else:
        messages.error(request, _('Something went wrong. Please try again later.'))

    return 'account_legal_info', dict(category='subscription'), '#subscription'


@_decorate_checkout
def card_details_unchanged(request, checkout):
    # checkout is no longer required
    checkout.delete()
    return 'account_legal_info', dict(category='subscription'), '#subscription'


@login_required
def cancel_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, pk=subscription_id, user=request.user)
    # will not actually delete subscription, but mark it as cancelled
    data = stripe.Subscription.delete(subscription.stripe_id)
    Subscription.update_from_stripe(data)

    messages.success(request, _('Subscription cancelled'))
    return redirect(reverse('account_legal_info', kwargs=dict(category='subscription')) + '#subscription')


@geoRestrictExempt
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
        if event_object['mode'] == 'payment':
            # one-time payment
            checkout.confirm_payment()

        elif event_object['mode'] == 'subscription':
            # created new subscription
            subscription_args = dict(stripe_id=event_object['subscription'],
                                        payment_plan=checkout.payment_plan,
                                        user=checkout.user)
            try:
                subscription = Subscription.objects.get(**subscription_args)
            except Subscription.DoesNotExist:
                subscription = Subscription.objects.create(**subscription_args)

            if subscription.payment_plan.type == 'corporate':
                user = subscription.user
                if len(user.corporation_set.all()) < 1:
                    corp_name = user.company_name if user.company_name != '' else f"{user.first_name}'s corporation"
                    corp = Corporation.objects.create(owner=user,
                                                name=corp_name)
                    user.member_of_corporation = corp
                    user.manager_of_corporation = corp
                    user.save()

            checkout.stripe_id = event_object['subscription']
            checkout.is_paid = True
            checkout.save()

        elif event_object['mode'] == 'setup':
            # updated subscription payment method e.g. card
            intent = stripe.SetupIntent.retrieve(event_object['setup_intent'])
            stripe.Subscription.modify(
                        intent['metadata']['subscription_id'],
                        default_payment_method=intent['payment_method'])

            checkout.is_paid = True
            checkout.save()


    elif event_type in ('customer.subscription.created', 'customer.subscription.updated', 'customer.subscription.deleted'):
        if event_type == 'customer.subscription.created':
            # if user tried initial payment with insufficient funds this event will happen before checkout.completed
            try:
                Subscription.objects.get(stripe_id=event_object['id'])
            except Subscription.DoesNotExist:
                checkout = Checkout.objects.get(pk=event_object['metadata']['internal_reference'])
                Subscription.objects.create(stripe_id=event_object['id'],
                                            payment_plan=checkout.payment_plan,
                                            user=checkout.user)

        Subscription.update_from_stripe(event_object)

    elif event_type in ('plan.created','plan.updated','plan.deleted'):
        if event_object['product'] in (settings.STRIPE_BUSINESS_PRODUCT_ID, settings.STRIPE_SUBSCRIPTION_PRODUCT_ID):
            plan = Plan.from_stripe(event_object)
            if event_type == 'plan.deleted':
                plan.type = 'deleted'
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

@login_required
def redeem_voucher(request):
    if request.method == 'POST' and request.user.member_of_corporation is None and len(request.user.active_subscriptions) < 1:
        form = VoucherRedeemForm(request.POST)
        success = False
        if form.is_valid():
            voucher = form.cleaned_data['voucher_instance']
            success = voucher.use_voucher(request.user)


        if success:
            days = voucher.bonus_days
            msg = ngettext('Your full access was extended for %(day)d day',
                            'Your full access was extended for %(day)d days', days) % {'day':days}
            messages.success(request, msg)
        else:
            messages.error(request, _('Provided voucher code is not valid'))
    return redirect(reverse('plans'))
