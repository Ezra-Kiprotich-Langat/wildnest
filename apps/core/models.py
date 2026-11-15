from django.db import models
from django.utils import timezone

class TimeStampedModel(models.Model):
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']

class ActiveModel(models.Model):
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True


class SlugModel(models.Model):
    
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    
    class Meta:
        abstract = True


class FullBaseModel(TimeStampedModel, ActiveModel):
   
    class Meta:
        abstract = True