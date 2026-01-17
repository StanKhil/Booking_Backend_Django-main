import base64, json, re, datetime
from backend.services import *
from main.models import *
from main.rest import *
from .serializers import *
from .filters import *

from typing import Dict, Any

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count
from django.http import HttpResponse, Http404
from django.http import JsonResponse


passwordRegex = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!?@$&*])[A-Za-z\d@$!%*?&]{12,}$")

userAccessAccessor = UserAccessAccessor()
accessTokenAccessor = AccessTokenAccessor()

storageService = DiskStorageService()
kdfService = PbKdfService()
jwtService = JwtService()
randomService = DefaultRandomService()

@api_view(['GET'])
def userDetail(request, login: str):
    try:
        user = (
            UserAccess.objects
            .select_related('user_data', 'user_role')
            .prefetch_related(
                'booking_items__realty',
                'feedbacks__realty',
                'user_data__cards'
            )
            .get(login=login, deleted_at__isnull=True)
        )
    except UserAccess.DoesNotExist:
        return Response(
            RestResponse(
                RestStatus(False, 404, "User not found"),
                None
            ).to_dict(),
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = UserDetailSerializer(user)
    return Response(
        RestResponse(
            RestStatus(True, 200, "OK"),
            serializer.data
        ).to_dict(),
        status=status.HTTP_200_OK
    )


def authenticate(request):
    authorizationHeader = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
 
    if(not authorizationHeader):
        raise ValueError("Missing 'Authorization' header")
    authorizationScheme = "Basic "
    if(not authorizationHeader.startswith(authorizationScheme)):
        raise ValueError(f"Authorization scheme error: '{authorizationScheme}' only")
    
    credentials = authorizationHeader[len(authorizationScheme):]
    print("Credentials:", credentials)
    decoded = ""
    try:
        decoded = base64.b64decode(credentials).decode('utf-8')
    except Exception as e:
        print(f"SignIn: {e}")
        raise ValueError("Authorization credentials decode error")
    
    parts = decoded.split(":", 1)

    if(len(parts) != 2):
        raise ValueError("Authorization credentials decompose error")
    login, password = parts[0], parts[1]

    userAccess = userAccessAccessor.getUserAccessByLogin(login, False)
    if(userAccess == None):
        raise ValueError("Authorization credentials rejected: invalid login")
    if(kdfService.dk(password, userAccess.salt) != userAccess.dk):
        raise KeyError("Authorization credentials rejected: invalid password")
    return userAccess 

def login(request):
    if request.method == "OPTIONS":
        return HttpResponse()
    
    userAccess = None
    try:
        userAccess = authenticate(request)
    except Exception as e:
        responseObj = RestResponse(status=RestStatus(False, 401, "Unauthorized"), data=jwt)
        return JsonResponse(responseObj.to_dict(), safe=False)
    
    now = int(time.time())
    access_token = AccessToken(
        jti=str(uuid.uuid4()),
        sub=userAccess.id,
        iat=str(now),
        exp=str(now + 100),
        iss="Booking_WEB",
        aud=str(userAccess.user_role.id),
        user_access=userAccess
    )

    accessTokenAccessor.create(access_token)
    jwtPayload = {
        "jti": access_token.jti,
        "sub": str(access_token.sub),
        "iat": access_token.iat,
        "Exp": access_token.exp,
        "iss": access_token.iss,
        "aud": access_token.aud,
        "FirstName": userAccess.user_data.first_name,
        "LastName": userAccess.user_data.last_name,
        "Email": userAccess.user_data.email,
        "RoleId": userAccess.user_role.id,
        "Login": userAccess.login,
        "Id": str(userAccess.id)
    }
    jwt = jwtService.encodeJwt(jwtPayload)
    request.session["AuthToken"] = jwt

    request.session["userAccess"] = {
        "login": userAccess.login,
        "id": str(userAccess.id)
    }

    responseObj = RestResponse(status=RestStatus(True, 200, "Ok"), data=jwt)
    return JsonResponse(responseObj.to_dict(), safe=False)

@csrf_exempt
def register(request):
    data = json.loads(request.body) # UserSignupFormModel
    errors = processSignUpData(data)
    print(errors)
    if errors.__len__() > 0:
        responseObj = RestResponse(status=RestStatus(False, 400, "Bad Request"), data=data)
        return JsonResponse(responseObj.to_dict(), safe=False) 

    responseObj = RestResponse(status=RestStatus(True, 200, "Ok"), data="Registration successful")
    return JsonResponse(responseObj.to_dict(), safe=False)


def processSignUpData(model: Any) -> Dict[str, str]:
    errors:Dict[str, str] = {}
    
    if not model["userFirstName"]:
        errors["userFirstName"] = "First Name must not be empty!"
        
    if not model["userLastName"]:
        errors["userLastName"] = "Last Name must not be empty!"
        
    if not model["userEmail"]:
        errors["userEmail"] = "Email must not be empty!"
        
    if not model["userLogin"]:
        errors["userLogin"] = "Login must not be empty!"
    elif ":" in model["userLogin"]:
        errors["userLogin"] = "Login must not contain ':'!"
    if not model["userPassword"]:
        errors["userPassword"] = "Password cannot be empty"
        errors["userRepeat"] = "Invalid original password"
    elif not passwordRegex.match(model["userPassword"]):
        errors["userPassword"] = (
            "Password must be at least 12 characters long and contain lower, "
            "upper case letters, at least one number and at least one special character"
        )
        errors["userRepeat"] = "Invalid original password"
    elif model["userRepeat"] != model["userPassword"]:
        errors["userRepeat"] = "Passwords must match"
    if not model["agree"]:
        errors["agree"] = "You must agree with policies!"
    if errors:
        return errors
    
    user_id = uuid.uuid4()
    user_data = UserData(
        id = user_id,
        first_name = model["userFirstName"],
        last_name = model["userLastName"],
        email = model["userEmail"],
        birth_date = model["birthdate"],
        registered_at = datetime.datetime.now(), 
    )
    salt = randomService.otp(12)
    user_access = UserAccess(
        id = uuid.uuid4(),
        user_id = user_id,
        login = model["userLogin"],
        salt = salt,
        dk = kdfService.dk(model["userPassword"], salt),
        user_role = UserRole.objects.get(id="self_registered"),
        user_data = user_data
    )

    try:
        user_data.save()
        user_access.save()
        #self._user_data_accessor.create_async(user_data)
        #self._user_access_accessor.create_async(user_access)
    except Exception as e:
        errors["user_login"] = "Login already exists"
    return errors



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

        response = RestResponse(
            status=RestStatus(True, 201, "Created"),
            data=RealtySerializer(instance).data
        )

        return Response(response.to_dict(), status=status.HTTP_201_CREATED)
    

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
        avg_rating=Avg("feedbacks__rate")
    )

    if "Rating" in data:
        queryset = queryset.annotate(
            avg_rating=Avg("feedbacks__rate")
        ).filter(
            avg_rating__gte=data["Rating"]
        )

    queryset = queryset.distinct()

    result = RealtySerializer(queryset, many=True).data

    response = RestResponse(
        status=RestStatus(True, 200, "OK"),
        data=result
    )

    return Response(response.to_dict(), status=status.HTTP_200_OK)

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

