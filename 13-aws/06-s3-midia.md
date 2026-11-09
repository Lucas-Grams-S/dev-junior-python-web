# 6. S3 para arquivos de mídia

> ⏱️ ~1h30 · Módulo 13 · Pré-requisitos: [13.03](03-iam.md), [5.14 (arquivos estáticos e de mídia)](../05-django/README.md), [9.02 (injeção e upload seguro)](../09-seguranca/02-injection-xss.md)

> ✅ **Verificação.** Executado: o passo 1 do `provision.sh` **contra o `moto`**; o código de **upload de imagem de produto** (campo `image`, endpoint, armazenamento por ambiente) com **7 testes novos** (disco e "S3" simulado pelo `moto`), a suíte inteira (**312 testes**), e um **teste ponta a ponta** do pacote de deploy num Compose local: upload pela API, pelo Nginx, e o objeto aparecendo no bucket simulado. **Não executado (sem conta AWS):** um bucket S3 real (consistência, latência, `AccessDenied` verdadeiro, bloqueio de acesso público efetivo, custos). O `moto` guarda o que você manda mas **não aplica** o IAM nem o bloqueio de acesso público. 💸 S3 cobra armazenamento, requisições e **saída de dados**. Código em [`projeto/referencia-api-m13/`](../projeto/referencia-api-m13/README.md).

## 🎯 Objetivos
- Explicar **bucket, objeto, chave** e como o S3 difere de um sistema de arquivos
- Criar um **bucket privado** (bloqueio de acesso público, criptografia, tags) e dar à aplicação **só** o prefixo de que ela precisa
- Servir arquivos privados por **URLs pré-assinadas** e temporárias
- Configurar o Django para **disco em desenvolvimento e S3 em produção**, por variável de ambiente
- Validar **uploads** (tamanho, formato real) e testá-los **sem conta AWS**

## 🤔 Por que isso importa
Uma EC2 pode ser apagada e recriada a qualquer momento; **arquivos enviados pelos usuários não podem morar no disco dela**. O S3 guarda objetos com durabilidade altíssima, por centavos, e vira a casa das imagens dos produtos. Mas é também o serviço dos vazamentos famosos: "bucket público" é manchete. E upload de arquivo é a porta de entrada de vários ataques (aula 9.02).

## 💡 Intuição (explicação simples)
O S3 é um **armário gigante de guarda-volumes**: você entrega um objeto e recebe um **número (a chave)**; para retirar, apresenta a chave. Não há "pastas" de verdade, só etiquetas com barras (`products/cas-049.png`) que *parecem* pastas. O armário é **trancado por padrão**. Para um cliente pegar a foto, você não abre o armário: emite um **ticket temporário** (a URL pré-assinada) válido por alguns minutos para *aquele* objeto.

## 🔬 Como funciona por dentro
- **Bucket:** o contêiner de objetos; o **nome é único no mundo todo** (por isso o script usa `minishop-midia-<ID da conta>`). Pertence a uma região. **Objeto:** os bytes + metadados, identificado pela **chave** (`products/cas-049.png`). Não há renomear nem editar parte do objeto: troca-se o objeto inteiro. O "prefixo" `products/` é só uma convenção de chave, mas é por ele que as políticas IAM restringem acesso.
- **Segurança em camadas.** (1) **Block Public Access** ligado nos quatro itens: nenhuma ACL ou política de bucket consegue tornar objetos públicos por engano. (2) **Criptografia em repouso** (SSE-S3 / AES-256, hoje padrão, mas explícita no script). (3) **Política IAM mínima** para a aplicação (aula 03): `Put/Get/DeleteObject` em `products/*`. (4) **Sem ACL por objeto** (`default_acl=None`): o controle é por políticas.
- **URL pré-assinada (*presigned*).** O servidor, com credenciais próprias, **assina** uma URL de `GET` para uma chave específica e um prazo (`X-Amz-Expires`); quem a possui consegue baixar até expirar, sem credenciais. A assinatura é calculada localmente (não chama a AWS). Importante: **a URL leva a permissão do papel que a assinou**; e o **SigV4** (`X-Amz-Algorithm=AWS4-HMAC-SHA256`) é o esquema atual (o antigo SigV2, com `AWSAccessKeyId=...&Signature=...`, é rejeitado nas regiões novas).
- **No Django.** `django-storages` fornece `S3Storage`; o `ImageField` passa a gravar no bucket e `imagem.url` devolve a URL assinada. A escolha entre disco e S3 é por **variável de ambiente** (12 fatores): sem `AWS_STORAGE_BUCKET_NAME`, usa disco.
- **Upload seguro.** (a) Limite de tamanho (2 MB), (b) **formato verificado pelo conteúdo** (o Pillow abre o arquivo; `foto.png` com texto dentro é rejeitado), (c) nome do arquivo **gerado pelo servidor** (`cas-049.png`, derivado do SKU), nunca o nome enviado pelo usuário, (d) só quem tem `catalog.change_product` envia, (e) o bucket é privado. Em cargas grandes, o navegador pode enviar **direto ao S3** com uma URL pré-assinada de `PUT` (exige CORS no bucket); no curso, o upload passa pela API.
- **Custos.** Armazenamento (GB-mês), **requisições** (PUT/GET custam fração de centavo por mil), e **saída de dados para a internet** (costuma ser o que surpreende); transferência para a mesma região é gratuita. Para o estudo, o custo tende a centavos, **mas apague o bucket** (e as versões, se houver versionamento).

