# Generated by Django 5.1.6 on 2025-04-09 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reservation',
            old_name='customer',
            new_name='reserved_by',
        ),
        migrations.AddField(
            model_name='reservation',
            name='is_reserved_for_self',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='reservation',
            name='reserved_for_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='reservation',
            name='reserved_for_first_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='reservation',
            name='reserved_for_last_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='reservation',
            name='reserved_for_phone',
            field=models.CharField(blank=True, max_length=11, null=True),
        ),
    ]
