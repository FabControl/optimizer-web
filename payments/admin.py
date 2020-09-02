from django.contrib import admin
from . import models as payment_models
from .forms import CurrencyAdminForm, PartnerAdminForm, VoucherAdminForm
from django.urls import path, reverse
from django.shortcuts import redirect
from django import forms
from django.contrib import messages
from django.utils import safestring

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


@admin.register(payment_models.Partner)
class PartnerModelAdmin(admin.ModelAdmin):
    form = PartnerAdminForm
    list_display = ('name', 'voucher_prefix')

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


@admin.register(payment_models.Voucher)
class VoucherModelAdmin(admin.ModelAdmin):
    form = VoucherAdminForm
    readonly_fields = ('partner',)

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()

        allowed_urls = ('payments_voucher_delete', 'payments_voucher_change', 'payments_voucher_autocomplete', 'payments_voucher_changelist')
        return [x for x in urls if x.name in allowed_urls]
