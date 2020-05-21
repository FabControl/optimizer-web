# Generated by Django 2.2.4 on 2020-01-29 18:28

from django.db import migrations


def assign_modes(app, schema_editor):
    db_alias = schema_editor.connection.alias
    SessionMode = app.get_model('session', 'SessionMode')
    Session = app.get_model('session', 'Session')
    advanced = SessionMode.objects.using(db_alias).get(name='Advanced')
    for s in Session.objects.using(db_alias).all():
        s.mode = advanced
        s.save()


class Migration(migrations.Migration):
    dependencies = [
        ('session', '0049_manual_add_test_junctions'),
    ]

    operations = [
        migrations.RunPython(assign_modes)
    ]
