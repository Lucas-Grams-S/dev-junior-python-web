from rest_framework.pagination import CursorPagination, PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 20  # padrão
    page_size_query_param = "page_size"  # ?page_size=50 (o cliente pode pedir...)
    max_page_size = 100  # ...mas nunca mais que isso


class NewestFirstCursorPagination(CursorPagination):
    """Cursor opaco: estável com dados mudando e custo constante; não permite 'pular para a página 50'."""

    page_size = 10
    ordering = "-created_at"
