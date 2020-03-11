# Generated by Django 2.2.4 on 2020-03-11 15:17

from django.db import migrations
import re


def prusa_footer_replacement(app):
    Machine = app.get_model('session', 'Machine')

    for machine in Machine.objects.all():
        if 'prusa' in machine.model.lower():
            machine.gcode_footer = re.sub(r'G28(?! W)', 'G28 W', machine.gcode_footer)
            machine.save()


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0037_set_session_performer'),
    ]

    operations = [
             migrations.RunPython(prusa_footer_replacement)
    ]
