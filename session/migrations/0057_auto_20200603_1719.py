# Generated by Django 2.2.4 on 2020-06-03 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0056_auto_20200603_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='material',
            name='max_temperature',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='material',
            name='min_temperature',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]