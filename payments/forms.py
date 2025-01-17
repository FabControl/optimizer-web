from django import forms
from .models import Checkout, Plan, Currency, Partner, Voucher
import stripe
from django.http.request import HttpRequest
from django.urls import reverse, reverse_lazy
from .countries import codes_iso3166
from django.utils.safestring import mark_safe
from base64 import b64encode
from django.contrib.admin.widgets import AdminDateWidget
import datetime
from uuid import uuid4
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from crispy_forms.bootstrap import FieldWithButtons
from django.utils.translation import gettext_lazy as _
from PIL import Image
from io import BytesIO


class PaymentPlanForm(forms.Form):
    plan_id = forms.IntegerField()

    class Meta:
        fields = ['plan_id']

    def create_invoice(self, user, request:HttpRequest):
        base_url = 'https://' + request.META['HTTP_HOST']
        plan = Plan.objects.get(pk=self.cleaned_data.get('plan_id'))
        checkout = Checkout(user=user, payment_plan=plan)

        if plan.is_one_time:
            items={'line_items': [{ 'name': '3DOptimizer full access {0.name}'.format(plan),
                                    'description': 'Full access to all 3DOptimizer features',
                                    'amount': int(plan.price * 100), # price in cents
                                    'currency': plan.currency.name.lower(),
                                    'quantity': 1}]}
        else:
            items={'subscription_data':{ 'items': [{'plan': plan.stripe_plan_id}],
                                        'metadata': {'internal_reference': checkout.pk}}}

        bill = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=user.email,
                client_reference_id=checkout.checkout_id,
                success_url=base_url + reverse('checkout_completed', args=[checkout.checkout_id]),
                cancel_url=base_url + reverse('checkout_cancelled', args=[checkout.checkout_id]),
                **items)

        if plan.is_one_time:
            checkout.stripe_id = bill['payment_intent']
        else:
            checkout.stripe_id = bill['id']
        checkout.save()

        return bill['id']


class VoucherRedeemForm(forms.Form):
    voucher = forms.CharField(max_length=60,
                            label=_('Redeem a voucher '))

    helper = FormHelper()
    helper.form_action = reverse_lazy('redeem_voucher')
    helper.layout = Layout(FieldWithButtons('voucher',
                        Submit('submit', _('Redeem'), css_class='btn-primary'),
                        style='text-align: center !important;'))

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields['voucher'].widget.attrs['placeholder'] = _('voucher code')

    def clean(self):
        cleaned_data = super().clean()

        ids = cleaned_data['voucher'].split('-')
        try:
            partner = Partner.objects.get(pk=ids[0])
        except Partner.DoesNotExist:
            raise forms.ValidationError('Invalid voucher prefix')
        else:
            try:
                voucher = partner.voucher_set.get(number='-'.join(ids[1:]))
            except Voucher.DoesNotExist:
                raise forms.ValidationError('Invalid voucher number')
            else:
                if voucher.valid_till < datetime.date.today():
                    raise forms.ValidationError('Voucher expired')
                if voucher.max_uses <= voucher.redeemed_by.count():
                    raise forms.ValidationError('Voucher used max times')

                cleaned_data['voucher_instance'] = voucher

        return cleaned_data


class CurrencyAdminForm(forms.ModelForm):
    countries = forms.MultipleChoiceField(choices=codes_iso3166, widget=forms.widgets.CheckboxSelectMultiple)
    class Meta:
        model = Currency
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            if 'initial' not in kwargs or kwargs['initial'] is None:
                kwargs['initial'] = {}

            kwargs['initial']['countries'] = kwargs['instance'].countries

        return super().__init__(*args, **kwargs)

    def save(self, commit=True):
        result = super().save(commit=False)
        result.countries = self.cleaned_data['countries']
        if commit:
            result.save()
        return result


