from django.db import migrations, models
from django.utils import timezone


def func_reset_default(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    db_alias = schema_editor.connection.alias
    users = User.objects.using(db_alias).all()
    formnext = timezone.datetime(2019, 11, 19)
    users.update(subscription_expiration=formnext)


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0008_user_subscription_expiration'),
    ]

    operations = [
        migrations.RunPython(func_reset_default)
    ]
