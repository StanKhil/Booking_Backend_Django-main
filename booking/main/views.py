from django.shortcuts import render
import base64
from django.http import HttpResponse, Http404
from backend.services import *
from main.models import *
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import *
from .filters import *
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.
#lol, lmao
userAccessAccessor = UserAccessAccessor()
accessTokenAccessor = AccessTokenAccessor()

storageService = DiskStorageService()
kdfService = PbKdfService()
jwtService = JwtService()

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
            {'detail': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = UserDetailSerializer(user)
    return Response(serializer.data)


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
        return JsonResponse({
            "status": 401,
            "data": e.__str__()
        }, status=401)
    
    now = int(time.time())
    access_token = AccessToken(
        jti=str(uuid.uuid4()),
        sub=userAccess.id,
        iat=str(now),
        exp=str(now + 100),
        iss="Booking_WEB",
        aud=str(userAccess.role_id),
        user_access=userAccess
    )

    accessTokenAccessor.create(access_token)
    jwtPayload = {
        "jti": access_token.jti,
        "sub": str(access_token.sub),
        "iat": access_token.iat,
        "exp": access_token.exp,
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

    return JsonResponse({
        "Status": 200,
        "Data": jwt
    })






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

    def get_serializer_class(self):
        if self.action == 'create':
            return RealtyCreateSerializer
        return RealtySerializer



    

