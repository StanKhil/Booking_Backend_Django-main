from typing import Any, Dict
import base64, json, re, datetime, time, uuid
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
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404
from django.http import JsonResponse
from main.filters import *
from django.shortcuts import get_object_or_404
from django.utils import timezone

passwordRegex = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!?@$&*])[A-Za-z\d@$!%*?&]{12,}$")

userAccessAccessor = UserAccessAccessor()
accessTokenAccessor = AccessTokenAccessor()

kdfService = PbKdfService()
jwtService = JwtService()
randomService = DefaultRandomService()

class UserViewSet(ModelViewSet):
    queryset = UserAccess.objects.filter(deleted_at__isnull = True)
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserAccessCreateSerializer
        return UserAccessSerializer
    
    #POST /user/
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        response = RestResponse(
            status=RestStatus(True, 201, "Created"),
            data=serializer.data
        )
        return Response(response.to_dict(), status=status.HTTP_201_CREATED)
    
    #PATCH /user/{former_login}
    def patch(self, request, *args, **kwargs):
        login = request.data.get('user-former-login')
        instance = get_object_or_404(UserAccess, login=login)

        first_name = request.data.get('user-first-name')
        if first_name:
            instance.user_data.first_name = first_name

        last_name = request.data.get('user-last-name')
        if last_name:
            instance.user_data.last_name = last_name

        email = request.data.get('user-email')
        if email:
            instance.user_data.email = email

        login = request.data.get('user-login')
        if login:
            instance.login = login

        birthdate = request.data.get('user-birthdate')
        if birthdate:
            instance.birthdate = birthdate

        password = request.data.get('user-password')
        if password:
            salt = randomService.otp(12)
            instance.salt = salt
            instance.dk = kdfService.dk(password, salt)

        role_id = request.data.get('user-role')
        if role_id:
            user_role = UserRole.objects.get(id=role_id)
            instance.user_role = user_role

        instance.save()
        serializer = UserAccessSerializer(instance, context={'request': request})
        response = RestResponse(
            status=RestStatus(True, 200, "Ok"),
            data=serializer.data
        )
        return Response(response.to_dict(), status=200)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = timezone.now()
        instance.save()

        response = RestResponse(
            status=RestStatus(True, 200, "Ok"),
            data=f"User '{login}' deleted successfully"
        )
        return Response(response.to_dict(), status=200)


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

    serializer = UserAccessSerializer(user)
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
        responseObj = RestResponse(status=RestStatus(False, 401, "Unauthorized"), data={"error": e.__str__()})
        return JsonResponse(responseObj.to_dict(), safe=False)
    
    now = int(time.time())
    access_token = AccessToken(
        jti=str(uuid.uuid4()),
        sub=userAccess.id,
        iat=str(now),
        exp=str(now + 1000000),
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
    data = json.loads(request.body)
    errors = processSignUpData(data)
    print(errors)
    if errors.__len__() > 0:
        responseObj = RestResponse(status=RestStatus(False, 400, "Bad Request"), data={"errors": errors})
        return JsonResponse(responseObj.to_dict(), status=400, safe=False) 

    responseObj = RestResponse(status=RestStatus(True, 201, "Created"), data="Registration successful")
    return JsonResponse(responseObj.to_dict(), status=201, safe=False)


def processSignUpData(model: Any) -> Dict[str, str]:
    errors:Dict[str, str] = {}
    
    if not model.get("userFirstName"):
        errors["userFirstName"] = "First Name must not be empty!"
        
    if not model.get("userLastName"):
        errors["userLastName"] = "Last Name must not be empty!"
        
    if not model.get("userEmail"):
        errors["userEmail"] = "Email must not be empty!"
        
    if not model.get("userLogin"):
        errors["userLogin"] = "Login must not be empty!"
    elif ":" in model["userLogin"]:
        errors["userLogin"] = "Login must not contain ':'!"
    
    if UserAccess.objects.filter(login__iexact=model.get("userLogin")).exists():
        errors["userLogin"] = "Login already exists"

    if not model.get("userPassword"):
        errors["userPassword"] = "Password cannot be empty"
        errors["userRepeat"] = "Invalid original password"
    elif not passwordRegex.match(model["userPassword"]):
        errors["userPassword"] = (
            "Password must be at least 12 characters long and contain lower, "
            "upper case letters, at least one number and at least one special character"
        )
        errors["userRepeat"] = "Invalid original password"
    elif model.get("userRepeat") != model.get("userPassword"):
        errors["userRepeat"] = "Passwords must match"
        
    if not model.get("agree"):
        errors["agree"] = "You must agree with policies!"
    if errors:
        return errors
    

    user_id = uuid.uuid4()
    user_data = UserData(
        id = user_id,
        first_name = model["userFirstName"],
        last_name = model["userLastName"],
        email = model["userEmail"],
        birth_date = model["birthdate"] if model["birthdate"] else None,
        registered_at = datetime.datetime.now(), 
    )
    salt = randomService.otp(12)
    user_access = UserAccess(
        id = uuid.uuid4(),
        user_id = user_id,
        login = model["userLogin"],
        salt = salt,
        dk = kdfService.dk(model["userPassword"], salt),
        user_role = UserRole.objects.get(id="SelfRegistered"),
        user_data = user_data
    )

    try:
        user_data.save()
        user_access.save()
    except Exception as e:
        print(e)
        errors["general"] = "Internal server error occured "
    return errors


def getUsersTable(request):
    userAccesses = UserAccess.objects.all()
    tableBodyContent = ""
    for userAccess in userAccesses:
        if userAccess.deleted_at is not None:
            continue
        tableBodyContent +=  f"<tr><td>{userAccess.user_data.first_name}</td> <td>{userAccess.user_data.last_name}</td> <td>{userAccess.user_data.email}</td> <td>{userAccess.login}</td> <td>{userAccess.user_data.birth_date}</td> <td>{userAccess.user_role.id}</td></tr>"
                
        response = RestResponse(
            status=RestStatus(True, 200, "Ok"),
            data = tableBodyContent
        )
    return JsonResponse(response.to_dict(), status=200)