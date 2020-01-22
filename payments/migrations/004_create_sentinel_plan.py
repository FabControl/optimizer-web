# Generated by Django 2.2.4 on 2020-01-15 15:29

from django.db import migrations
from datetime import timedelta


def create_sentinel_plan(app, schema_editor):
    db_alias = schema_editor.connection.alias

    Plan = app.get_model('payments', 'Plan')
    Plan.objects.using(db_alias).create(**{"name": "deleted",
                                           "price": 0,
                                           "subscription_period": timedelta(0),
                                           "type": 'deleted'})


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_auto_20191128_1118'),
    ]

    operations = [
             migrations.RunPython(create_sentinel_plan)
    ]
