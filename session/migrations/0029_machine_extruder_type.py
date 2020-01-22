# Generated by Django 2.2.7 on 2019-12-03 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0028_auto_20191128_1118'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='extruder_type',
            field=models.CharField(choices=[('Bowden', 'bowden'), ('Direct drive', 'directdrive')], default='bowden', max_length=20),
        ),
    ]
