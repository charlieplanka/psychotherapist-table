from django.contrib import admin
from .models import Therapist, Method, AirtableRaw

@admin.register(Therapist)
class TherapistAdmin(admin.ModelAdmin):
    pass

@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    pass


@admin.register(AirtableRaw)
class AirtableRawAdmin(admin.ModelAdmin):
    pass
