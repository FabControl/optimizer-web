from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.views.generic.list import ListView
from .models import User, Affiliate

# Register your models here.
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (None, {'fields': ('email', 'password',)}),
        ('Subscription', {'fields': ('_plan', 
                                    'subscription_expiration', 
                                    'custom_payments', 
                                    'manager_of_corporation', 
                                    'member_of_corporation')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Company info', {'fields': ('company_name',
                                        'company_registration_number',
                                        'company_vat_number',
                                        'company_country',
                                        'company_legal_address')}),
        ('Permissions', {'fields': ('is_active', 'can_access_investor_dashboard', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        ('Onboarding', {'fields': ('onboarding', '_onboarding_sections',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
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



class UserInformationReferenceView(ListView):
    model = User
    paginate_by = 100
    template_name = 'admin/user_references_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.exclude(information_reference='')
        queryset = queryset.values('email', 'date_joined', 'information_reference')
        queryset = queryset.order_by(self.request.GET.get('order_by', '-date_joined'))
        return queryset

    def render_to_response(self, context, *args, **kwargs):
        context['ordering'] = self.request.GET.get('order_by', '-date_joined')
        return super().render_to_response(context, *args, **kwargs)


admin.site.register_custom_view('user_references',
                                UserInformationReferenceView.as_view())
