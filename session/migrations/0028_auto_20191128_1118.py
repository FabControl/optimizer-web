# Generated by Django 2.2.4 on 2019-11-28 09:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0027_auto_20191014_1051'),
    ]

    operations = [
        migrations.RenameField(
            model_name='settings',
            old_name='temperature_extruder',
            new_name='_temperature_extruder',
        ),
    ]