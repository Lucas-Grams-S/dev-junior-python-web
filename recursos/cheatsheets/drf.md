# Cheatsheet: DRF (Django REST Framework 3.18)

> Aulas 6.03 a 6.13. Exemplos do MiniShop. Tudo abaixo foi executado no laboratório [`projeto/referencia-api-m6`](../../projeto/referencia-api-m6/README.md).

## Instalação mínima
```bash
uv add djangorestframework djangorestframework-simplejwt django-filter drf-spectacular django-cors-headers
```
```python
INSTALLED_APPS += ["rest_framework", "rest_framework_simplejwt", "rest_framework_simplejwt.token_blacklist",
                   "django_filters", "drf_spectacular", "corsheaders"]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],      # negar por padrão
    "EXCEPTION_HANDLER": "config.errors.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle", "rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/hour", "user": "1000/hour", "login": "5/min"},
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1", "ALLOWED_VERSIONS": ["v1"],
}
```

## Serializer
```python
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)                                  # aninhado (leitura)
    category_slug = serializers.SlugRelatedField(source="category", slug_field="slug",
                                                 queryset=Category.objects.all(), write_only=True)
    in_stock = serializers.SerializerMethodField()                                  # def get_in_stock(self, obj) -> bool

    class Meta:
        model = Product
        fields = ["id", "sku", "name", "price", "stock", "in_stock", "category", "category_slug"]   # NUNCA "__all__"
        read_only_fields = ["slug", "created_at"]

    def validate_sku(self, value): ...          # por campo (devolve o valor normalizado)
    def validate(self, attrs): ...              # entre campos (só roda se os campos passaram)
```
`Serializer(obj).data` · `Serializer(qs, many=True).data` · `Serializer(data=d).is_valid(raise_exception=True)` → `.validated_data` → `.save()` · `partial=True` para `PATCH`.

## Views (do mais baixo ao mais alto)
| Quando | Use |
|---|---|
| endpoint solto | `@api_view(["GET"])` ou `APIView` |
| parte do CRUD | `generics.ListAPIView`, `RetrieveUpdateDestroyAPIView`… |
| CRUD completo | `viewsets.ModelViewSet` (+ `ReadOnlyModelViewSet`) |
| subconjunto | `mixins.CreateModelMixin` + `viewsets.GenericViewSet` |

```python
class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    def get_queryset(self):                                           # escopo = segurança + select_related
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product")
    def get_permissions(self): ...                                    # permissão por ação
    @action(detail=True, methods=["post"])                            # /orders/{pk}/cancel/
    def cancel(self, request, pk=None, **kwargs): ...                 # **kwargs: a URL versionada passa `version`
```
```python
router = DefaultRouter(); router.register("orders", OrderViewSet, basename="order")
path("api/<str:version>/", include("config.api_urls"))
```

## Status e erros
| Situação | Status |
|---|---|
| criado (+`Location`) / ok / sem corpo | `201` / `200` / `204` |
| JSON malformado, campo inválido | `400` (`{campo: [..]}`) |
| sem credencial / token inválido | `401` (+`WWW-Authenticate`) |
| sem permissão | `403` |
| inexistente ou alheio (escopo) | `404` |
| método não permitido / mídia não suportada | `405` / `415` |
| regra de negócio | `422` (`{detail, code}`) |
| limite de taxa | `429` (+`Retry-After`) |

## JWT (simplejwt)
```python
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=15), "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
              "ROTATE_REFRESH_TOKENS": True, "BLACKLIST_AFTER_ROTATION": True}
# POST /auth/token/ → {access, refresh} · POST /auth/token/refresh/ · POST /auth/logout/ (blacklist)
# Cabeçalho: Authorization: Bearer <access>
```

## Permissões
`AllowAny` · `IsAuthenticated` · `IsAuthenticatedOrReadOnly` · `IsAdminUser` · `DjangoModelPermissions[OrAnonReadOnly]` · composição `A & (B | ~C)`.
`has_permission` (view) × `has_object_permission` (só em `get_object()`). Escopo no queryset → `404`; objeto → `403`.

## Filtros, busca, ordenação, paginação, throttling
```python
filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
filterset_class = ProductFilter            # FilterSet: NumberFilter(field_name="price", lookup_expr="gte")
search_fields = ["name", "sku"]            # ?search=
ordering_fields = ["price", "name"]        # lista permitida: ?ordering=-price
pagination_class = NewestFirstCursorPagination   # ou PageNumberPagination (page_size, max_page_size)
throttle_classes = [ScopedRateThrottle]; throttle_scope = "login"
```

## OpenAPI, CORS, testes
```bash
uv run python manage.py spectacular --file schema.yml --validate --fail-on-warn
```
```python
@extend_schema(summary="...", request=None, responses={201: OrderSerializer, 422: ErrorSerializer},
               parameters=[OpenApiParameter("Idempotency-Key", str, OpenApiParameter.HEADER)])
if getattr(self, "swagger_fake_view", False): return Model.objects.none()          # no get_queryset()
CORS_ALLOWED_ORIGINS = ["https://loja.exemplo.com"]; CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_HEADERS = (*default_headers, "idempotency-key")                         # cabeçalho personalizado
```
```python
c = APIClient(); c.force_authenticate(user)                       # permissões (rápido)
c.credentials(HTTP_AUTHORIZATION="Bearer " + access)               # JWT real
c.post(url, dados, format="json"); r.json(); r["Location"]
```

## Regras de bolso
- Listas: `select_related`/`prefetch_related` no `get_queryset()`; o serializer **não** resolve N+1.
- Dinheiro como **string decimal**; datas em **ISO 8601 UTC**; campos em `snake_case`.
- Regra de negócio no **serviço**; a view traduz HTTP; o handler traduz exceções do domínio em 422.
- Todo `POST` que cobra/cria algo caro: `Idempotency-Key`. `GET` nunca altera estado.
- Teste as cinco frentes por endpoint: feliz, validação, 401, 403/404, 422 (+ efeitos no banco).