## 🛠️ Exemplo prático
**1. O bucket** (passo 1 do `provision.sh`; no `moto`):
```bash
aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration LocationConstraint="$AWS_DEFAULT_REGION"
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-bucket-tagging --bucket "$BUCKET" --tagging '{"TagSet":[{"Key":"Project","Value":"minishop-curso"}]}'
```
```text
{ BlockPublicAcls: true, IgnorePublicAcls: true, BlockPublicPolicy: true, RestrictPublicBuckets: true }
```
(A `LocationConstraint` é obrigatória fora de `us-east-1`.) Na AWS real, a mesma configuração se confere no console (*Permissions → Block public access*) e com `aws s3api get-public-access-block`.

**2. O modelo e o endpoint.** `Product.image = ImageField(upload_to="products/", blank=True, null=True)` (migração `0002_product_image`). O endpoint (`apps/catalog/api.py`), com as validações no serializer:
```python
@action(detail=True, methods=["post", "delete"], url_path="image", parser_classes=[MultiPartParser])
def image(self, request, pk=None, **kwargs):  # `version` chega por kwargs (URLPathVersioning)
    produto = self.get_object()
    if request.method == "DELETE":
        if produto.image:
            produto.image.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
    ser = ProductImageSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    if produto.image:
        produto.image.delete(save=False)  # não deixa arquivo órfão no bucket
    produto.image.save(f"{produto.sku.lower()}.{ser.validated_data['image'].image.format.lower()}", ser.validated_data["image"])
    return Response(ProductSerializer(produto, context={"request": request}).data)
```
```python
MAX_IMAGE_BYTES = 2 * 1024 * 1024
IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}

class ProductImageSerializer(serializers.Serializer):
    image = serializers.ImageField()
    def validate_image(self, f):
        if f.size > MAX_IMAGE_BYTES:
            raise serializers.ValidationError("A imagem deve ter no máximo 2 MB.")
        if getattr(f.image, "format", None) not in IMAGE_FORMATS:
            raise serializers.ValidationError("Formato não aceito (use JPEG, PNG ou WebP).")
        return f
```
Uma armadilha pega na primeira execução: sem o `**kwargs`, a rota quebrava com `TypeError: ProductViewSet.image() got an unexpected keyword argument 'version'`, porque o versionamento por URL (módulo 6) passa `version` para a ação.

**3. Armazenamento por ambiente** (`config/settings.py`):
```python
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
if os.environ.get("AWS_STORAGE_BUCKET_NAME"):
    # Credenciais: NUNCA aqui. Na EC2 vêm do PAPEL (instance profile) pela cadeia padrão do boto3 (aula 13.03).
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": os.environ["AWS_STORAGE_BUCKET_NAME"],
            "region_name": os.environ.get("AWS_S3_REGION_NAME", "sa-east-1"),
            "endpoint_url": os.environ.get("AWS_S3_ENDPOINT_URL") or None,  # só para testes locais (moto/MinIO)
            "signature_version": "s3v4",   # obrigatória nas regiões novas; o padrão antigo (v2) gera URLs rejeitadas
            "default_acl": None,           # bucket privado, sem ACL por objeto
            "querystring_auth": True,      # URLs assinadas e temporárias
            "querystring_expire": int(os.environ.get("AWS_S3_URL_EXPIRE", "3600")),
            "file_overwrite": False,
        },
    }
```
**Uma descoberta do teste:** a primeira versão sem `signature_version` gerou URLs assim:
```text
https://minishop-midia-teste.s3.amazonaws.com/products/cas-049.png?AWSAccessKeyId=FOOBARKEY&Signature=hlg9W0DDGX...&Expires=1794189049
```
É o **SigV2**, que não funciona nas regiões mais novas; o teste exigia `X-Amz-Signature` e **falhou**, o que me fez fixar `s3v4`. Se eu só tivesse "visto funcionar" com o simulador, esse bug só apareceria em produção.

