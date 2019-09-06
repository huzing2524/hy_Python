from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import subprocess


# Create your views here.

class Test(APIView):
    def get(self, request):
        subprocess.run(["git", "pull", "origin", "dev"])
        return Response("test", status=status.HTTP_200_OK)
