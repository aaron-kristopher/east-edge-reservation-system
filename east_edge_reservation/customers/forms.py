from django import forms
from .models import Customer, UserModel
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AdminPasswordChangeForm

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=True)


    class Meta:
        model = UserModel
        fields = ["first_name", "last_name", "phone_number", "email", "password", "password_confirm"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if not phone_number or not str(phone_number).isdigit() or len(str(phone_number)) != 11:
            raise forms.ValidationError("Phone number must be exactly 11 digits.")
        if UserModel.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("A customer with this phone number already exists.")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match. Try again.")    

        return cleaned_data
    

class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users in the admin panel."""
    
    class Meta:
        model = UserModel
        fields = ("first_name", "last_name", "email", "phone_number", "password1", "password2")

class CustomUserChangeForm(UserChangeForm):
    """Form for updating existing users in the admin panel."""

    class Meta:
        model = UserModel
        fields = ("first_name", "last_name", "email", "phone_number", "is_staff", "is_active", "is_superuser", "groups")

class CustomAdminPasswordChangeForm(AdminPasswordChangeForm):
    """Form for changing a user's password in the admin panel."""
    pass

