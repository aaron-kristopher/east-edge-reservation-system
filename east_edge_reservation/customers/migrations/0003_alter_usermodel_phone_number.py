# Generated by Django 5.1.6 on 2025-03-12 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0002_usermodel_date_joined_alter_usermodel_last_login'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usermodel',
            name='phone_number',
            field=models.CharField(max_length=11, unique=True),
        ),
    ]
