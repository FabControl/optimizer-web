# Generated by Django 2.2.4 on 2020-01-29 18:28

from django.db import migrations


def populate_testing_modes(app, schema_editor):
    db_alias = schema_editor.connection.alias

    SessionMode = app.get_model('session', 'SessionMode')

    SessionMode.objects.using(db_alias).create(name='Advanced',
                                               type='normal',
                                               plan_availability='premium')

    SessionMode.objects.using(db_alias).create(name='Guided',
                                               type='guided',
                                               plan_availability='premium')

    SessionMode.objects.using(db_alias).create(name='Core',
                                               type='guided',
                                               _included_tests="['01', '03', '10']")


class Migration(migrations.Migration):
    dependencies = [
        ('session', '0046_auto_20200521_1510'),
    ]

    operations = [
        migrations.RunPython(populate_testing_modes)
    ]
