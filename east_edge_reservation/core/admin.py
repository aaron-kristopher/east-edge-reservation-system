from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from django.urls import reverse
from customers.forms import CustomUserChangeForm, CustomUserCreationForm, CustomAdminPasswordChangeForm


from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin

from customers.models import UserModel


# admin.site.unregister(User)
if Group in admin.site._registry:
    admin.site.unregister(Group)




# @admin.register(User)
# class UserAdmin(BaseUserAdmin, ModelAdmin):
#     Forms loaded from `unfold.forms`
#     form = UserChangeForm
#     add_form = UserCreationForm
#     change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    pass

@admin.register(UserModel)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    ordering = ("first_name",)
    form =  CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = CustomAdminPasswordChangeForm
    fieldsets = (
        (None, {"fields": ("phone_number", "password",)}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("date_joined", "last_login")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("first_name", "last_name", "phone_number", "email", "password1", "password2", "is_staff", "is_superuser"),        }),
    )
    list_display = ("first_name", "last_name", "email", "phone_number", "is_staff", "is_superuser")

    search_fields = ("first_name", "last_name", "email")
    ordering = ("date_joined",)
    readonly_fields = ("date_joined", "last_login")
    list_filter = ("is_staff", "is_superuser", "is_active")

