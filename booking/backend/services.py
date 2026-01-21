from abc import ABC, abstractmethod
from django.db.models import Prefetch
from main.models import * 
from pathlib import Path
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
import hashlib, hmac, base64, json, random

# SERVICES

class IKdfService(ABC):
    @abstractmethod
    def dk(self, password: str, salt: str) -> str:
        pass

class PbKdfService(IKdfService):
    def dk(self, password: str, salt: str) -> str:
        c = 3
        dkLength = 20
        t = password + salt
        for i in range(0, c):
            t = self.hash(t)
        return t[0:dkLength]
    
    def hash(self, input:str) -> str:
        return hashlib.sha1(input.encode('utf-8')).hexdigest().upper()
    
class IRandomService(ABC):
    @abstractmethod
    def otp(length: int) -> str:
        pass

class DefaultRandomService(IRandomService):
    def __init__(self):
        self._random = random.Random(time.time())

    def otp(self, length: int) -> str:
        return "".join(str(self._random.randint(0, 9)) for _ in range(length))


class IJwtService(ABC):
    @abstractmethod
    def encodeJwt(payload, header, secret: str) -> str:
        pass

    @abstractmethod
    def decodeFwt(jwt: str, secret:str = None):
        pass

class JwtService:
    _default_secret = "JwtService"

    def _base64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

    def _base64url_decode(self, payload: str) -> bytes:
        rem = len(payload) % 4
        if rem > 0:
            payload += "=" * (4 - rem)
        return base64.urlsafe_b64decode(payload)

    def sign(self, open_part: str, secret: str = None) -> str:
        secret = secret or self._default_secret
        signature_bytes = hmac.new(
            secret.encode('utf-8'),
            open_part.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return self._base64url_encode(signature_bytes)

    def encodeJwt(self, payload: dict, header: dict = None, secret: str = None) -> str:
        secret = secret or self._default_secret
        if header is None:
            header = {"alg": "HS256", "typ": "JWT"}

        header_json = json.dumps(header, separators=(',', ':'))
        payload_json = json.dumps(payload, separators=(',', ':'))
        
        open_part = (
            self._base64url_encode(header_json.encode('utf-8')) + "." +
            self._base64url_encode(payload_json.encode('utf-8'))
        )
        
        signature = self.sign(open_part, secret)
        return f"{open_part}.{signature}"

    def decodeJwt(self, jwt: str, secret: str = None) -> tuple:
        last_dot_index = jwt.rfind('.')
        if last_dot_index == -1:
            raise ValueError("Invalid format: dot was not found")

        secret = secret or self._default_secret
        signature = jwt[last_dot_index + 1:]
        open_part = jwt[:last_dot_index]

        control_sign = self.sign(open_part, secret)
        if not hmac.compare_digest(control_sign, signature):
            raise ValueError("Invalid signature")

        parts = open_part.split('.')
        if len(parts) != 2:
            raise ValueError("Invalid format: dot was not found in openPart")

        header = json.loads(self._base64url_decode(parts[0]).decode('utf-8'))
        payload = json.loads(self._base64url_decode(parts[1]).decode('utf-8'))
        
        return (header, payload)

class IStorageService(ABC):
    @abstractmethod
    def getItemBytes(self, itemName: str) -> bytes:
        pass

    @abstractmethod
    def tryGetMimeType(self, itemName: str) -> str:
        pass

    @abstractmethod
    def saveItem(self, formFile: UploadedFile) -> str:
        pass

class DiskStorageService(IStorageService):
    def __init__(self):
        self.basePath = Path(settings.STORAGE_PATH)

    def getItemBytes(self, itemName: str) -> bytes:
        path = self.basePath / itemName
        if path.exists():
            return path.read_bytes()
        raise FileNotFoundError(f"File '{itemName}' was not found in storage.")

    def tryGetMimeType(self, itemName: str) -> str:
        ext = self._getFileExtension(itemName).lower()
        mapping = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".bmp": "image/bmp",
            ".svg": "image/svg+xml",
        }
        if ext in mapping:
            return mapping[ext]
        raise ValueError(f"Unsupported exception '{ext}'")

    def saveItem(self, formFile: UploadedFile) -> str:
        ext = self._getFileExtension(formFile.name)
        savedName = f"{uuid.uuid4()}{ext}"
        path = self.basePath / savedName

        with open(path, 'wb+') as destination:
            for chunk in formFile.chunks():
                destination.write(chunk)

        return savedName
    
    def _getFileExtension(self, filename: str) -> str:
        dotIndex = filename.rfind(".")
        if dotIndex < 0:
            raise ValueError("File name must have an extension")
        return filename[dotIndex:]


#   ACCESSORS

class UserAccessAccessor:
    def __init__(self):
        pass
    
    def getUserAccessByLogin(selfm, userLogin: str, isEditable: bool = False) -> UserAccess:
        bookings = Prefetch('bookingitems', queryset=BookingItem.objects.filter(deleted_at__isnull=True))
        feedbacks = Prefetch('feedbacks', queryset=Feedback.objects.filter(deleted_at__isnull=True))
  
        #query = UserAccess.objects.select_related('user_data', "user_role").prefetch_related(bookings, feedbacks)
        query = UserAccess.objects.select_related('user_data', "user_role")
        try:
            return query.get(login=userLogin, user_data__deleted_at__isnull=True)
        except UserAccess.DoesNotExist:
            return None
        
class AccessTokenAccessor:
    def create(self, accessToken: AccessToken) -> AccessToken:
        accessToken.save()
        return accessToken
