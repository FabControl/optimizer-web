# Generated by Django 2.2.2 on 2019-07-16 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model', models.CharField(default='Unknown', max_length=30)),
                ('buildarea_maxdim1', models.IntegerField(default=0)),
                ('buildarea_maxdim2', models.IntegerField(default=0)),
                ('form', models.CharField(choices=[('elliptic', 'Elliptic'), ('cartesian', 'Cartesian')], default='cartesian', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size_od', models.DecimalField(decimal_places=2, default=1.75, max_digits=3)),
                ('name', models.CharField(max_length=60)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='date published')),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_number', models.IntegerField(default=0)),
                ('session_name', models.CharField(default='Untitled', max_length=20)),
                ('target', models.CharField(choices=[('MS', 'Mechanical Strength'), ('A', 'Aesthetics'), ('FP', 'Fast Printing')], default='MS', max_length=20)),
                ('test_number', models.CharField(choices=[('01', 'First-layer printing height test'), ('03', 'Extrusion temperature test')], default='01', max_length=20)),
                ('slicer', models.CharField(choices=[('Prusa', 'Slic3r PE'), ('Simplify3D', 'Simplify3D'), ('Cura', 'Cura')], default='Prusa', max_length=20)),
            ],
        ),
    ]
