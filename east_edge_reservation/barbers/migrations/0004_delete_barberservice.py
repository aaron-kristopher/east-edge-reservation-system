# Generated by Django 5.1.6 on 2025-02-11 00:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('barbers', '0003_alter_barberservice_unique_together_and_more'),
        ('reservations', '0002_reservation_services_delete_reservationservice'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BarberService',
        ),
    ]
