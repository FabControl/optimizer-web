from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _
from .models import User, Affiliate

# Register your models here.
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (None, {'fields': ('email', 'password',)}),
        ('Subscription', {'fields': ('_plan', 'subscription_expiration', 'manager_of_corporation', 'member_of_corporation')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Company info'), {'fields': ('company_name',
                                        'company_registration_number',
                                        'company_vat_number',
                                        'company_country',
                                        'company_legal_address')}),
        (_('Permissions'), {'fields': ('is_active', 'can_access_investor_dashboard', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        ('Onboarding', {'fields': ('onboarding', '_onboarding_sections',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    actions = ['reset_onboarding', 'send_activation_email']

    def reset_onboarding(self, request, queryset):
        for user in queryset:
            user.onboarding_reset(request)

    reset_onboarding.short_description = "Reenable onboarding tour"

    def send_activation_email(self, request, queryset):
        for user in queryset:
            if not user.is_active:
                user.send_account_activation(request)

    send_activation_email.short_description = 'Resend activation email'

    list_display = ('email', 'first_name', 'last_name', 'plan', 'last_active', 'date_joined', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

@admin.register(Affiliate)
class AffiliatesAdmin(admin.ModelAdmin):
    list_display = ('email', 'sender', 'date_created', 'date_registered', 'receiver')

    def has_add_permission(self, request):
        return False
