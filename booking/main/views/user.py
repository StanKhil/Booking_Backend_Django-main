from typing import Any, Dict
import base64
import json
import re
import datetime
import time
import uuid
from backend.services import *
from main.models import *
from main.rest import *
from main.serializers.user import *
from main.serializers.booking import *
from main.serializers.realty import *
from main.serializers.feeedback import *
from main.serializers.location import *
from main.filters import *
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