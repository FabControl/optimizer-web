# Generated by Django 2.2.4 on 2019-08-23 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0016_auto_20190822_1544'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='_min_max_parameter_one',
            field=models.CharField(default='[0,0]', max_length=20),
        ),
        migrations.AlterField(
            model_name='session',
            name='_min_max_parameter_three',
            field=models.CharField(default='[0,0]', max_length=20),
        ),
        migrations.AlterField(
            model_name='session',
            name='_min_max_parameter_two',
            field=models.CharField(default='[0,0]', max_length=20),
        ),
    ]