# Generated by Django 2.2.4 on 2019-08-25 17:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0017_auto_20190823_1249'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='_previous_tests',
            field=models.TextField(default='', max_length=1000000),
        ),
        migrations.AlterField(
            model_name='session',
            name='_persistence',
            field=models.TextField(default='', max_length=1000000),
        ),
    ]