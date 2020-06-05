# Generated by Django 2.2.4 on 2020-04-20 10:47
from django.db import migrations


def assing_numbers(app, schema_editor):
    countries = [
            ('BE', 21),
            ('BG', 20),
            ('CY', 19),
            ('CZ', 21),
            ('HR', 25),
            ('DK', 25),
            ('EE', 20),
            ('FI', 24),
            ('FR', 20),
            ('MC', 20),
            ('DE', 19),
            ('GR', 24),
            ('HU', 27),
            ('IE', 23),
            ('IT', 22),
            ('LT', 21),
            ('LU', 17),
            ('MT', 18),
            ('NL', 21),
            ('PL', 23),
            ('PT', 23),
            ('RO', 19),
            ('SK', 20),
            ('SI', 22),
            ('ES', 21),
            ('SE', 25)]

    db_alias = schema_editor.connection.alias
    TaxationCountry = app.get_model('payments', 'TaxationCountry')
    for country, rate in countries:
        TaxationCountry.objects.using(db_alias).create(name=country, vat_charge=rate, exclude_vat=True)


    TaxationCountry.objects.using(db_alias).create(name='LV', vat_charge=21, exclude_vat=False)


class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0009_create_country_vat_table'),
    ]

    operations = [
            migrations.RunPython(assing_numbers, lambda x,y: None)
    ]


