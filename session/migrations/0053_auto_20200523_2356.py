# Generated by Django 2.2.4 on 2020-05-23 20:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0052_rename_plan_availability'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='mode',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='session.SessionMode'),
        ),
    ]