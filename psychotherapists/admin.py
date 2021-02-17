from django.contrib import admin
from .models import Therapist, Method, AirtableRaw

@admin.register(Therapist)
class TherapistAdmin(admin.ModelAdmin):

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    pass


@admin.register(AirtableRaw)
class AirtableRawAdmin(admin.ModelAdmin):
    pass
