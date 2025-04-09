from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager, AbstractBaseUser, PermissionsMixin


class Customer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=11, unique=True)
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class UserManagerModel(BaseUserManager):    
    use_in_migrations = True

    def create_user(self, first_name, last_name, email, phone_number, password, **extra_fields):
        if not email: 
            raise ValueError('Users must have an email address')
        if not phone_number:
            raise ValueError('Users must have an phone number')
        email = self.normalize_email(email)
        user = self.model(first_name=first_name, last_name=last_name, email=email,  phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, phone_number, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(first_name, last_name, email, phone_number, password, **extra_fields)

class UserModel(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50) 
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=254, unique=True)
    phone_number = models.CharField(max_length=11, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now=True, null=True) 
    last_login = models.DateTimeField(auto_now=True, null=True) 

    objects = UserManagerModel()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"