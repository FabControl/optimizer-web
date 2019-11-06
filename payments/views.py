from datetime import datetime
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from .models import Plan

# Create your views here.


def plans(request):
    if request.method == "POST":
        if "Yearbutton" in request.POST:
            request.user.renew_subscription(mode="year")
            messages.success(request, "Your subscription has extended by a year")
        elif "Monthbutton" in request.POST:
            request.user.renew_subscription(mode="month")
            messages.success(request, "Your subscription has extended by a month")
        elif "Weekbutton" in request.POST:
            request.user.renew_subscription(mode="week")
            messages.success(request, "Your subscription has extended by a week")
        elif "Corebutton" in request.POST:
            request.user.expire()
            messages.info(request, "You are now using Core subscription")
        return redirect('dashboard')

    else:
        plans = Plan.objects.filter(type='premium').order_by('price')

        days_remaining = request.user.subscription_expiration - timezone.now()

        context = {'plans': plans,
                   'expiration': days_remaining.days + 1,
                   'core': Plan.objects.get(name='Core')}
        return render(request, 'payments/plans.html', context)
