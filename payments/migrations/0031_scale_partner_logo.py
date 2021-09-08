# Generated by Django 2.2.4 on 2020-09-14 17:42

from django.db import migrations
from PIL import Image
from io import BytesIO
from base64 import b64encode, b64decode

def scale_logo(app, schema_editor):
    db_alias = schema_editor.connection.alias
    Partner = app.get_model('payments', 'Partner')
    for partner in Partner.objects.using(db_alias).all():
        logo = Image.open(BytesIO(b64decode(partner.logo.encode('utf-8'))))
        scale = max((logo.width / 400.0, logo.height / 80.0))
        if scale > 1.0:
            logo_bytes = BytesIO()
            logo.resize((int(logo.width / scale), int(logo.height / scale))).save(logo_bytes, 'PNG')

            partner.logo = b64encode(logo_bytes.getvalue()).decode('utf-8')
            partner.save()


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0030_partner_banner'),
    ]

    operations = [
            migrations.RunPython(scale_logo, lambda x,y: None)
    ]