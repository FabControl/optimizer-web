from django.db import migrations, models


def func_reset_default(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    db_alias = schema_editor.connection.alias
    User.objects.using(db_alias).all().update(plan='premium')


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0006_auto_20191022_1009'),
    ]

    operations = [
        migrations.RunPython(func_reset_default)
    ]
