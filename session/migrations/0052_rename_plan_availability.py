from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0051_auto_20200522_0917'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sessionmode',
            old_name='plan_availability',
            new_name='_plan_availability',
        ),
    ]
