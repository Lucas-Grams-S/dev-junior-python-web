# Checkpoint — Módulo 5: Framework web: Django

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa. 30 min para o quiz, 60 min para a entrega.

## 📝 Quiz (10 questões)
1. Explique o MVT do Django e descreva o caminho de uma requisição, do servidor à resposta. Qual a diferença entre projeto e app?
2. Como o Django escolhe a view de uma URL? Para que servem `name`/`reverse()`, e o que é e como o Django previne CSRF?
3. O que é o *autoescape* dos templates e por que `|safe` em dado de usuário é perigoso? Como funciona a herança de templates?
4. Qual a diferença entre `makemigrations` e `migrate`? `null=True` × `blank=True`? Por que `DecimalField` para dinheiro?
5. O que significa um QuerySet ser *lazy*? Diferença entre `count()`, `len()` e `exists()`. Para que servem `Q` e `F`?
6. Qual a diferença entre `aggregate` e `annotate`? Por que dois `Count` sobre relações diferentes podem inflar o resultado e como corrigir?
7. O que é N+1? Diferença entre `select_related` e `prefetch_related` e como detectar o problema em testes.
8. Como uma CBV processa a requisição (`as_view`, `dispatch`)? Por que a ordem dos *mixins* importa? O que é Post/Redirect/Get e por que não usar `fields = "__all__"`?
9. Como o Django guarda senhas e sessões? Autenticação × autorização? Como funcionam grupos e `PermissionRequiredMixin` (302 × 403) e o que é IDOR?
10. Como você cria um pedido sem vender mais do que existe em estoque? Explique `transaction.atomic`, `select_for_update()`, ordem de bloqueios e por que o preço é copiado para o `OrderItem`. O que você muda no Django ao ir para produção (`DEBUG`, `SECRET_KEY`, estáticos, logs)?

<details><summary>Gabarito</summary>

1. **Model** (dados/ORM), **Template** (apresentação), **View** (lógica que recebe a requisição e devolve a resposta); o roteador de URLs faz o papel de controlador. Caminho: servidor WSGI/ASGI → middlewares (ida) → resolvedor de URLs → view → ORM/SQL → template → middlewares (volta) → cliente. Projeto: configuração e ligação (settings, URLs raiz); app: módulo coeso e reutilizável registrado em `INSTALLED_APPS`.
2. Percorre `urlpatterns` em ordem e usa a primeira rota que casa (`include` delega prefixos). `name` + `reverse()`/`{% url %}` evitam URLs fixas. CSRF: outro site faz o navegador logado enviar uma requisição que muda dados; o Django exige um token secreto (campo/cabeçalho + cookie) em métodos não seguros e devolve `403` sem ele.
3. Escapa `< > & " '` por padrão em `{{ }}`, evitando XSS; `|safe`/`mark_safe` desliga a proteção e, com dado do usuário, permite injetar script. Herança: o filho usa `{% extends %}` e preenche `{% block %}` do pai (`{{ block.super }}` reaproveita o conteúdo).
4. `makemigrations` gera os arquivos comparando models e histórico; `migrate` aplica as pendentes ao banco. `null` é do banco (aceita `NULL`); `blank` é da validação (pode ficar vazio); em texto prefira `blank=True` sem `null`. `DecimalField` guarda valores decimais exatos (sem erro de ponto flutuante).
5. Montar o QuerySet não executa SQL; a consulta roda quando o resultado é necessário (iteração, `len`, `bool`, índice) e fica em cache. `count()` = `COUNT(*)` no banco; `len()` carrega tudo; `exists()` = `SELECT 1 … LIMIT 1`. `Q` compõe condições (`AND/OR/NOT`); `F` referencia colunas na própria consulta (`stock=F("stock")-1`, atômico no banco).
6. `aggregate` resume a consulta inteira (dicionário); `annotate` calcula por objeto/grupo. Dois `JOIN`s multiplicam linhas e inflam as contagens; corrige-se com `distinct=True`, consultas separadas ou `Subquery`.
7. Uma consulta para a lista + uma por objeto para acessar uma relação. `select_related`: `JOIN` em uma consulta (FK/1:1); `prefetch_related`: consulta extra por relação com `IN` e junção em Python (N:N/reverso). Detecta-se contando consultas (`django_assert_max_num_queries`, `CaptureQueriesContext`, debug toolbar, APM).
8. `as_view()` devolve uma função que cria a instância, chama `setup()` e `dispatch()`, que escolhe `get()`/`post()`. Os *mixins* devem vir antes da view base (MRO: a busca de métodos vai da esquerda para a direita). PRG: responder ao POST com redirect para um GET, evitando reenvio ao recarregar. `__all__` expõe campos novos automaticamente (*mass assignment*); liste os permitidos.
9. Senha: hash lento e com sal (PBKDF2-SHA256), `algoritmo$iterações$sal$hash`, comparação em tempo constante. Sessão: o login grava o id na sessão do servidor e envia o cookie `sessionid` (`HttpOnly`); o middleware preenche `request.user`. Autenticação = quem é; autorização = o que pode. Permissões `add/change/delete/view` por model, atribuídas a **grupos**; sem login → 302 para o login; logado sem permissão → 403. IDOR: acessar objeto alheio trocando o id; evita-se filtrando a consulta pelo dono.
10. Dentro de **uma** transação: trava o carrinho e os produtos com `select_for_update()` **sempre na mesma ordem** (evita deadlock), valida o estoque antes de gravar, baixa com `UPDATE … WHERE stock >= n`, cria `Order`/`OrderItem` e esvazia o carrinho; se qualquer passo falhar, `ROLLBACK` desfaz tudo. O preço é copiado para o `OrderItem` porque o preço do catálogo muda e o pedido é um registro histórico. Produção: `DEBUG=False`, `SECRET_KEY` e `ALLOWED_HOSTS` do ambiente, banco real, HTTPS com *cookies* seguros/HSTS, `collectstatic` + servidor de estáticos (WhiteNoise/Nginx/CDN), logs no `stdout`, `check --deploy`.
</details>

