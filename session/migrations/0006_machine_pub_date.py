# Generated by Django 2.2.2 on 2019-07-18 07:34

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0005_session_material'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='pub_date',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now),
        ),
    ]
