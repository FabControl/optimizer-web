# Generated by Django 2.2.4 on 2020-06-22 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0065_add_MP_printers_to_sample_printers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='target',
            field=models.CharField(choices=[('mechanical_strength', 'Mechanical Strength'), ('aesthetics', 'Visual Quality'), ('fast_printing', 'Short printing time')], default='mechanical_strength', max_length=20),
        ),
    ]