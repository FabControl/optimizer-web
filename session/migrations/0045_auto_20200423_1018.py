# Generated by Django 2.2.4 on 2020-04-23 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0044_material_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nozzle',
            name='size_id',
            field=models.DecimalField(decimal_places=2, default=0.4, max_digits=3),
        ),
    ]