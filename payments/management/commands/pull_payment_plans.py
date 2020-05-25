from django.core.management.base import BaseCommand
import stripe
from django.conf import settings
from payments.models import Plan


stripe.api_key = settings.STRIPE_API_KEY

class Command(BaseCommand):
    help = 'Pulls payment plan data from Stripe and saves in database'
    requires_migrations_checks = True

    def handle(self, *args, **kwargs):
        # pull list of payment plans
        unsorted_simple_plans = stripe.Plan.list(product=settings.STRIPE_SUBSCRIPTION_PRODUCT_ID,
                                                limit=100)['data']

        unsorted_business_plans = stripe.Plan.list(product=settings.STRIPE_BUSINESS_PRODUCT_ID,
                                                limit=100)['data']

        stripe_plans = {x['id']:x for x in unsorted_business_plans + unsorted_simple_plans}

        for plan in Plan.objects.exclude(stripe_plan_id='').exclude(stripe_plan_id__in=stripe_plans.keys()):
            # remove no longer existing plans
            plan.type = 'deleted'
            plan.save()
            self.stdout.write(self.style.WARNING('Removed payment plan: ' + str(plan)))

        # update existing or create new
        for stripe_plan in stripe_plans.values():
            plan = Plan.from_stripe(stripe_plan)
            if plan.pk is None:
                msg = self.style.SUCCESS('Created new subscription plan: ' + str(plan))
            else:
                msg = self.style.WARNING('Altered subscription plan: ' + str(plan))
            if plan.has_changed:
                plan.save()
                self.stdout.write(msg)
