# Generated by Django 2.2.4 on 2020-10-23 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0026_auto_20200615_1855'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='information_reference',
            field=models.CharField(blank=True, default='', max_length=150, verbose_name='Where did you find out about 3DOptimizer'),
        ),
    ]