from rest_framework import viewsets
from rest_framework.response import Response

from .models import DynamicNetworkLocation
from .models import NetworkLocation
from .models import StaticNetworkLocation
from .serializers import NetworkLocationSerializer
from kolibri.core.content.permissions import CanManageContent
from kolibri.core.discovery.utils.network.search import get_available_instances


class NetworkLocationViewSet(viewsets.ModelViewSet):
    permission_classes = (CanManageContent,)
    serializer_class = NetworkLocationSerializer
    queryset = NetworkLocation.objects.all()


class DynamicNetworkLocationViewSet(viewsets.ModelViewSet):
    permission_classes = (CanManageContent,)
    serializer_class = NetworkLocationSerializer
    queryset = DynamicNetworkLocation.objects.all()

    def list(self, request):
        available_instances = get_available_instances()
        serializer = NetworkLocationSerializer(available_instances, many=True)
        return Response(serializer.data)


class StaticNetworkLocationViewSet(viewsets.ModelViewSet):
    permission_classes = (CanManageContent,)
    serializer_class = NetworkLocationSerializer
    queryset = StaticNetworkLocation.objects.all()
