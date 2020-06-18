# Generated by Django 2.2.4 on 2020-06-15 16:13

from django.db import migrations


def assign_limited(app, schema_editor):
    db_alias = schema_editor.connection.alias

    SessionMode = app.get_model('session', 'SessionMode')

    for m in SessionMode.objects.using(db_alias).filter(_plan_availability__contains='basic'):
        m._plan_availability = m._plan_availability[:-1] + ", 'limited']"
        m.save()


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0063_adjust_session_numbers'),
    ]

    operations = [
        migrations.RunPython(assign_limited)
    ]
