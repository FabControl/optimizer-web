# Generated by Django 2.2.4 on 2020-01-29 18:28

from django.db import migrations


def populate_junctions(app, schema_editor):
    db_alias = schema_editor.connection.alias

    test_list = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13']
    Junction = app.get_model('session', 'Junction')

    for test in test_list:
        Junction.objects.using(db_alias).create(base_test=test)


class Migration(migrations.Migration):
    dependencies = [
        ('session', '0048_manual_add_session_modes'),
    ]

    operations = [
        migrations.RunPython(populate_junctions)
    ]
