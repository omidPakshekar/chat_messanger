from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db.models.signals import (pre_save, post_save)



GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
)

class MyAccountManager(BaseUserManager):
	def create_user(self, username, password=None):
		if not username:
			raise ValueError('Users must have a username')
		user = self.model(
			username=username,
		)
		user.set_password(password)
		user.save()
		return user

	def create_superuser(self, username, password):
		user = self.create_user(
			password=password,
			username=username,
		)
		user.is_admin = True
		user.is_staff = True
		user.is_superuser = True
		user.save()
		return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
	username 		= models.CharField(max_length=30, unique=True)
	name            = models.CharField(max_length=30, default='', blank=True, null=True)
	gender          = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
	date_joined		= models.DateTimeField(verbose_name='date joined', auto_now_add=True)
	last_login		= models.DateTimeField(verbose_name='last login', auto_now=True)
	is_admin		= models.BooleanField(default=False)
	is_active		= models.BooleanField(default=True)
	is_staff		= models.BooleanField(default=False)
	is_superuser	= models.BooleanField(default=False)
	birthday_time   = models.DateField(blank=True, null=True)

	objects = MyAccountManager()

	USERNAME_FIELD = 'username'

	def __str__(self):
		return self.username









