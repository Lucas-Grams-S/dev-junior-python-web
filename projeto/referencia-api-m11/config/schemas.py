from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):
    """Formato de erro geral da API (aula 05). Erros de validação usam {campo: [mensagens]}."""

    detail = serializers.CharField()
    code = serializers.CharField()
