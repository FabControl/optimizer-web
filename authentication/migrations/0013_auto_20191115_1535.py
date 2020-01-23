# Generated by Django 2.2.4 on 2019-11-15 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0012_auto_20191115_1148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(error_messages={'unique': 'Email must be unique'}, max_length=254, unique=True, verbose_name='email address'),
        ),
    ]