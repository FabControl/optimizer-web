# Generated by Django 2.2.4 on 2020-01-31 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0035_add_header_footer_sessions'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='offset_1',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='machine',
            name='offset_2',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
