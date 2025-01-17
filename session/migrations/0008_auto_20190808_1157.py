# Generated by Django 2.2.2 on 2019-08-08 11:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0007_auto_20190808_0959'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='machine',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='session.Machine'),
        ),
        migrations.AlterField(
            model_name='session',
            name='material',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='session.Material'),
        ),
        migrations.AlterField(
            model_name='session',
            name='settings',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='session.Settings'),
        ),
    ]