## 🛠️ Entrega prática
Repositório `minishop` na tag `v1.0-minishop-django`:
- [ ] Projeto Django 5.2 com apps `catalog`, `accounts`, `cart`, `orders`; usuário customizado (`AbstractUser`) desde a 1ª migração
- [ ] Catálogo: listagem com **busca, filtros, ordenação por lista permitida e paginação**; detalhe, categorias e imagem do produto
- [ ] Models com restrições no banco (`CheckConstraint`, `UniqueConstraint`) e migrações versionadas; **sem N+1** nas telas principais (testado)
- [ ] Admin configurado (listagens, filtros, inlines) e pedidos **somente leitura**
- [ ] Cadastro, login por usuário **ou e-mail**, logout por POST, `next` seguro e e-mail único sem diferenciar maiúsculas
- [ ] Grupos `Estoquista` e `Gerente` criados por *data migration*; telas de produto com `PermissionRequiredMixin`; pedido/carrinho sempre do `request.user`
- [ ] Configuração por ambiente (`.env`, `.env.example`), logging e `check --deploy` sem avisos; estáticos com WhiteNoise e uploads validados
- [ ] Carrinho (`Cart`/`CartItem`) e pedido transacional (`create_order`/`cancel_order`) com preço congelado e estoque controlado
- [ ] `manage.py seed` idempotente e protegido contra produção
- [ ] Testes: `uv run pytest` verde, incluindo rollback, duplo envio, fluxo cadastro→compra→cancelamento e (em PostgreSQL) concorrência na última unidade
- [ ] `manage.py check` e `makemigrations --check` sem pendências; README com “como rodar” em até 5 comandos; `docs/arquitetura.md` (ER) e capturas em `docs/img/`
- [ ] Tag publicada: `git tag -a v1.0-minishop-django -m "MiniShop v1" && git push --follow-tags`

**Prova de fogo (40 min, sem consultar):** (1) numa view de lista, elimine um N+1 de `product.category.name` e prove com um teste de contagem de consultas; (2) escreva `baixar_estoque(sku, qtd)` que **nunca** deixa o estoque negativo mesmo com requisições simultâneas, e explique por que `if p.stock >= qtd: p.stock -= qtd; p.save()` falha; (3) proteja uma view para que só quem tem `catalog.change_product` edite, devolvendo 302 para anônimo e 403 para quem não pode, e escreva os três testes.

## 🪞 Autoavaliação
Nota de 0 a 3. Se algum item ficar em **0 ou 1**, refaça a aula antes de seguir.

| Habilidade | Aula | Nota |
|---|---|---|
| Estrutura de projeto/apps, MVT e ciclo da requisição | 01 | |
| URLs, `reverse`, views de função, CSRF | 02 | |
| Templates: herança, autoescape, filtros, context processors | 03 | |
| Models, migrações, restrições no banco | 04 | |
| ORM: QuerySets lazy, `Q`, `F`, `update()` | 05 | |
| Relacionamentos, `aggregate`/`annotate`, `GROUP BY` | 06 | |
| Detectar e corrigir N+1 | 07 | |
| Django Admin: configuração e riscos | 08 | |
| CBVs, mixins e MRO | 09 | |
| Formulários, validação, PRG | 10 | |
| Autenticação, senhas, sessões, `next` seguro | 11 | |
| Permissões, grupos, IDOR | 12 | |
| Estáticos, mídia e uploads seguros | 13 | |
| Configuração por ambiente e logging | 14 | |
| Paginação, busca e ordenação segura | 15 | |
| Carrinho: serviço, restrições, POST/CSRF | 16 | |
| Pedido transacional, `select_for_update`, deadlock | 17 | |
| Seed idempotente, testes de ponta a ponta, entrega | 18 | |

## 🧠 Lógica: lista de verificação
Resolveu sem olhar: mini WSGI com middlewares (01), roteador com *converters* e `reverse` (02), mini motor de templates (03), leitura do grafo de migrações (04), `Q` de brinquedo (05), `GROUP BY` à mão (06), modelo de custo do N+1 (07), tabela por introspecção (08), MRO C3 (09), validador de CPF (10), mini *hasher* (11), permissões efetivas com ciclos (12), nome de arquivo seguro (13), leitor de `.env` (14), paginação por cursor (15), cupom em centavos (16), pedidos “tudo ou nada” (17), sincronizador idempotente (18)? Marque o que faltou e refaça.

## 🧪 Estado de verificação deste módulo
As aulas 01 a 11 foram geradas numa sessão anterior, com saídas que parecem de execuções reais (não as reverifiquei agora). As aulas **12 a 18** foram escritas **sem o laboratório disponível**: seus blocos de código e as saídas em `text` **não foram executados**. Antes de dar o módulo por concluído, rode no seu projeto os testes dessas aulas e corrija o que divergir (nomes de fixtures, numeração das migrações). Os links de “Para ir além” foram conferidos com HTTP 200 em 2026-11-08.

➡️ Próximo: [Módulo 6 — APIs REST](../06-apis-rest/README.md).
