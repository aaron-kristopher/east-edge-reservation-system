from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from customers.models import UserModel

class Command(BaseCommand):
    help = 'Create default groups and permissions'

    def handle(self, *args, **options):
        # Create groups
        customer_group, created = Group.objects.get_or_create(name='Customer')
        receptionist_group, created = Group.objects.get_or_create(name='Receptionist')
        barber_group, created = Group.objects.get_or_create(name='Barber')

        # Create superuser if it doesn't exist
        if not UserModel.objects.filter(email='admin@example.com').exists():
            superuser = UserModel.objects.create_superuser(
                first_name='Admin',
                last_name='User',
                email='admin@example.com',
                phone_number='00000000000',
                password='admin123'
            )
            # Add superuser to all groups
            superuser.groups.add(customer_group, receptionist_group, barber_group)
            self.stdout.write(self.style.SUCCESS('Successfully created superuser with all groups'))

        self.stdout.write(self.style.SUCCESS('Successfully created groups'))
