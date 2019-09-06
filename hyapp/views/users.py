from rest_framework.views import APIView
from rest_framework import status
from hyapp.utils import util_response
from hyapp.e import ecode

import base64


class UserAPI(APIView):
    def get(self, request):
        token = request.META.get("HTTP_AUTHORIZATION")
        token = base64.b64decode(token).split(':')
        if len(token) != 2:
            return util_response(http_status=status.HTTP_400_BAD_REQUEST, code=ecode.InvalidParams)
