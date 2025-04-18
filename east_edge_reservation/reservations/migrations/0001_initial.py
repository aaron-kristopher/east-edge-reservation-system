# Generated by Django 5.1.6 on 2025-03-12 18:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('barbers', '0001_initial'),
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField(blank=True, help_text="Calculated based on services' estimated time", null=True, verbose_name='End Time')),
                ('status', models.CharField(choices=[('C', 'Completed'), ('P', 'Pending'), ('X', 'Cancelled')], default='P', max_length=1)),
                ('barber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='barbers.barber', verbose_name='Barber')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='customers.customer', verbose_name='Customer')),
                ('services', models.ManyToManyField(help_text='Services included in this reservation', related_name='reservations', to='barbers.service', verbose_name='Services')),
            ],
        ),
    ]
