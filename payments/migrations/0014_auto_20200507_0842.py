# Generated by Django 2.2.4 on 2020-05-07 05:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import payments.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payments', '0013_plan_stripe_plan_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='_one_time_payment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paid_invoice', to='payments.Checkout'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='date_paid',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoice',
            name='user',
            field=models.ForeignKey(editable=False, null=True, on_delete=models.SET(payments.models.get_sentinel_user), to=settings.AUTH_USER_MODEL),
        ),
    ]
