from django.db import migrations, models
from django.utils import timezone


def func_reset_default(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    db_alias = schema_editor.connection.alias
    users = User.objects.using(db_alias).all()
    expiry = timezone.datetime(2020, 3, 31)
    users.update(subscription_expiration=expiry)


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0015_auto_20191125_1500'),
    ]

    operations = [
        migrations.RunPython(func_reset_default)
    ]