**4. Testes sem conta AWS** (`tests/test_midia_s3.py`, com o `moto` em memória; credenciais falsas):
```python
@pytest.fixture
def s3(settings, monkeypatch):
    for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        monkeypatch.setenv(k, "teste")                     # FALSAS: o moto não valida
    with mock_aws():
        cliente = boto3.client("s3", region_name="sa-east-1")
        cliente.create_bucket(Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": "sa-east-1"})
        settings.STORAGES = {**settings.STORAGES, "default": {"BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {"bucket_name": BUCKET, "region_name": "sa-east-1", "signature_version": "s3v4",
                        "default_acl": None, "querystring_auth": True, "querystring_expire": 600, "file_overwrite": False}}}
        yield cliente
```
```bash
uv run pytest -q tests/test_midia_s3.py
```
```text
.......                                                                  [100%]
7 passed in 1.40s
```
Os testes cobrem: upload em disco; upload no "S3" com **URL assinada** (`X-Amz-Signature`, `X-Amz-Expires=600`) e **nenhuma permissão pública** no objeto; substituir e remover **sem deixar órfãos**; só quem pode alterar o produto envia (anônimo e `cliente` recebem 401/403 e nada é gravado); rejeição de um **arquivo de texto disfarçado de `.png`**, de um GIF e de uma imagem de **mais de 2 MB**; e produto sem imagem devolvendo `image_url: null`. A suíte completa: **312 passed**. O contrato OpenAPI foi regenerado e validado (`spectacular --validate --fail-on-warn`), e as ferramentas (`ruff`, `mypy`, `lint-imports`, `makemigrations --check`) ficaram limpas.

**5. Ponta a ponta, no pacote de deploy local.** Com o Compose de produção (aula 07) apontado para um PostgreSQL de contêiner (no lugar do RDS) e um `moto` (no lugar do S3):
```bash
curl -s -X POST $B/products/49/image/ -H "Authorization: Bearer $TOKEN" -F "image=@foto.png"
aws s3 ls s3://midia-lab/products/ --endpoint-url http://127.0.0.1:5056
```
```text
image_url: http://moto:5000/midia-lab/products/cas-049.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=teste%2F20261109%2Fsa-...
2026-11-08 22:48:37        103 cas-049.png
```
A requisição passou pelo Nginx, pelo Uvicorn, pelo Django, pela validação e chegou ao "bucket", com a URL SigV4 assinada. (O host `moto:5000` da URL é o do simulador; na AWS seria `https://<bucket>.s3.sa-east-1.amazonaws.com/...`.)

**6. Versões: o `rb --force` não basta (executado no `moto`).** Se o **versionamento** estiver ligado, apagar um objeto só põe um *marcador de exclusão*; as versões continuam (e cobrando). O `aws s3 rb --force` **não apaga versões**. Teste que fiz (bucket versionado com 3 versões/marcadores):
```text
$ aws s3 rb s3://minishop-midia-123456789012 --force
remove_bucket failed: ... An error occurred (BucketNotEmpty) when calling the DeleteBucket operation: The bucket you tried to delete is not empty...
$ uv run python scripts/aws/empty_bucket.py minishop-midia-123456789012
   3 versão(ões)/objeto(s) removido(s) de minishop-midia-123456789012
$ aws s3 rb s3://minishop-midia-123456789012 --force
remove_bucket: minishop-midia-123456789012
```
Por isso o `destroy.sh` chama o `scripts/aws/empty_bucket.py` (boto3: `bucket.object_versions.delete()`) **antes** do `rb`. (A primeira versão do meu script e desta aula afirmava que o `rb --force` esvaziava as versões: **estava errado**, e só o teste com versionamento mostrou.) Para o estudo, uma regra de *lifecycle* que aborta uploads multipart incompletos e expira versões antigas evita lixo invisível.