class BookingView(APIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookingItemFilter

    @staticmethod
    def has_overlap(realty_id, start_date, end_date, exclude_id=None):
        qs = BookingItem.objects.filter(
            realty_id=realty_id,
            deleted_at__isnull=True,
            start_date__lt=end_date,
            end_date__gt=start_date
        )

        if exclude_id:
            qs = qs.exclude(id=exclude_id)

        return qs.exists()

    def get(self, request):
        queryset = BookingItem.objects.all()

        booking_filter = BookingItemFilter(request.GET, queryset=queryset)
        queryset = booking_filter.qs

        serializer = BookingItemSerializer(queryset, many=True)

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
            user_access = UserAccess.objects.get(id=data.get("userAccessId"))
            realty_id = data.get("realtyId")
            start_date = data.get("startDate")
            end_date = data.get("endDate")

            if not realty_id or not start_date or not end_date:
                return Response(
                    RestResponse(
                        RestStatus(False, 400, "Bad Request"),
                        "Missing required fields"
                    ).to_dict(),
                    status=status.HTTP_400_BAD_REQUEST
                )

            if start_date >= end_date:
                return Response(
                    RestResponse(
                        RestStatus(False, 400, "Invalid date range"),
                        None
                    ).to_dict(),
                    status=status.HTTP_400_BAD_REQUEST
                )

            if self.has_overlap(
                realty_id=realty_id,
                start_date=start_date,
                end_date=end_date
            ):
                return Response(
                    RestResponse(
                        RestStatus(False, 409, "Conflict"),
                        "Realty already booked for selected dates"
                    ).to_dict(),
                    status=status.HTTP_409_CONFLICT
                )

            booking_item = BookingItem.objects.create(
                realty_id=realty_id,
                start_date=start_date,
                end_date=end_date,
                user_access=user_access
            )

            serializer = BookingItemSerializer(booking_item)

            return Response(
                RestResponse(
                    RestStatus(True, 201, "Created"),
                    serializer.data
                ).to_dict(),
                status=status.HTTP_201_CREATED
            )

        except UserAccess.DoesNotExist:
            return Response(
                RestResponse(
                    RestStatus(False, 404, "User not found"),
                    None
                ).to_dict(),
                status=status.HTTP_404_NOT_FOUND
            )

class BookingDetailView(APIView):
    def get_object(self, id):
        try:
            return BookingItem.objects.get(id=id)
        except BookingItem.DoesNotExist:
            return None

    def get(self, request, id):
        booking_item = self.get_object(id)
        if not booking_item:
            return Response(
                RestResponse(
                    RestStatus(False, 404, "Not Found"),
                    None
                ).to_dict(),
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BookingItemShortSerializer(booking_item)

        return Response(
            RestResponse(
                RestStatus(True, 200, "OK"),
                serializer.data
            ).to_dict(),
            status=status.HTTP_200_OK
        )