from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheck(APIView):
    def get(self, request):
        result = {
            "status_code": 200,
            "detail": "ok",
            "result": "working"
        }
        return Response(result)