## 🧠 Pausa para lógica
**Problema.** Uma URL pré-assinada de `GET` expira em 1 hora. (a) Um cliente copia a URL e a posta num fórum. O que acontece? (b) Você troca a imagem do produto pouco depois. A URL antiga ainda funciona? (c) Por que gerar a URL a cada resposta da API (em vez de guardá-la no banco)? (d) Se o papel que assinou a URL perder a permissão de `GetObject` hoje, a URL antiga (ainda não expirada) continua funcionando?

<details><summary>Dica</summary>A URL contém a chave do objeto e uma assinatura; quem a possui é "o portador". O que a assinatura herda?</details>

<details><summary>Solução comentada</summary>

(a) **Qualquer pessoa** com a URL baixa o objeto até expirar: é uma credencial temporária ao portador; por isso prazos curtos e imagens que não são sigilosas por natureza. (b) **Depende, e a nossa API tem uma sutileza:** o código apaga o arquivo antigo e grava o novo com o **mesmo nome** (`cas-049.png`, derivado do SKU); como a chave é a mesma, a URL antiga, ainda válida, passa a servir a **imagem nova** (e navegadores e CDNs podem ter a antiga em cache). Se você quer que a troca invalide as URLs antigas, inclua um identificador único na chave (`cas-049-<uuid>.png`). (c) Porque ela expira e porque o prazo é um parâmetro de configuração; guardar a URL no banco guardaria uma URL **vencida**. Guarde só a chave (o `ImageField` faz isso). (d) **Não**: a URL assinada vale apenas enquanto as credenciais que a assinaram valerem *e* tiverem a permissão (a assinatura é verificada contra o papel que a gerou, no momento do uso); remover a permissão invalida as URLs já emitidas.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| `AccessDenied` ao subir/baixar | Prefixo/ARN da política não bate (`uploads/` × `products/*`) | Corrigir o código ou o prefixo; **não** abrir para `*` |
| `BucketAlreadyExists` / `BucketAlreadyOwnedByYou` | Nome global já usado | Sufixo com o ID da conta; rodar de novo é idempotência |
| `IllegalLocationConstraintException` | Região ≠ `LocationConstraint` | Informar a região do bucket (e não usar em `us-east-1`) |
| URL com `AWSAccessKeyId=…&Signature=…` (SigV2) rejeitada | `signature_version` não definido | `s3v4` |
| Imagem some depois de recriar a EC2 | Estava no disco da instância | `STORAGES` apontando para o S3 |
| `TypeError: image() got an unexpected keyword argument 'version'` | Ação do DRF sem `**kwargs` com versionamento por URL | `def image(self, request, pk=None, **kwargs)` |
| Arquivo `.png` que na verdade é script/texto aceito | Validava só a extensão | Validar pelo conteúdo (Pillow) e gerar o nome no servidor |
| Bucket "público" por engano | ACL/política aberta | Block Public Access ligado nos 4 itens (e verificado) |
| Fatura de S3 com bucket "vazio" ou `BucketNotEmpty` ao apagar | Versões/marcadores e uploads incompletos | `list-object-versions`; `empty_bucket.py`; regra de lifecycle (o `rb --force` **não** apaga versões) |
| Credenciais no `settings.py` | Atalho | Papel de instância / perfil; nunca no código |
- **Privado por padrão, URL assinada com prazo curto.**
- **Chave gerada pelo servidor**; nunca use o nome do arquivo do usuário em caminhos.
- **Apague o objeto antigo ao trocar** (ou use lifecycle) e decida se a chave deve mudar quando o conteúdo muda (cache).
- **Teste com simulador, mas confirme na AWS real** o que o simulador não aplica (permissões, bloqueio público).
- **Não guarde dados pessoais sensíveis em S3 sem criptografia e política** (LGPD, módulo 9.07).

## 🧩 Exercícios
**1. Fixação.** (a) Bucket × objeto × chave. (b) Para que serve o Block Public Access? (c) O que é uma URL pré-assinada e que risco ela tem? (d) Por que `bucket/*` para `PutObject` e `bucket` para `ListBucket`? (e) Por que validar o conteúdo e não só a extensão?

<details><summary>Solução</summary>

