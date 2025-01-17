# Generated by Django 2.2.4 on 2020-05-20 08:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0021_create_corporations_model'),
        ('authentication', '0024_create_affiliates_model'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='plan',
            new_name='_plan',
        ),
        migrations.AddField(
            model_name='affiliate',
            name='corporation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='payments.Corporation'),
        ),
        migrations.AddField(
            model_name='user',
            name='manager_of_corporation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managers', to='payments.Corporation'),
        ),
        migrations.AddField(
            model_name='user',
            name='member_of_corporation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='team', to='payments.Corporation'),
        ),
        migrations.AlterField(
            model_name='user',
            name='_plan',
            field=models.CharField(choices=[('basic', 'Core'), ('premium', 'Premium'), ('education', 'Education'), ('permanent', 'Permanent'), ('test', 'Test')], db_column='plan', default='basic', max_length=32),
        ),
    ]
