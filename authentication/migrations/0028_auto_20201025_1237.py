# Generated by Django 2.2.4 on 2020-10-25 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0027_user_information_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='information_reference',
            field=models.CharField(blank=True, default='', max_length=150, verbose_name='Where did you find out about 3DOptimizer?'),
        ),
    ]
