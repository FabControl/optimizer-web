# Generated by Django 2.2.4 on 2020-04-16 14:01

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0020_auto_20200330_2110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='subscription_expiration',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 10, 0, 0, tzinfo=utc)),
        ),
    ]
