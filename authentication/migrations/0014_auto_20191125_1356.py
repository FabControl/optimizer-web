# Generated by Django 2.2.4 on 2019-11-25 11:56

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0013_auto_20191115_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='subscription_expiration',
            field=models.DateTimeField(default=datetime.datetime(2019, 11, 24, 11, 56, 13, 624931, tzinfo=utc)),
        ),
    ]
