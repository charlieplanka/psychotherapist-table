from django.db import models
from django.core.files import File
from tempfile import NamedTemporaryFile
from requests import request

class Method(models.Model):
    title = models.CharField(max_length=300)

    def __str__(self):
        return self.title

class Therapist(models.Model):
    airtable_id = models.CharField(max_length=200, blank=True, null=True)  # make primary key
    name = models.CharField(max_length=200)
    methods = models.ManyToManyField(Method, related_name='therapists')
    photo = models.ImageField(upload_to='therapists', blank=True, null=True)

    def __str__(self):
        return self.name
