from django.contrib import admin
from .models import Plan, Checkout, TaxationCountry

# Register your models here.
admin.site.register(TaxationCountry)

def mark_checkout_paid(modeladmin, request, queryset):
    for c in queryset:
        c.confirm_payment()

mark_checkout_paid.short_description = 'Mark checkouts paid'

@admin.register(Checkout)
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

@admin.register(Plan)
class PlanModelAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request):
        return False


