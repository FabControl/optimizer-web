# Generated by Django 2.2.4 on 2020-06-03 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0055_add_and_assign_descriptors'),
    ]

    operations = [
        migrations.AddField(
            model_name='material',
            name='max_temperature',
            field=models.IntegerField(default=240),
        ),
        migrations.AddField(
            model_name='material',
            name='min_temperature',
            field=models.IntegerField(default=240),
        ),
    ]