class PartnerAdminForm(forms.ModelForm):
    logo_image = forms.FileField(help_text='800x80px. Larger images will be scaled down to fit.')
    banner_image = forms.FileField(help_text='728x130px. Larger images will be scaled down to fit.', required=False)
    clear_banner = forms.BooleanField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Partner
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)

        if instance is not None:
            if 'initial' not in kwargs or kwargs['initial'] is None:
                kwargs['initial'] = {}

            kwargs['initial']['logo_image'] = 'logo.png'
            kwargs['initial']['logo_image'] = 'banner.png'

        super().__init__(*args, **kwargs)

        self.fields['voucher_prefix'].validators.append(self._validate_prefix)

        if instance is not None:
            self.fields['logo_image'].help_text += mark_safe('<br><img src="data:image/png;base64,{}"/>'.format(instance.logo))
            if instance.banner != '':
                self.fields['banner_image'].help_text += mark_safe('<br><img src="data:image/png;base64,{}"/>'.format(instance.banner))
                self.fields['clear_banner'].widget = forms.CheckboxInput()

            # self.fields['voucher_prefix'].widget.attrs['disabled'] = ''  # Had to be removed in order to be able modify partners from AdminView
    def _validate_prefix(self, prefix):
        if '-' in prefix:
            raise forms.ValidationError('Prefix must not contain a "-"')

    def save(self, commit=True):
        instance = super().save(commit=False)

        if 'logo_image' in self.files:
            logo_image = Image.open(self.files['logo_image'])
            scale = max((logo_image.width / 800.0, logo_image.height / 80.0))
            if scale > 1.0:
                logo_image = logo_image.resize((int(logo_image.width / scale), int(logo_image.height / scale)))
            logo_bytes = BytesIO()
            logo_image.save(logo_bytes, format='PNG')
            instance.logo = b64encode(logo_bytes.getvalue()).decode('utf-8')

        clear_banner = 'clear_banner' in self.cleaned_data and self.cleaned_data['clear_banner']

        if 'banner_image' in self.files and not clear_banner:
            banner_image = Image.open(self.files['banner_image'])
            scale = max((banner_image.width / 728.0, banner_image.height / 130.0))
            if scale > 1.0:
                banner_image = banner_image.resize((int(banner_image.width / scale), int(banner_image.height / scale)))
            banner_bytes = BytesIO()
            banner_image.save(banner_bytes, format='PNG')
            instance.banner = b64encode(banner_bytes.getvalue()).decode('utf-8')

        elif clear_banner:
            instance.banner = ''

        if commit:
            instance.save()

        return instance


class VoucherAdminForm(forms.ModelForm):

    @classmethod
    def generate_new_number(cls, partner):
        voucher_set = partner.voucher_set.values('number')
        for i in range(100):
            code = ('-'.join(str(uuid4()).split('-')[1:3])).upper()
            if code not in voucher_set:
                return code

    class Meta:
        model = Voucher
        fields = '__all__'

    def __init__(self, *a, **k):
        if 'instance' not in k:
            initial = k.get('initial', {})
            if 'bonus_days' not in initial:
                initial['bonus_days'] = 14
            if 'max_uses' not in initial:
                initial['max_uses'] = 5
            if 'valid_till' not in initial:
                initial['valid_till'] = datetime.date.today() + datetime.timedelta(days=180)

            if 'partner' in initial:
                initial['number'] = self.generate_new_number(initial['partner'])

            k['initial'] = initial

        super().__init__(*a, **k)
        self.fields['valid_till'].help_text = 'YYYY-MM-DD'

    def clean(self):
        data = super().clean()
        try:
            partner = data['partner'] if self.instance is None else self.instance.partner
        except Partner.DoesNotExist:
            partner = data['partner']
        similar_vouchers = partner.voucher_set.filter(number=data['number'])
        if similar_vouchers.count() > 0:
            if similar_vouchers.count() > 1 or similar_vouchers[0] != self.instance:
                raise forms.ValidationError('Voucher number "{}"already in use'.format(data['number']))

        return data
