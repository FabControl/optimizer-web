# Generated by Django 2.2.4 on 2019-11-01 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_manual_set_all_users_to_premium'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='subscription_expiration',
            field=models.DateTimeField(null=True),
        ),
    ]
