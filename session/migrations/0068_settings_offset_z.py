# Generated by Django 2.2.4 on 2020-07-30 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0067_auto_20200622_1616'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='offset_z',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=3),
        ),
    ]