(a) Bucket é o contêiner; objeto são os bytes + metadados; chave é o nome único dentro do bucket. (b) Impede que ACLs/políticas tornem objetos públicos. (c) URL com permissão temporária embutida; qualquer portador acessa até expirar. (d) Objetos são `bucket/chave`; listar atua no bucket. (e) A extensão é controlada pelo usuário; o conteúdo é a evidência real.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] Campo `image` + migração + endpoint de upload/remoção + serializer de validação (tamanho e formato real)
- [ ] `STORAGES` por ambiente (disco × S3), `signature_version="s3v4"`, sem credenciais no código
- [ ] **7 testes** do módulo (disco, S3 simulado com URL assinada, sem órfãos, permissões, arquivo disfarçado/GIF/grande, sem imagem) e a suíte inteira verde
- [ ] OpenAPI regenerado e validado; `makemigrations --check` limpo
- [ ] O passo 1 do `provision.sh` no `moto`, e a conferência do bucket (bloqueio de acesso público, tag)
- [ ] Um teste que **falha** de propósito se `signature_version` for removido (a prova do SigV2) ou o relato da descoberta
- [ ] `docs/aws.md`: política da aplicação (`products/*`) e como confirmar, **na AWS real**, o que o simulador não prova
- [ ] Commit `feat(catalog): product images on s3 with presigned urls`

**3. Desafio (opcional).** Implemente o upload **direto do navegador para o S3**: um endpoint que devolve uma URL pré-assinada de `PUT` (`generate_presigned_post`, com condições de tamanho e tipo) e um segundo passo que confirma o objeto no banco. Liste o que muda na política IAM e no CORS do bucket, e por que o servidor precisa **conferir** o objeto depois.

## 🎤 Na entrevista
**1. Como você guarda arquivos enviados por usuários em uma aplicação em nuvem?** Em armazenamento de objetos (S3), fora do disco da instância, com bucket privado, criptografia, política IAM restrita ao prefixo da aplicação e URLs pré-assinadas de curta duração para leitura; o Django usa `django-storages` e a escolha disco/S3 vem de variável de ambiente.

**2. O que é uma URL pré-assinada?** Uma URL com permissão temporária embutida, assinada com as credenciais do servidor, para um objeto e uma operação específicos; quem a tem acessa sem credenciais até expirar. Por isso o prazo deve ser curto.

**3. Como validar um upload de imagem?** Limitar o tamanho, verificar o conteúdo com uma biblioteca de imagem (não confiar na extensão nem no `Content-Type`), gerar o nome do arquivo no servidor, restringir quem pode enviar e armazenar fora do diretório servido como código.

## 📚 Para ir além
- 📄 Documentação oficial: [Bloquear acesso público ao S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html). Os quatro itens e como se aplicam.
- 📄 Documentação oficial: [URLs pré-assinadas](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html). Como funcionam, validade e limites.
- 📄 Documentação oficial: [Excluir um bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-bucket.html). Esvaziar, versões e marcadores.
- 📄 Documentação: [`django-storages` — Amazon S3](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html). Todas as opções usadas (`signature_version`, `querystring_auth`, `default_acl`).
- 📄 Documentação: [Django — gerenciar arquivos](https://docs.djangoproject.com/en/5.2/topics/files/) e [`STORAGES`](https://docs.djangoproject.com/en/5.2/ref/settings/#storages).
- 📄 Documentação: [`moto`](https://docs.getmoto.org/en/latest/). O simulador usado nos testes (leia a seção de limitações).
- 📄 Referência: [OWASP — File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html). Checklist de upload seguro (em inglês).
- 🏋️ Prática extra: escreva o teste que prova que um usuário **sem** `change_product` não consegue sobrescrever a imagem de um produto, **mesmo** conhecendo a URL assinada de outro (e explique por que a URL não dá permissão de escrita).

## ✅ Checklist da aula
- [ ] Sei bucket, objeto, chave, prefixo e URL pré-assinada
- [ ] O bucket é privado (4 itens do Block Public Access), criptografado e com tag
- [ ] A aplicação só alcança `products/*` e não tem credenciais no código
- [ ] Os uploads são validados pelo conteúdo e pelo tamanho; nome gerado pelo servidor
- [ ] Testei disco e S3 simulado e entendi o que o simulador **não** prova
- [ ] Sei o que cobra no S3 e como apagar sem deixar versões
