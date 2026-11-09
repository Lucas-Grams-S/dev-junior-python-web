from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=MeSerializer, summary="Dados do usuário autenticado")
    def get(self, request, *args, **kwargs):
        return Response(MeSerializer(request.user).data)
