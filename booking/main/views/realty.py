from django.http import HttpResponse, Http404
#from django.http import JsonResponse
from main.models import *
from main.rest import *
from main.serializers.user import *
from main.serializers.booking import *
from main.serializers.realty import *
from main.serializers.feeedback import *
from main.serializers.location import *
from main.filters import *
#from typing import Dict, Any
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
#from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
#from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count
from django.db.models.functions import Coalesce
from backend.services import *
from django.shortcuts import get_object_or_404

storageService = DiskStorageService()


def item(request, itemId):
    try:
        content = storageService.getItemBytes(itemId)
        mime_type = storageService.tryGetMimeType(itemId)
        return HttpResponse(content, content_type=mime_type)
    except (FileNotFoundError, ValueError):
        raise Http404("Item not found")

class RealtyViewSet(ModelViewSet):
    queryset = Realty.objects.filter(deleted_at__isnull=True)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RealtyFilter

    queryset = queryset.annotate(
        avg_rating=Avg("feedbacks__rate"),
        rates_count=Count("feedbacks")
    )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RealtyCreateSerializer
        return RealtySerializer

    #GET /realty/
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        response = RestResponse(
            status=RestStatus(True, 200, "OK"),
            data=serializer.data
        )

        return Response(response.to_dict(), status=status.HTTP_200_OK)

    #GET /realty/{id}/
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        response = RestResponse(
            status=RestStatus(True, 200, "OK"),
            data=serializer.data
        )

        return Response(response.to_dict(), status=status.HTTP_200_OK)

    #POST /realty/
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        image_file = request.FILES.get("realty-img")
        if not image_file:
            return Response(
                {"error": "Image is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        saved_name = storageService.saveItem(image_file)

        itemImage = ItemImage(
            image_url=saved_name,
            order=0,
            realty=instance
        )
        itemImage.save()

        response = RestResponse(
            status=RestStatus(True, 201, "Created"),
            data=serializer.data
        )
        return Response(response.to_dict(), status=status.HTTP_201_CREATED)
    
    def patch(self, request, *args, **kwargs):
        slug = request.data.get('realty-former-slug')
        instance = get_object_or_404(Realty, slug=slug)

        serializer = self.get_serializer(instance, data=request.data, partial=True)

        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()

                if 'realty-main-image' in request.FILES:
                    image_file = request.FILES.get("realty-img")
                    if not image_file:
                        return Response(
                            {"error": "Image is required"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    saved_name = storageService.saveItem(image_file)

                    itemImage = ItemImage(
                        image_url=saved_name,
                        order=0,
                        realty=instance
                    )
                    itemImage.save()
            else:
                raise Exception

            response = RestResponse(
                status=RestStatus(True, 200, "Ok"),
                data=serializer.data
            )
            return Response(response.to_dict(), status=status.HTTP_200_OK)
        except:
            response = RestResponse(
                status=RestStatus(False, 400, "Bad Request"),
                data=serializer.errors
            )
            return Response(response.to_dict(), status=status.HTTP_400_BAD_REQUEST)

    

@api_view(["POST"])
def RealtySearchViewSet(request):
    serializer = RealtySearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data

    queryset = Realty.objects.filter(deleted_at__isnull=True)

    if "Price" in data:
        queryset = queryset.filter(price__gte=data["Price"])

    if "Checkboxes" in data and data["Checkboxes"]:
        queryset = queryset.filter(
            realty_group__slug__in=data["Checkboxes"]
        )

    queryset = queryset.annotate(
        avg_rating=Coalesce(Avg("feedbacks__rate"), 0.0)
    )

    if "Rating" in data:
        queryset = queryset.filter(avg_rating__gte=data["Rating"])

    queryset = queryset.distinct()

    result = RealtySerializer(queryset, many=True).data

    response = RestResponse(
        status=RestStatus(True, 200, "OK"),
        data=result
    )

    return Response(response.to_dict(), status=status.HTTP_200_OK)

