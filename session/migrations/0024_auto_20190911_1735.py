# Generated by Django 2.2.4 on 2019-09-11 14:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('session', '0023_auto_20190911_1144'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='session',
            name='_previously_tested_parameters',
            field=models.TextField(default='{}', max_length=1000000),
        ),
    ]
