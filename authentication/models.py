from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    
    # Make email the username field
    USERNAME_FIELD = 'email'
    # Remove email from REQUIRED_FIELDS since it's now the USERNAME_FIELD
    REQUIRED_FIELDS = ['username']
