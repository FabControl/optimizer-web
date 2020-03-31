from django.db import migrations, models
from django.utils import timezone


def func_reset_default(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    db_alias = schema_editor.connection.alias
    users = User.objects.using(db_alias).all()
    for user in users:
        current_expiration = user.subscription_expiration
        new_expiration = current_expiration + timezone.timedelta(days=30)
        user.subscription_expiration = new_expiration
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0018_user_can_access_investor_dashboard'),
    ]

    operations = [
        migrations.RunPython(func_reset_default)
    ]
