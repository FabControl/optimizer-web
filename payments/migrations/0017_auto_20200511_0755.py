# Generated by Django 2.2.4 on 2020-05-11 04:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import payments.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payments', '0016_auto_20200507_0959'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('paid_till', models.DateTimeField(auto_now_add=True)),
                ('stripe_id', models.CharField(editable=False, max_length=32)),
                ('state', models.CharField(choices=[('active', 'Active'), ('incomplete', 'First payment pending'), ('incomplete_expired', 'First payment expired'), ('past_due', 'Charge failed'), ('failure_notified', 'Failure notified'), ('canceled', 'Cancelled')], default='incomplete', editable=False, max_length=32)),
                ('payment_plan', models.ForeignKey(editable=False, on_delete=models.SET(payments.models.get_sentinel_plan), to='payments.Plan')),
                ('user', models.ForeignKey(editable=False, on_delete=models.SET(payments.models.get_sentinel_user), to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='invoice',
            name='_subscription',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paid_invoice', to='payments.Subscription'),
        ),
    ]