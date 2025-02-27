# Generated by Django 5.1.6 on 2025-02-12 06:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('barbers', '0004_delete_barberservice'),
    ]

    operations = [
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('barber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='barbers.barber')),
            ],
            options={
                'ordering': ['start_datetime'],
            },
        ),
    ]
