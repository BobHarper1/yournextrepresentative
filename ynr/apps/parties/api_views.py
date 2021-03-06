from rest_framework import viewsets

from api.helpers import ResultsSetPagination

from .models import Party
from .serializers import PartySerializer


class PartyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Party.objects.all().prefetch_related("emblems", "descriptions")
    serializer_class = PartySerializer
    lookup_field = "ec_id"
    pagination_class = ResultsSetPagination
