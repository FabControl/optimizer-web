# Generated by Django 2.2.4 on 2020-05-20 08:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0021_create_corporations_model'),
        ('session', '0045_auto_20200423_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='corporation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='payments.Corporation'),
        ),
        migrations.AddField(
            model_name='material',
            name='corporation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='payments.Corporation'),
        ),
        migrations.AddField(
            model_name='session',
            name='corporation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='payments.Corporation'),
        ),
    ]