from django.db import models

class Method(models.Model):
    title = models.CharField(max_length=300)

    def __str__(self):
        return self.title

class Therapist(models.Model):
    name = models.CharField(max_length=200)
    methods = models.ManyToManyField(Method, related_name='therapists')
    photo = models.ImageField(upload_to='therapists', blank=True)

    def __str__(self):
        return self.name