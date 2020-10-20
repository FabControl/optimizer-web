from django.contrib import admin
from . import models as payment_models
from .forms import CurrencyAdminForm, PartnerAdminForm, VoucherAdminForm
from django.urls import path, reverse
from django.shortcuts import redirect
from django import forms
from django.contrib import messages
from django.utils import safestring
from django.db import models
from django.utils import safestring, timezone
from django.http import StreamingHttpResponse
import csv
from datetime import timedelta
from django.contrib.auth import get_user_model
from collections import Counter
from django.core.paginator import Paginator

# Register your models here.
admin.site.register(payment_models.TaxationCountry)


@admin.register(payment_models.Corporation)
class CorporationModelAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user_count', )


def mark_checkout_paid(modeladmin, request, queryset):
    for c in queryset:
        c.confirm_payment()


mark_checkout_paid.short_description = 'Mark checkouts paid'


@admin.register(payment_models.Checkout)
class CheckoutModelAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'payment_plan', 'current_state', 'stripe_id')
    sortable_by = ('created', 'user', 'payment_plan', 'current_state')
    date_hierarchy = 'created'

    actions = [mark_checkout_paid]
    list_display_links = None

    def has_add_permission(self, request):
        return False

    def current_state(self, c):
        if c.is_paid:
            return 'paid'
        elif c.is_cancelled:
            return 'cancelled'
        elif c.is_expired:
            return 'expired'
        return 'in progress'


@admin.register(payment_models.Plan)
class PlanModelAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(payment_models.Subscription)
class SubscriptionModelAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'payment_plan', 'state', 'stripe_id')
    sortable_by = ('created', 'user', 'payment_plan', 'state', 'stripe_id')
    date_hierarchy = 'created'

    list_display_links = None

    def has_delete_permission(self, request):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(payment_models.Currency)
class CurrencyModelAdmin(admin.ModelAdmin):
    form = CurrencyAdminForm

    def has_delete_permission(self, request, obj=None):
        return False


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


