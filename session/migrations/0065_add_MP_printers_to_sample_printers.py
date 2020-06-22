from django.db import migrations
from django.conf import settings
import json

MACHINE_SAMPLES = '''
[{
    "model": "Mass Portal XD30",
    "buildarea_maxdim1": 300,
    "buildarea_maxdim2": 300,
    "form": "elliptic",
    "extruder": {
      "nozzle": {
        "size_id": 0.4
      }
    },
    "printbed": {
      "printbed_heatable": true
    }
  },
  {
    "model": "Mass Portal XD40",
    "buildarea_maxdim1": 400,
    "buildarea_maxdim2": 400,
    "form": "elliptic",
    "extruder": {
      "nozzle": {
        "size_id": 0.4
      }
    },
    "printbed": {
      "printbed_heatable": true
    }
  },
  {
    "model": "Mass Portal D600",
    "buildarea_maxdim1": 400,
    "buildarea_maxdim2": 400,
    "form": "elliptic",
    "extruder": {
      "nozzle": {
        "size_id": 0.4
      }
    },
    "printbed": {
      "printbed_heatable": true
    }
  }
]
'''


def populate_machine_samples(app, schema_editor):
    db_alias = schema_editor.connection.alias

    User = app.get_model('authentication', 'User')
    Nozzle = app.get_model('session', 'Nozzle')
    Extruder = app.get_model('session', 'Extruder')
    Printbed = app.get_model('session', 'Printbed')
    Chamber = app.get_model('session', 'Chamber')
    Machine = app.get_model('session', 'Machine')

    user = User.objects.get(email=settings.SAMPLE_SESSIONS_OWNER)
    for m in json.loads(MACHINE_SAMPLES):
        nozzle = Nozzle.objects.using(db_alias).create(**m['extruder']['nozzle'])
        m['extruder']['nozzle'] = nozzle
        extruder = Extruder.objects.using(db_alias).create(**m['extruder'])
        m['extruder'] = extruder
        printbed = Printbed.objects.using(db_alias).create(**m['printbed'])
        m['printbed'] = printbed

        Machine.objects.using(db_alias).create(owner=user,
                                               chamber=Chamber.objects.create(),
                                               **m)


class Migration(migrations.Migration):
    dependencies = [
        ('session', '0064_allow_guided_in_limited_access'),
    ]

    operations = [
        migrations.RunPython(populate_machine_samples)
    ]
