# Generated by Django 2.2.4 on 2019-08-19 14:28

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0011_auto_20190819_1130'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_name', models.CharField(choices=[('First-layer printing height test', 'First-layer printing height test'), ('Extrusion temperature test', 'Extrusion temperature test'), ('Retraction distance test', 'Retraction distance test'), ('Bridging test', 'Bridging test')], max_length=64)),
                ('test_number', models.CharField(choices=[('01', '01'), ('03', '03'), ('10', '10'), ('11', '11')], max_length=64)),
                ('executed', models.BooleanField(default=True)),
                ('tested_parameter_one_values', models.TextField(blank=True, max_length=10000)),
                ('tested_parameter_two_values', models.TextField(blank=True, max_length=10000)),
                ('tested_parameter_three_values', models.TextField(blank=True, max_length=10000)),
                ('tested_volumetric_flow_rate_values', models.TextField(blank=True, max_length=10000)),
                ('selected_parameter_one_value', models.DecimalField(blank=True, decimal_places=3, default=0, max_digits=4)),
                ('selected_parameter_two_value', models.DecimalField(blank=True, decimal_places=3, default=0, max_digits=4)),
                ('selected_parameter_three_value', models.DecimalField(blank=True, decimal_places=3, default=0, max_digits=4)),
                ('selected_volumetric_flow_rate_value', models.DecimalField(blank=True, decimal_places=3, default=0, max_digits=4)),
                ('parameter_one_name', models.CharField(default='first-layer track height', max_length=64)),
                ('parameter_two_name', models.CharField(default='first-layer printing speed', max_length=64)),
                ('parameter_one_units', models.CharField(choices=[('mm', 'mm'), ('mm/s', 'mm/s'), ('degC', 'degC')], default='mm', max_length=12)),
                ('parameter_two_units', models.CharField(choices=[('mm', 'mm'), ('mm/s', 'mm/s'), ('degC', 'degC')], default='mm/s', max_length=12)),
                ('datetime_info', models.DateTimeField(blank=True, default=datetime.datetime.now)),
            ],
        ),
    ]
