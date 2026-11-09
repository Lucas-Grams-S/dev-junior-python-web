"""A MESMA listagem de categorias escrita em 4 níveis de abstração do DRF."""
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category
from .serializers import CategorySerializer


@api_view(["GET"])                                          # 1) função
def categorias_fn(request):
    return Response(CategorySerializer(Category.objects.all(), many=True).data)


class CategoriasAPIView(APIView):                           # 2) classe, você escreve o get()
    def get(self, request):
        return Response(CategorySerializer(Category.objects.all(), many=True).data)


class CategoriasGeneric(generics.ListAPIView):              # 3) view genérica: só declara o quê
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoriasViewSet(viewsets.ReadOnlyModelViewSet):     # 4) viewset: lista + detalhe, rotas pelo router
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
