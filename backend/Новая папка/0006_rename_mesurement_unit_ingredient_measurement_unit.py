# Generated by Django 3.2.3 on 2024-09-05 18:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_rename_measuring_unit_ingredient_mesurement_unit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ingredient',
            old_name='mesurement_unit',
            new_name='measurement_unit',
        ),
    ]
