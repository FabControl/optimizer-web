# Generated by Django 2.2.4 on 2020-05-15 05:58

from django.db import migrations

def create_basic_currencies(app, schema_editor):
    db_alias = schema_editor.connection.alias

    Currency = app.get_model('payments', 'Currency')
    Currency.objects.using(db_alias).create(name='EUR',
                                    _countries='AX EU AD AT BE CY EE FI FR TF DE GR GP IE IT XK LV LT LU MT GF MQ YT MC ME NL PT RE BL MF PM SM SK SI ES VA')

    Currency.objects.using(db_alias).create(name='USD', _countries='US')


def delete_basic_currencies(app, schema_editor):
    db_alias = schema_editor.connection.alias

    Currency = app.get_model('payments', 'Currency')
    for c in ('EUR', 'USD'):
        try:
            currency = Currency.objects.using(db_alias).get(name=c)
        except Currency.DoesNotExist:
            pass
        else:
            currency.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0018_add_currencies'),
    ]

    operations = [
         migrations.RunPython(create_basic_currencies, delete_basic_currencies)
    ]