@admin.register(payment_models.Partner)
class PartnerModelAdmin(admin.ModelAdmin):
    form = PartnerAdminForm
    list_display = ('name', 'voucher_prefix', 'voucher_count', 'stats')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(_voucher_count=models.Count('voucher'))
        return queryset

    def voucher_count(self, instance):
        return instance._voucher_count

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        try:
            partner = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            pass
        else:
            voucher_form = VoucherAdminForm(initial=dict(partner=partner))

            voucher_form.fields['partner'].widget = forms.HiddenInput()
            extra_context['voucher_form'] = voucher_form
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        extra_urls = [
                path('voucher/create/',
                        self.admin_site.admin_view(self.create_voucher),
                        name='create_voucher'),
                path('<object_id>/stats/',
                        self.admin_site.admin_view(self.get_stats),
                        name='partner_stats'),
                ]

        return extra_urls + urls

    def create_voucher(self, request):
        if request.method == 'POST':
            count = int(request.POST.get('voucher_count', '1'))
            form = VoucherAdminForm(request.POST)
            if form.is_valid():
                voucher = form.save()
                partner = voucher.partner

                if count > 1:
                    for i in range(count - 1):
                        post = { k:v for k,v in request.POST.items() }
                        post['number'] = VoucherAdminForm.generate_new_number(partner)
                        form = VoucherAdminForm(post)
                        voucher = form.save()
            else:
                errors = '<br>'.join('<br>'.join(x) for x in form.errors.values())
                messages.error(request, safestring.mark_safe(errors))

        return redirect(reverse('admin:payments_partner_change', kwargs=dict(object_id=form.cleaned_data['partner'].pk)))

    def stats(self, instance):
        return safestring.mark_safe('<a href="{}" target="blank">Download</a>'.format(reverse('admin:partner_stats', args=[instance.pk])))


    def _active_client(self, user, partner):
        # should always contain at least one row
        # Ordered with latest first
        redeemed = payment_models.RedeemedVoucher.objects.filter(user=user).order_by('-date_redeemed')
        # latest used voucher was deleted - no idea, who was partner
        if redeemed[0].voucher is None:
            return False
        # user once was client of partner, but no more
        if redeemed[0].voucher.partner != partner:
            return False
        for i in range(len(redeemed)):
            if redeemed[i].voucher is None or redeemed[i].voucher.partner != partner:
                break
            user.client_of_selected_partner_since = redeemed[i].date_redeemed

        payments = list(user.checkout_set
                                    .filter(created__gt=user.client_of_selected_partner_since, is_paid=True)
                                    .annotate(amount_paid=models.F('payment_plan__price')*models.F('payment_plan__currency__conversion_rate')*0.971-0.3)
                                    .values_list('created', 'amount_paid'))

        subscriptions = (user.subscription_set
                                    .filter(created__gt=user.client_of_selected_partner_since)
                                    .annotate(amount_paid=models.F('payment_plan__price')*models.F('payment_plan__currency__conversion_rate')*0.971-0.3)
                                    .values_list('created', 'amount_paid', 'paid_till', 'payment_plan__interval'))

        for created, amount, paid_till, interval in subscriptions:
            payment_date = paid_till - payment_models.Plan.timedelta_interval[interval]
            while payment_date >= created:
                payments.append((payment_date, amount))
                payment_date = payment_date - payment_models.Plan.timedelta_interval[interval]

        # sort ascending by payment date
        payments.sort(key=lambda x: x[0])
        user.received_subscription_payments = payments

        return True


    def generate_stats(self, partner, now):
        client_keys = partner.voucher_set.annotate(models.Count('redeemed_by')).filter(redeemed_by__count__gt=0).values_list('redeemed_by').distinct()

        clients = [c for c in get_user_model().objects.filter(pk__in=client_keys) if self._active_client(c, partner)]

        month_prev = now.month - 1
        year_prev = now.year
        if month_prev < 1:
            month_prev += 12
            year_prev -= 1

        last_30 = now - timedelta(days=30)
        last_60 = now - timedelta(days=60)
        last_90 = now - timedelta(days=90)

        yield [partner.name, now]

        yield ['Category', f'Last month({year_prev}-{month_prev})', 'Last 30 days', 'Last 60 days', 'Last 90 days', 'Total']
        yield ['New clients',
                len(tuple(c for c in clients if c.client_of_selected_partner_since.month == month_prev and c.client_of_selected_partner_since.year == year_prev)),
                len(tuple(c for c in clients if c.client_of_selected_partner_since > last_30)),
                len(tuple(c for c in clients if c.client_of_selected_partner_since > last_60)),
                len(tuple(c for c in clients if c.client_of_selected_partner_since > last_90)),
                len(clients)]
        yield ['New accounts',
                len(tuple(c for c in clients if c.date_joined.month == month_prev and c.date_joined.year == year_prev)),
                len(tuple(c for c in clients if c.date_joined > last_30)),
                len(tuple(c for c in clients if c.date_joined > last_60)),
                len(tuple(c for c in clients if c.date_joined > last_90)),
                len(clients)]

        payments_total = [c.received_subscription_payments for c in clients if len(c.received_subscription_payments) > 0]
        payments_90 = [c for c in payments_total if any(x[0] > last_90 for x in c)]
        payments_60 = [c for c in payments_90 if any(x[0] > last_60 for x in c)]
        payments_30 = [c for c in payments_60 if any(x[0] > last_30 for x in c)]
        payments_month = [c for c in payments_60 if any(x[0].month == month_prev and x[0].year == year_prev for x in c)]

        yield ['Paying clients',
                len(payments_month),
                len(payments_30),
                len(payments_60),
                len(payments_90),
                len(payments_total)
                ]

        yield ['Income',
                sum(p[1] for c in payments_month for p in c if p[0].month == month_prev and p[0].year == year_prev),
                sum(p[1] for c in payments_30 for p in c if p[0] > last_30),
                sum(p[1] for c in payments_60 for p in c if p[0] > last_60),
                sum(p[1] for c in payments_90 for p in c if p[0] > last_90),
                sum(p[1] for c in payments_total for p in c),
                ]

        del payments_total, payments_90, payments_60, payments_30, payments_month


        sessions = [s for u in clients for s in u.session_set.filter(pub_date__gt=u.client_of_selected_partner_since).values_list('pub_date', 'material__name', 'machine__model', 'buildplate')]
        column_names = ('Materials by session', '3D Printers by session', 'Build plate coating/material by session')
        session_count = len(sessions)

        yield ['Testing sessions',
                len(tuple(s for s in sessions if s[0].month == month_prev and s[0].year == year_prev)),
                len(tuple(s for s in sessions if s[0] > last_30)),
                len(tuple(s for s in sessions if s[0] > last_60)),
                len(tuple(s for s in sessions if s[0] > last_90)),
                session_count]

        for i in range(len(column_names)):
            yield [' ']
            yield [column_names[i]]

            column = i + 1
            items_total = Counter(x[column] for x in sessions)
            items_month = Counter(sessions[x][column] for x in range(session_count) if sessions[x][0].month == month_prev and sessions[x][0].year == year_prev)
            items_30 = Counter(sessions[x][column] for x in range(session_count) if sessions[x][0] > last_30)
            items_60 = Counter(sessions[x][column] for x in range(session_count) if sessions[x][0] > last_60)
            items_90 = Counter(sessions[x][column] for x in range(session_count) if sessions[x][0] > last_90)

            for item in items_total:
                yield [item,
                        items_month[item],
                        items_30[item],
                        items_60[item],
                        items_90[item],
                        items_total[item]]


        del sessions

        yield [' ']
        yield ['Materials by user']
        materials = [m for u in clients for m in u.material_set.values_list('pub_date', 'name')]
        material_count = len(materials)
        items_total = Counter(x[1] for x in materials)
        items_month = Counter(materials[x][1] for x in range(material_count) if materials[x][0].month == month_prev and materials[x][0].year == year_prev)
        items_30 = Counter(materials[x][1] for x in range(material_count) if materials[x][0] > last_30)
        items_60 = Counter(materials[x][1] for x in range(material_count) if materials[x][0] > last_60)
        items_90 = Counter(materials[x][1] for x in range(material_count) if materials[x][0] > last_90)

        for item in items_total:
            yield [item,
                    items_month[item],
                    items_30[item],
                    items_60[item],
                    items_90[item],
                    items_total[item]]

        del materials

        yield [' ']
        yield ['3D printers by user']
        machines = [m for u in clients for m in u.machine_set.values_list('pub_date', 'model')]
        machine_count = len(machines)
        items_total = Counter(x[1] for x in machines)
        items_month = Counter(machines[x][1] for x in range(machine_count) if machines[x][0].month == month_prev and machines[x][0].year == year_prev)
        items_30 = Counter(machines[x][1] for x in range(machine_count) if machines[x][0] > last_30)
        items_60 = Counter(machines[x][1] for x in range(machine_count) if machines[x][0] > last_60)
        items_90 = Counter(machines[x][1] for x in range(machine_count) if machines[x][0] > last_90)

        for item in items_total:
            yield [item,
                    items_month[item],
                    items_30[item],
                    items_60[item],
                    items_90[item],
                    items_total[item]]

        del machines


        yield [' ']
        yield ['Vouchers']
        yield ['Code', 'Bonus days', 'Valid till', 'Max uses allowed', 'Used by']

        vouchers = (partner.voucher_set
                        .annotate(code=models.functions.Concat(models.Value(f'{partner.voucher_prefix}-'), 'number'),
                                  used_by=models.Count('redeemed_by'))
                        .order_by('-used_by')
                        .values_list('code', 'bonus_days', 'valid_till', 'max_uses', 'used_by'))
        for v in vouchers:
            yield v


        yield [' ']
        yield ['End of stats file']



    def get_stats(self, request, object_id):
        partner = payment_models.Partner.objects.get(pk=object_id)

        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        now = timezone.now()

        response = StreamingHttpResponse((writer.writerow(row) for row in self.generate_stats(partner, now)),
                                                 content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{partner.voucher_prefix}_stats_{now:%Y-%m-%d_%H-%M-%S}.csv"'
        return response


@admin.register(payment_models.Voucher)
class VoucherModelAdmin(admin.ModelAdmin):
    form = VoucherAdminForm
    readonly_fields = ('partner',)
    list_display = ('__str__', 'partner', 'bonus_days', 'valid_till', 'used_by')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['ordering'] = request.GET.get('redeemer_order_by', '-date_redeemed')
        redeemers = (payment_models.RedeemedVoucher.objects.filter(voucher=object_id)
                                            .annotate(user_email=models.F('user__email'),
                                                      user_plan=models.F('user___plan'),
                                                      subscription_expiration=models.F('user__subscription_expiration'))
                                            .values('user_email', 
                                                    'date_redeemed',
                                                    'user_plan',
                                                    'subscription_expiration')
                                            .order_by(extra_context['ordering'])
                            )

        redeemer_paginator = Paginator(redeemers, 100)
        extra_context['redeemers'] = redeemer_paginator.get_page(request.GET.get('redeemer_page'))
        return super().change_view(request, object_id, form_url, extra_context)


    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(_used_count=models.Count('redeemed_by'))
        return queryset

    def used_by(self, instance):
        return instance._used_count

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()

        allowed_urls = ('payments_voucher_delete', 'payments_voucher_change', 'payments_voucher_autocomplete', 'payments_voucher_changelist')
        return [x for x in urls if x.name in allowed_urls]
