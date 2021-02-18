from .models import Therapist
from .serializers import TherapistSerializer
from django.views.generic.list import ListView


class TherapistListView(ListView):
    model = Therapist

    def get_context_data(self):
        therapists = Therapist.objects.prefetch_related("methods").all()
        context = {
            'therapists': TherapistSerializer(therapists, many=True).data
        }
        return context
