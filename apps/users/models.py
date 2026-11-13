from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    RESIDENCY_CHOICES =[
        ('LOCAL', 'Local Citizen'),
        ('REGIONAL', 'Regional Resident'),
        ('INTERNATIONAL', 'International Tourist'),
    ]

    residency_status = models.CharField(max_length=20, choices=RESIDENCY_CHOICES, default='LOCAL', help_text="Used to calculate game park entrance fees.")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)

    def __str__(self):
        return self.username