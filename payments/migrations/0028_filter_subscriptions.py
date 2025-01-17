# Generated by Django 2.2.4 on 2020-09-09 15:38

from django.db import migrations

def remove_duplicate_subscriptions(app, schema_editor):
    db_alias = schema_editor.connection.alias

    Subscription = app.get_model('payments', 'Subscription')
    current_id = ''
    for s in Subscription.objects.using(db_alias).order_by('stripe_id'):
        if s.stripe_id == current_id:
            s.delete()
        current_id = s.stripe_id

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0027_currency_conversion_rate'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_subscriptions, lambda x,y: None)
    ]
