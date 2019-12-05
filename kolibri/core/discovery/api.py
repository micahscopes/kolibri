from rest_framework import viewsets
from rest_framework.response import Response

from .models import NetworkLocation
from .serializers import NetworkLocationSerializer
from .utils.network.search import discovery_index


class DynamicNetworkLocationViewSet(viewsets.ViewSet):
    def list(self, request):
        locations = discovery_index.values()
        return Response(locations)

    def retrieve(self, request, pk=None):
        return Response(discovery_index[pk])


class StaticNetworkLocationViewSet(viewsets.ModelViewSet):
    serializer_class = NetworkLocationSerializer
    queryset = NetworkLocation.objects.all()


class NetworkLocationViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        if pk in discovery_index:
            return Response(discovery_index[pk])
        else:
            return StaticNetworkLocationViewSet().retrieve(request, pk)
