# Generated by Django 2.2.4 on 2019-11-06 12:24

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0010_auto_20191106_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='subscription_expiration',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
