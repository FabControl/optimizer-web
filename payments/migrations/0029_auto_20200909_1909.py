# Generated by Django 2.2.4 on 2020-09-09 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0028_filter_subscriptions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='stripe_id',
            field=models.CharField(editable=False, max_length=32, unique=True),
        ),
    ]
