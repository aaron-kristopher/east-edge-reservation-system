from django.contrib.auth.backends import BaseBackend
# from django.contrib.auth.hashers import check_password
from .models import UserModel

class EmailBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password) and user.is_active:
            # if user and check_password(password, user.password):
                return user
        except UserModel.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
