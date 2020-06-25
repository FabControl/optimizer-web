# Generated by Django 2.2.4 on 2020-06-22 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0066_auto_20200622_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='target',
            field=models.CharField(choices=[('mechanical_strength', 'Mechanical Strength'), ('aesthetics', 'Visual Quality'), ('fast_printing', 'Short Printing Time')], default='mechanical_strength', max_length=20),
        ),
    ]
