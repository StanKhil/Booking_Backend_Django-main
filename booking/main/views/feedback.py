from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from main.models import *
from main.serializers.feeedback import FeedbackSerializer
from main.filters import FeedbackFilter
from main.rest import RestResponse, RestStatus


class FeedbackView(APIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = FeedbackFilter

    def get(self, request):
        queryset = Feedback.objects.filter(deleted_at__isnull=True)


        feedback_filter = FeedbackFilter(request.GET, queryset=queryset)
        queryset = feedback_filter.qs

        serializer = FeedbackSerializer(queryset, many=True)

        return Response(
            RestResponse(
                RestStatus(True, 200, "OK"),
                serializer.data
            ).to_dict(),
            status=status.HTTP_200_OK
        )

    def post(self, request):
        data = request.data

        try:
            realty = Realty.objects.get(id=data.get("realty_id"))
            user_access = UserAccess.objects.get(id=data.get("user_access_id"))

            feedback = Feedback.objects.create(
                text=data.get("text"),
                rate=data.get("rate"),
                realty=realty,
                user_access=user_access
            )

            serializer = FeedbackSerializer(feedback)

            return Response(
                RestResponse(
                    RestStatus(True, 201, "Created"),
                    serializer.data
                ).to_dict(),
                status=status.HTTP_201_CREATED
            )

        except Realty.DoesNotExist:
            return Response(
                RestResponse(
                    RestStatus(False, 404, "Realty not found"),
                    None
                ).to_dict(),
                status=status.HTTP_404_NOT_FOUND
            )

        except UserAccess.DoesNotExist:
            return Response(
                RestResponse(
                    RestStatus(False, 404, "User not found"),
                    None
                ).to_dict(),
                status=status.HTTP_404_NOT_FOUND
            )
