# Generated by Django 5.1.6 on 2025-04-11 08:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0006_alter_usermodel_email'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Customer',
        ),
    ]
