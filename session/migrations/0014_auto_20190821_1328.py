# Generated by Django 2.2.4 on 2019-08-21 10:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0013_session_persistence'),
    ]

    operations = [
        migrations.RenameField(
            model_name='session',
            old_name='persistence',
            new_name='_persistence',
        ),
    ]
