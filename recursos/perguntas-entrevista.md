# Perguntas de entrevista (banco consolidado)

## Módulo 0
**1. O que `chmod 755 script.sh` faz?** Dono: leitura, escrita e execução (7); grupo e outros: leitura e execução (5).
**2. Diferença entre `>` e `>>`?** `>` sobrescreve; `>>` acrescenta.
**3. O que é o `PATH`?** Lista ordenada de pastas onde o shell procura os programas.
**4. Por que usar ambiente virtual?** Isolar dependências por projeto e tornar o ambiente reproduzível.
**5. Para que serve um lockfile?** Fixar versões exatas, inclusive indiretas, para todos instalarem o mesmo.
**6. `git merge` vs `git rebase`?** Merge preserva o histórico com commit de junção; rebase reaplica commits sobre outra base (histórico linear, reescrito; não use em branch compartilhada).
**7. O que é staging area?** Onde se escolhe o que entra no próximo commit.
**8. Commitei uma senha. E agora?** Revogar/trocar o segredo primeiro; depois limpar o histórico se preciso.
**9. Como resolve um conflito de merge?** Escolher/combinar as versões, remover marcadores, testar, `git add`, concluir o merge.
**10. Por que não usar `git push --force` na main?** Reescreve histórico compartilhado e pode apagar commits alheios.
**11. Como investiga um bug?** Reproduzir de forma mínima, ler o traceback de baixo para cima, hipótese, breakpoint/log, corrigir, teste de regressão.
**12. Você usa IA para programar?** Sim, para explicar erros e tarefas repetitivas; leio, entendo e testo tudo, não envio segredos e confiro na documentação oficial.

## Módulo 1 — Python
**13. Por que `0.1 + 0.2 != 0.3`?** `float` é binário (IEEE 754); use `Decimal` ou centavos inteiros para dinheiro.
**14. Tipagem do Python?** Dinâmica e forte.
**15. O que é *truthy/falsy*?** Valores usados como condição; falsy: `False`, `None`, `0`, vazios.
**16. `==` vs `is`?** Valor vs identidade; `is None`.
**17. Qual o problema de `def f(x, lst=[])`?** O padrão é criado uma vez e compartilhado; use `None`.
**18. O que é LEGB?** Ordem de busca de nomes: Local, Enclosing, Global, Built-in.
**19. Lista vs tupla?** Mutável vs imutável (tupla pode ser chave); `x in lista` O(n).
**20. Por que dict/set são rápidos?** Tabela hash, O(1) médio; chaves precisam ser hashable.
**21. `b = a` copia a lista?** Não; `copy()`/`list(a)`; `deepcopy` para aninhados.
**22. `except Exception` vs `except:`?** O segundo captura até `KeyboardInterrupt`; prefira tipos específicos.
**23. Para que serve `finally` e `raise ... from`?** Executa sempre; encadeia a causa.
**24. Por que `with open(..., encoding="utf-8")`?** Fecha o arquivo com segurança e fixa a codificação.
**25. `json.load` vs `json.loads`?** Arquivo vs string.
**26. Módulo vs pacote? O que faz `if __name__ == "__main__"`?** Arquivo vs pasta; executa só quando rodado diretamente.
**27. O que é um bom teste unitário e para que serve `parametrize`?** Pequeno, rápido, independente; mesmo teste com vários dados.
**28. `self`, `@classmethod`, `@staticmethod`?** Instância atual; recebe a classe; função sem `self`/`cls`.
**29. Herança vs composição?** “É um” vs “tem um”; prefira composição.
**30. `__str__` vs `__repr__`?** Usuário vs desenvolvedor.
**31. Type hints são checados em execução?** Não; mypy/Pydantic/FastAPI os usam.
**32. Iterável vs iterador; o que faz `yield`?** `__iter__` vs `__next__`; pausa e devolve valor preservando estado.
**33. O que é um decorator e por que `functools.wraps`?** Função que embrulha outra; preserva metadados.
**34. O que é Big-O e quais as complexidades de `x in lista`, `x in set`, `sorted`?** Crescimento do custo; O(n), O(1) médio, O(n log n).
**35. Como evitar `RecursionError`?** Caso base correto, iteração ou memoização.

## Módulo 2 — Web e HTTP
**36. O que acontece quando você digita uma URL e aperta Enter?** DNS → TCP (handshake) → TLS → requisição HTTP → servidor processa → resposta → renderização.
**37. TCP vs UDP?** Confiável, ordenado e com conexão vs sem garantias e mais leve.
**38. `127.0.0.1` vs `0.0.0.0`?** Loopback (só a máquina) vs todas as interfaces ao escutar.
**39. `Connection refused` vs timeout?** Ninguém atende na porta vs nenhuma resposta (firewall/rota).
**40. O que significa HTTP ser *stateless*?** Cada requisição é independente; estado vem por cookie/token ou banco.
**41. GET vs POST vs PUT vs PATCH vs DELETE?** Leitura segura; criação/ação não idempotente; substituição idempotente; alteração parcial; remoção idempotente.
**42. 401 vs 403? 400 vs 422? 404 vs 410?** Não autenticado vs sem permissão; formato inválido vs regra de negócio; não existe vs removido para sempre.
**43. O que o HTTPS garante?** Confidencialidade, integridade e autenticidade do servidor via certificado de uma CA.
**44. Como funciona uma sessão com cookie? Para que `HttpOnly`/`Secure`/`SameSite`?** ID aleatório ↔ dados no servidor; bloqueia JS, exige HTTPS, limita cross-site.
**45. Sessão vs JWT?** Estado no servidor (revogável) vs estado assinado no cliente (sem consulta, difícil revogar).
**46. O que é idempotência e por que importa?** Repetir não muda o resultado além da primeira vez; permite retentativas seguras (pagamentos, webhooks).
**47. Como depurar uma chamada de API que falha?** Reproduzir com `curl`/Bruno, ver status/corpo/headers, comparar com o DevTools, olhar logs.
**48. O que é TTFB e p95?** Tempo até o 1º byte (lentidão do servidor) e o tempo abaixo do qual ficam 95% das requisições (cauda lenta).
**49. Por que não usar `http.server` em produção?** Sem foco em segurança/desempenho; use Gunicorn/Uvicorn atrás de um proxy reverso.
**50. O que um framework web faz?** Roteia, parseia a requisição, valida, trata erros, serializa e integra com servidor WSGI/ASGI.

## Módulo 3 — Banco de dados e SQL
**51. Por que usar um banco em vez de arquivos?** Concorrência segura, índices, integridade, durabilidade e linguagem declarativa.
**52. PK vs FK? Como modelar N:N?** Identifica a linha / referencia a PK de outra tabela; tabela de junção com duas FKs.
**53. O que é normalização (1FN, 2FN, 3FN)?** Eliminar redundância: valores atômicos; nada depende de parte da chave; nada depende de coluna não-chave.
**54. Quando desnormalizar?** Totais, contadores e relatórios, com plano de consistência; `unit_price` é histórico, não desnormalização.
**55. Ordem lógica de um SELECT?** FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT.
**56. WHERE vs HAVING?** Filtra linhas antes / grupos depois da agregação.
**57. INNER vs LEFT vs FULL JOIN? Como achar o que não tem par?** Só pares / todo o esquerdo / ambos; `LEFT JOIN ... IS NULL` ou `NOT EXISTS`.
**58. Por que `WHERE col = NULL` não funciona e `NOT IN` falha com NULL?** Comparação com NULL é desconhecida; use `IS NULL` e `NOT EXISTS`.
**59. O que é um índice e qual o custo? Como investigar uma consulta lenta?** B-tree que acelera leitura e atrasa escrita; `EXPLAIN (ANALYZE, BUFFERS)`.
**60. Em um índice `(a, b)` a ordem importa?** Sim: serve `a` e `a+b`; só `b` não (exceto skip scan no PG 18 com `a` de poucos valores).
**61. OFFSET grande é um problema? Alternativa?** Descarta linhas; use paginação por cursor (keyset).
**62. O que é ACID?** Atomicidade, Consistência, Isolamento, Durabilidade.
**63. Níveis de isolamento e anomalias?** READ COMMITTED (padrão), REPEATABLE READ, SERIALIZABLE; leitura não repetível, fantasma, lost update, write skew.
**64. Como evitar vender o mesmo item duas vezes?** `UPDATE ... WHERE stock >= n` atômico ou `SELECT ... FOR UPDATE`, em transação.
**65. O que é um deadlock?** Duas transações esperando travas uma da outra; prevenir com ordem fixa e transações curtas.
**66. O que é SQL injection e como evitar?** Concatenar entrada ao SQL; parametrizar, allowlist para identificadores, menor privilégio.
**67. O que é um ORM? Prós e contras? O que é N+1?** Mapeia objetos ↔ tabelas; produtividade e segurança vs SQL opaco e N+1.
**68. Para que servem migrações? Por que não editar uma aplicada?** Versionar o schema; outros ambientes já a aplicaram.
**69. Redis, MongoDB, PostgreSQL: quando cada um?** Cache/filas; documentos flexíveis; fonte da verdade relacional (com `jsonb`).
**70. Como testar um backup?** Restaurar em outro banco e comparar contagens/somas e rodar verificações.

## Módulo 4 — Front-end
**71. O que é HTML semântico e por que importa?** Tags pelo significado; acessibilidade, SEO e manutenção.
**72. Como um formulário vira uma requisição HTTP? `GET` × `POST`? Basta validar no navegador?** Campos com `name`; query string × corpo; não: o servidor revalida.
**73. Como o CSS decide qual regra aplicar?** Importância, especificidade (ids, classes, tags) e ordem; herança em algumas propriedades.
**74. O que é o box model e `box-sizing: border-box`?** Conteúdo+padding+borda+margem; `width` incluindo padding e borda.
**75. Flexbox × Grid? O que é mobile-first?** 1D × 2D; CSS base para o celular e `min-width` para ampliar.
**76. `==` × `===`, `var`/`let`/`const`, `null` × `undefined`?** Coerção × estrita; escopo; vazio intencional × não definido.
**77. O que é uma closure?** Função que lembra as variáveis do escopo onde nasceu.
**78. Por que `0.1 + 0.2 !== 0.3` e como tratar dinheiro em JS?** Double IEEE 754; centavos inteiros e `Intl`.
**79. Como funciona o event loop?** Uma thread; microtarefas (Promises) antes das tarefas (timers/eventos).
**80. O que `fetch` faz com 404/500? E com servidor fora do ar?** Resolve com `ok:false` / rejeita com `TypeError`.
**81. `textContent` × `innerHTML`? O que é XSS?** Texto × HTML interpretado; injeção de script por dado não escapado.
**82. Event bubbling e delegação? E debounce?** Subida do evento; um listener no contêiner; esperar o usuário parar.
**83. O que é CORS e por que há `OPTIONS`?** Autorização por cabeçalhos, imposta pelo navegador; preflight para requisições não simples.
**84. Como lidar com respostas fora de ordem em buscas?** Numerar requisições, `AbortController`, descartar as obsoletas.
**85. Por que `new Date("2026-12-25")` mostra o dia 24 no Brasil?** É UTC; use a data local ou `Temporal`.
**86. React/Vue × HTMX × templates do servidor?** Componentes reativos no cliente × HTML do servidor trocado por atributos × páginas completas.
**87. Como você garante acessibilidade?** Semântica, `label`, `alt`, foco visível, contraste ≥ 4,5:1, ARIA só se preciso; axe/Lighthouse + teste de teclado e leitor de tela.
**88. Qual a primeira regra do ARIA?** Use o elemento HTML nativo antes de adicionar ARIA.

## Módulo 5 — Django

**89. Explique o padrão MVT do Django.** Model (dados e regras, ORM), Template (apresentação em HTML) e View (função/classe que recebe o `HttpRequest`, usa o modelo e devolve a resposta); o roteador de URLs do framework faz o papel de controlador. É o MVC com nomes diferentes. *(aula 5.01)*
**90. Descreva o caminho de uma requisição no Django.** O servidor (Gunicorn/Uvicorn) chama a aplicação WSGI/ASGI → *middlewares* (ida) → resolvedor de URLs → view → ORM/SQL → template → resposta volta pelos *middlewares* (volta) → servidor → cliente. *(aula 5.01)*
**91. Qual a diferença entre projeto e app?** Projeto é a configuração e a ligação (settings, URLs raiz, WSGI); app é um módulo coeso e reutilizável (modelos, views, URLs) registrado em `INSTALLED_APPS`. *(aula 5.01)*
**92. Para que serve o middleware? Dê exemplos.** Processar todas as requisições/respostas de forma transversal: sessões, autenticação, CSRF, segurança, compressão, métricas; a ordem na lista importa. *(aula 5.01)*
**93. Por que não usar `runserver` em produção?** Foi feito para desenvolvimento (um processo, sem foco em segurança/desempenho); usa-se um servidor WSGI/ASGI (Gunicorn/Uvicorn) atrás de um proxy reverso. *(aula 5.01)*
**94. Como o Django escolhe qual view atende uma URL?** Percorre `urlpatterns` do `ROOT_URLCONF` em ordem e usa a primeira rota que casa; `include` delega prefixos a outros módulos; os *converters* capturam parâmetros. *(aula 5.02)*
**95. Para que servem `name` e `reverse()`?** Dar nomes às rotas e gerar URLs a partir deles, evitando URLs fixas no código e nos templates. *(aula 5.02)*
**96. O que é CSRF e como o Django o previne?** Ataque em que outro site faz o navegador logado enviar uma requisição que altera dados; o Django exige um token secreto (cookie + campo/cabeçalho) em métodos não seguros, e responde `403` se faltar. *(aula 5.02)*
**97. Qual a diferença entre `HttpResponse`, `JsonResponse` e `redirect`?** Resposta genérica (texto/HTML, status e cabeçalhos livres), resposta com corpo JSON e `Content-Type: application/json`, e resposta `301/302` com `Location`. *(aula 5.02)*
**98. Como você restringe os métodos HTTP de uma view?** Com `@require_http_methods([...])` (ou `require_GET`/`require_POST`), que devolve `405` com o cabeçalho `Allow`. *(aula 5.02)*
**99. O que é o *autoescape* do Django e por que importa?** Escapa por padrão `< > & " '` em tudo que é impresso com `{{ }}`, evitando XSS; só deixa passar HTML marcado como seguro (`|safe`/`mark_safe`), que nunca deve ser aplicado a dados de usuário. *(aula 5.03)*
**100. Como funciona a herança de templates?** O *template* filho usa `{% extends "base.html" %}` e preenche os `{% block %}` definidos pelo pai; o que não sobrescreve vem do pai; `{{ block.super }}` reaproveita o conteúdo do bloco do pai. *(aula 5.03)*
**101. Quando criar um filtro ou *template tag* próprio?** Para formatação/apresentação reutilizável (moeda, datas, botões); regras de negócio ficam fora do template. *(aula 5.03)*
**102. O que é um *context processor*?** Função que recebe a requisição e devolve um dicionário injetado no contexto de todos os templates renderizados com `RequestContext` (por exemplo, usuário, mensagens, nome do site). *(aula 5.03)*
**103. Por que não colocar consultas ao banco no template?** O template é só apresentação; acessar relações dentro de laços gera consultas extras (N+1) e esconde custo; prepare os dados na *view*/modelo com `select_related`/`prefetch_related`. *(aula 5.03)*
**104. O que é uma migração e por que usar?** Um arquivo versionado que descreve uma mudança no schema (e/ou nos dados), aplicado de forma ordenada e registrado em uma tabela de controle; garante que todos os ambientes tenham o mesmo banco e permite desfazer passos. *(aula 5.04)*
**105. Qual a diferença entre `makemigrations` e `migrate`?** `makemigrations` gera os arquivos comparando os modelos com o histórico; `migrate` executa as migrações pendentes no banco. *(aula 5.04)*
**106. `null=True` × `blank=True`?** `null` é do banco (aceita `NULL`); `blank` é da validação (pode ficar vazio). Para texto, prefira `blank=True` sem `null`. *(aula 5.04)*
**107. Por que `DecimalField` para dinheiro?** Evita o erro de ponto flutuante: `numeric` no banco e `Decimal` no Python armazenam e calculam valores decimais exatos. *(aula 5.04)*
**108. Como você altera uma tabela grande sem derrubar a produção?** Com mudanças compatíveis e em etapas (campo nulo → preencher em lotes → endurecer), índices criados de forma concorrente e deploy em duas fases (código compatível com o schema antigo e o novo). *(aula 5.04)*
**109. O que significa um QuerySet ser *lazy*?** Montar o QuerySet não executa SQL; a consulta só roda quando o resultado é necessário (iteração, `len`, `bool`, índice, `list`), e fica em cache no objeto. *(aula 5.05)*
**110. Diferença entre `count()`, `len()` e `exists()`?** `count()` faz `COUNT(*)` no banco; `len()` carrega todos os objetos e conta em Python; `exists()` faz um `SELECT 1 … LIMIT 1`, mais barato para saber se há resultados. *(aula 5.05)*
**111. O que são `Q` e `F`?** `Q` compõe condições com `AND/OR/NOT`; `F` referencia uma coluna dentro da consulta (comparações entre campos e atualizações calculadas no banco, como `stock = stock - 1`). *(aula 5.05)*
**112. Como evitar *lost update* ao baixar estoque?** Com `update(stock=F("stock") - n)` filtrando `stock__gte=n` (uma instrução atômica) e conferindo o nº de linhas afetadas, ou `select_for_update()` dentro de uma transação. *(aula 5.05)*
**113. O que `bulk_create`/`update()`/`delete()` não fazem?** Não chamam `save()`/`delete()` dos modelos nem emitem sinais, e `update()` não atualiza `auto_now`; em troca, executam em uma ou poucas instruções SQL. *(aula 5.05)*
**114. Como modelar e usar um relacionamento muitos-para-muitos no Django?** Com `ManyToManyField` (o Django cria a tabela de junção); acesso por `produto.tags` e, no reverso, `tag.products`; com atributos na relação usa-se `through=` com um modelo próprio (por exemplo, `OrderItem`). *(aula 5.06)*
**115. Qual a diferença entre `aggregate` e `annotate`?** `aggregate` calcula resumos sobre a consulta inteira e devolve um dicionário; `annotate` calcula por objeto/grupo e adiciona atributos aos resultados; com `values()` antes, vira `GROUP BY`. *(aula 5.06)*
**116. O que é `related_name`?** O nome do acessor da relação **reversa**; deixa o código legível (`categoria.products`) e define o prefixo nos filtros reversos. *(aula 5.06)*
**117. Por que `Count` com dois relacionamentos pode dar resultado errado?** Os `JOIN`s multiplicam as linhas (produtos × etiquetas) e a contagem infla; corrige-se com `distinct=True`, consultas separadas ou `Subquery`. *(aula 5.06)*
**118. Como filtrar depois de agregar?** `annotate(...).filter(campo__gte=…)` gera `HAVING`; já `filter()` antes do `annotate()` gera `WHERE`. *(aula 5.06)*
**119. O que é o problema N+1 e como resolver no Django?** Uma consulta para listar objetos e uma consulta adicional por objeto para acessar uma relação; resolve-se com `select_related` (FK/1:1, `JOIN`), `prefetch_related` (N:N/reverso, consulta com `IN`) ou `annotate` quando só se precisa de agregados. *(aula 5.07)*
**120. Diferença entre `select_related` e `prefetch_related`?** O primeiro faz um `JOIN` e traz tudo em **uma** consulta (relações “para um”); o segundo faz uma **consulta extra por relação** e junta em Python (relações “para muitos”), evitando multiplicar linhas. *(aula 5.07)*
**121. Como você detecta N+1 em um projeto?** Contando consultas por requisição (cabeçalho/`django-debug-toolbar`/APM/logs), `CaptureQueriesContext` e testes com `assertNumQueries`/`django_assert_num_queries`. *(aula 5.07)*
**122. O que é `Prefetch` com `to_attr`?** Um objeto que personaliza o `prefetch_related`: define o `queryset` dos relacionados (filtro/ordem) e o atributo onde guardá-los, evitando novas consultas. *(aula 5.07)*
**123. Por que o N+1 só aparece em produção?** Porque depende da escala (muitos objetos) e da latência de rede até o banco; em desenvolvimento, com poucos dados e banco local, parece rápido. *(aula 5.07)*
**124. O que é o Django Admin e como funciona?** Interface de gestão gerada automaticamente a partir dos modelos registrados (via introspecção de `_meta`), com CRUD, autenticação (`is_staff`), permissões por modelo, busca, filtros e histórico; é personalizada pela classe `ModelAdmin`. *(aula 5.08)*
**125. Como personalizar a listagem e o formulário?** Com `list_display`, `list_filter`, `search_fields`, `list_editable`, `fieldsets`, `readonly_fields`, `prepopulated_fields`, *inlines* e `actions`. *(aula 5.08)*
**126. O Admin deve ser usado pelos clientes finais?** Não: é uma ferramenta interna para a equipe, com UX genérica e acesso amplo; interfaces de cliente usam *views*/APIs próprias com as regras de negócio e permissões adequadas. *(aula 5.08)*
**127. Como proteger o Admin em produção?** Senhas fortes e 2FA, URL não óbvia, restrição de rede (VPN/IP), permissões mínimas por grupo (staff sem superuser), limite de tentativas, HTTPS e auditoria dos acessos. *(aula 5.08)*
**128. O que `queryset.update()` em uma ação do Admin deixa de fazer?** Não chama `save()` nem sinais, não atualiza `auto_now` e não gera `LogEntry`; para auditoria por objeto é preciso iterar com `save()` ou registrar manualmente. *(aula 5.08)*
**129. Como uma CBV processa uma requisição?** `as_view()` devolve uma função que cria uma instância da classe, chama `setup()` e `dispatch()`, que escolhe `get()`/`post()` conforme o verbo; nas views genéricas esses métodos chamam ganchos como `get_queryset()` e `get_context_data()` e renderizam o template. *(aula 5.09)*
**130. Quando usar CBV e quando função?** CBV quando há padrão repetido (CRUD/listagens) ou necessidade de herança/*mixins*; função quando a lógica é simples e única; evitar hierarquias profundas. *(aula 5.09)*
**131. O que é um *mixin* e por que a ordem na herança importa?** Classe pequena que adiciona comportamento a outras; a ordem define a MRO, e os *mixins* devem vir **antes** da view base para que seus métodos (que chamam `super()`) sejam encontrados primeiro. *(aula 5.09)*
**132. O que é a MRO?** A ordem em que o Python procura métodos em herança múltipla (algoritmo C3): a própria classe, depois as bases da esquerda para a direita, sem repetições, respeitando as hierarquias. *(aula 5.09)*
**133. Por que não guardar estado em atributos de classe de uma view?** Eles são compartilhados entre todas as requisições e *threads*; o estado de uma requisição deve ficar na instância (`self`), que é criada por requisição. *(aula 5.09)*
**134. Como funciona a validação de um formulário Django?** Os dados chegam como texto; cada campo converte e valida, depois rodam `clean_<campo>()` e `clean()`; `is_valid()` preenche `cleaned_data` e `errors`. *(aula 5.10)*
**135. Form × ModelForm?** `Form` define campos manualmente; `ModelForm` os deriva do modelo, valida unicidade e tem `save()`. *(aula 5.10)*
**136. O que é Post/Redirect/Get e por quê?** Responder a um POST bem-sucedido com redirect para um GET, evitando duplicidade ao recarregar. *(aula 5.10)*
**137. O que é CSRF e como o Django protege?** Ataque em que um site malicioso faz o navegador logado enviar uma requisição; o Django exige um token secreto por formulário/sessão em métodos não seguros. *(aula 5.10)*
**138. Por que não usar `fields = "__all__"`?** Expõe automaticamente campos novos e abre brecha para *mass assignment*; liste os campos permitidos. *(aula 5.10)*
**139. Como o Django armazena senhas?** Hash lento e com sal (PBKDF2-SHA256 por padrão), no formato `algoritmo$iterações$sal$hash`; `check_password` recalcula e compara em tempo constante, e atualiza hashes antigos. *(aula 5.11)*
**140. Como funciona a sessão?** O login grava o id do usuário numa sessão no servidor e envia ao navegador um cookie `sessionid` aleatório (`HttpOnly`); o middleware carrega a sessão e preenche `request.user`. *(aula 5.11)*
**141. Autenticação × autorização?** Quem é × o que pode. *(aula 5.11)*
**142. O que é *open redirect* e como o Django evita?** Redirecionar o usuário a um site arbitrário via parâmetro `next`; o Django só aceita destinos do mesmo host (`url_has_allowed_host_and_scheme`). *(aula 5.11)*
**143. Por que um modelo de usuário customizado desde o início?** Trocar `AUTH_USER_MODEL` depois das migrações é muito difícil; começar com `AbstractUser` custa nada e dá liberdade. *(aula 5.11)*
**144. Como funcionam permissões no Django?** Cada model ganha `add/change/delete/view`; atribuímos a usuários ou, melhor, a **grupos**. `user.has_perm("app.codename")` considera diretas e de grupo; superusuário tem todas. Nas views, `PermissionRequiredMixin`. *(aula 5.12)*
**145. Diferença entre 401, 403 e 404 nesse contexto?** 401: não autenticado; 403: autenticado sem permissão; 404 pode ser usado de propósito para **não revelar** a existência de um recurso alheio. *(aula 5.12)*
**146. O que é IDOR e como evitar?** Acesso a objetos de outros trocando o identificador; evita-se filtrando sempre a consulta pelo usuário/dono ou checando a regra por objeto. *(aula 5.12)*
**147. Qual a diferença entre `STATIC_ROOT`, `STATICFILES_DIRS` e `MEDIA_ROOT`?** `STATICFILES_DIRS`: onde estão seus estáticos extras; `STATIC_ROOT`: para onde o `collectstatic` os reúne para produção; `MEDIA_ROOT`: onde ficam os uploads. *(aula 5.13)*
**148. Por que o CSS some quando `DEBUG=False`?** O `runserver` só serve estáticos em modo debug; em produção é preciso `collectstatic` e um servidor (WhiteNoise, Nginx, CDN). *(aula 5.13)*
**149. Quais cuidados em uploads?** Limitar tamanho e tipos, validar o conteúdo, gerar o nome do arquivo, não executar nem servir com permissão de execução, e guardar fora do disco efêmero (S3). *(aula 5.13)*
**150. Como você gerencia segredos e configuração?** Variáveis de ambiente (12-factor), `.env` só em desenvolvimento e fora do Git, `.env.example` como documentação; em produção, o gerenciador da plataforma (AWS Parameter Store/Secrets Manager). *(aula 5.14)*
**151. O que você muda ao colocar o Django em produção?** `DEBUG=False`, `SECRET_KEY` própria, `ALLOWED_HOSTS`, banco real, HTTPS com *cookies* seguros e HSTS, estáticos coletados, logs no `stdout`; confirmo com `check --deploy`. *(aula 5.14)*
**152. Quando usar cada nível de log?** `DEBUG` detalhe; `INFO` eventos normais relevantes; `WARNING` situação inesperada, mas tolerável; `ERROR` falha; `CRITICAL` sistema comprometido. Sem dados sensíveis. *(aula 5.14)*
**153. Como paginar uma listagem grande?** No banco, com `LIMIT/OFFSET` (`Paginator`/`paginate_by`), sempre com ordem estável; para dados enormes ou *feeds*, paginação por cursor, que mantém custo constante. *(aula 5.15)*
**154. Por que `OFFSET` fica lento nas páginas finais?** O banco precisa ler e descartar todas as linhas anteriores; o cursor usa um índice e vai direto à posição. *(aula 5.15)*
**155. Como evitar que a busca vire um problema de segurança ou desempenho?** Parâmetros sempre pelo ORM (sem concatenar SQL), ordenação por lista permitida, validação dos filtros, `select_related` para evitar N+1 e índices/busca de texto quando `LIKE '%x%'` não escalar. *(aula 5.15)*
**156. Como você modelaria um carrinho?** `Cart` ligado ao usuário (ou à sessão) e `CartItem` com produto e quantidade, único por (carrinho, produto) e com quantidade > 0 como restrição do banco. Preço lido do produto; congelado só no pedido. *(aula 5.16)*
**157. Por que nunca confiar no preço enviado pelo cliente?** Tudo que vem do navegador pode ser alterado; o servidor decide o preço e valida estoque e quantidade. *(aula 5.16)*
**158. Como evitar erros de arredondamento com dinheiro?** `Decimal`/`DecimalField` ou inteiros em centavos; jamais `float`. Calcular totais no banco com `Sum`. *(aula 5.16)*
**159. Como evitar vender mais do que existe em estoque?** Dentro de uma transação, travar as linhas dos produtos com `select_for_update()` (na mesma ordem) e baixar o estoque com `UPDATE … WHERE stock >= n`; mais uma restrição `CHECK (stock >= 0)` no banco como última defesa. *(aula 5.17)*
**160. O que é atomicidade e como o Django a garante?** Um conjunto de operações acontece por inteiro ou não acontece. `transaction.atomic()` abre a transação e faz `ROLLBACK` se uma exceção sair do bloco. *(aula 5.17)*
**161. O que é deadlock e como evitar?** Duas transações esperando uma pela outra por travas em ordem inversa. Travar sempre na mesma ordem, manter transações curtas e tratar o erro de deadlock com nova tentativa. *(aula 5.17)*
**162. Por que guardar o preço no item do pedido?** O preço do produto muda; o pedido é um registro histórico do que foi cobrado. *(aula 5.17)*
**163. O que é um seed idempotente e por que importa?** Rodar várias vezes resulta no mesmo estado, sem duplicar nem falhar; importa para ambientes de dev/CI e reexecução segura. *(aula 5.18)*
**164. Fixtures, seed ou factories?** Fixtures para dados fixos e pequenos; seed (comando) para demonstração com lógica e regras; factories para criar objetos sob medida nos testes. *(aula 5.18)*
**165. O que você confere antes de entregar uma versão?** Testes, `check`/`check --deploy`, migrações em dia, README com passos de execução, sem segredos no repositório e uma tag de versão. *(aula 5.18)*

## Módulo 6 — APIs REST

**166. O que é uma API REST?** Um estilo de arquitetura sobre HTTP: recursos com URIs próprias, manipulados por uma interface uniforme (verbos com semântica fixa), sem estado entre requisições, com possibilidade de cache e camadas; na prática, JSON sobre HTTP com status corretos. *(aula 6.01)*
**167. O que é idempotência e por que importa?** Repetir a mesma requisição N vezes deixa o servidor no mesmo estado que uma vez (`GET`, `PUT`, `DELETE`); permite *retry* seguro após *timeout*. `POST` não é idempotente, então pagamentos/pedidos usam uma chave de idempotência. *(aula 6.01)*
**168. Diferença entre `PUT` e `PATCH`?** `PUT` substitui o recurso inteiro (idempotente); `PATCH` altera só os campos enviados. *(aula 6.01)*
**169. O que significa *stateless* e qual a vantagem?** O servidor não guarda contexto de sessão do cliente; cada requisição é autossuficiente. Qualquer instância atende qualquer chamada, o que facilita escalar horizontalmente. *(aula 6.01)*
**170. Como você nomeia endpoints REST?** Substantivos no plural para coleções (`/products/`), identificador para o item (`/products/12/`), o verbo fica no método HTTP; filtros na query string; ações que não são CRUD como `POST` num sub-recurso (`/orders/7/cancel/`); minúsculas e hífen; prefixo de versão. *(aula 6.02)*
**171. Qual a diferença entre 401, 403 e 404?** 401: não autenticado (falta ou é inválida a credencial); 403: autenticado, mas sem permissão; 404: o recurso não existe (e pode ser usado para não revelar a existência de um recurso alheio). *(aula 6.02)*
**172. Como representar dinheiro e datas em JSON?** Dinheiro como string decimal ou centavos inteiros (nunca `float`); datas em ISO 8601/RFC 3339, em UTC. *(aula 6.02)*
**173. Como você evita quebrar clientes ao evoluir a API?** Versionamento na URL (`/v1/`), mudanças compatíveis sem nova versão, depreciação avisada e documentação/contrato (OpenAPI) como referência. *(aula 6.02)*
**174. O que é um serializer no DRF?** A camada que converte objetos/QuerySets em tipos simples (para JSON) e valida e converte os dados de entrada em `validated_data`, podendo criar/atualizar o objeto (`ModelSerializer`). *(aula 6.03)*
**175. Por que não usar `fields = "__all__"`?** Expõe automaticamente qualquer campo novo do model (inclusive sensíveis) e aceita escrita em campos que não deveria; o contrato da API deve ser explícito. *(aula 6.03)*
**176. Onde ficam as validações e em que ordem?** Validadores do campo/model, depois `validate_<campo>()` e por fim `validate()` para regras entre campos; os erros voltam agrupados por campo. *(aula 6.03)*
**177. Como evitar N+1 numa listagem DRF?** Preparar o QuerySet da view com `select_related` (FK) e `prefetch_related` (muitos), pois o serializer só lê as relações; medir com `CaptureQueriesContext`/`assertNumQueries`. *(aula 6.03)*
**178. Qual a diferença entre `APIView`, `GenericAPIView` e `ViewSet`?** `APIView`: você escreve cada método HTTP; `GenericAPIView`: acrescenta `queryset`/`serializer_class`/`get_object()` e se combina com mixins; `ViewSet`: agrupa as ações (`list`, `retrieve`…) numa classe e delega as URLs ao router. *(aula 6.04)*
**179. Para que serve o router?** Gerar as rotas de um viewset (lista/detalhe e ações extras) a partir de uma convenção, evitando declarar cada `path()` à mão. *(aula 6.04)*
**180. Como você garante que um usuário só veja os próprios pedidos?** No `get_queryset()`, filtrando por `request.user`; assim o pedido alheio dá `404` e a regra vale para lista, detalhe e ações. *(aula 6.04)*
**181. Por que sem login a API devolve 403 e não 401 em alguns casos?** Porque o DRF só envia `401` (com `WWW-Authenticate`) se a primeira classe de autenticação define o cabeçalho; `SessionAuthentication` não define, então vira `403`. *(aula 6.04)*
**182. Como você padroniza erros numa API DRF?** Com um `EXCEPTION_HANDLER` próprio que converte exceções (inclusive as do domínio) para um formato único, mantendo erros de campo por campo e o restante como `detail` + `code`; mais um `handler500` em JSON que não vaza detalhes. *(aula 6.05)*
**183. Qual a diferença entre 400 e 422?** 400: requisição malformada ou campos inválidos; 422: dados válidos no formato, mas rejeitados por regra de negócio. O essencial é a consistência documentada. *(aula 6.05)*
**184. Onde fica a validação: serializer, model ou serviço?** Formato e consistência dos dados no serializer; integridade que não pode falhar nunca nas constraints do banco/model; regras que dependem do estado e têm efeito (estoque) no serviço. Cada camada protege o que conhece. *(aula 6.05)*
**185. O que não pode aparecer numa resposta 500?** *Traceback*, mensagens de exceção cruas, SQL, caminhos de arquivos, versões; isso vai para o log, e o cliente recebe uma mensagem genérica. *(aula 6.05)*
**186. O que é um JWT e como funciona a assinatura?** Um token com três partes em Base64URL (cabeçalho, claims, assinatura); a assinatura é um HMAC (ou assinatura assimétrica) sobre as duas primeiras partes com uma chave secreta, então qualquer alteração invalida o token. É assinado, **não** criptografado. *(aula 6.06)*
**187. Por que usar access e refresh?** O access de vida curta limita o impacto do vazamento; o refresh de vida longa gera novos access. A rotação com lista de bloqueio detecta reuso de refresh roubado. *(aula 6.06)*
**188. Quais os riscos do JWT e como mitigar?** Roubo (use HTTPS, validade curta, evite XSS), dificuldade de revogar (validade curta, blacklist), dados sensíveis nas claims (nunca), algoritmo e chave fracos (fixar o algoritmo, chave longa e secreta). *(aula 6.06)*
**189. Sessão ou token numa API?** Sessão + cookie combina com o mesmo domínio e navegador; token no cabeçalho serve a apps móveis, outros domínios e serviços, e permite escalar sem estado compartilhado. *(aula 6.06)*
**190. Como você protege endpoints numa API DRF?** Autenticação (JWT) mais uma política de permissões “negar por padrão” (`IsAuthenticated` global), abrindo exceções explícitas; permissões por papel via grupos (`DjangoModelPermissions`), escopo por usuário no `get_queryset()` e permissões de objeto para regras como “só o dono”. *(aula 6.07)*
**191. Qual a diferença entre `has_permission` e `has_object_permission`?** O primeiro roda antes da ação para a view toda (lista e criação); o segundo roda quando se obtém um objeto específico via `get_object()`, nunca na lista, então listas dependem do `get_queryset()`. *(aula 6.07)*
**192. O que é IDOR e como evitar?** Acesso a objetos de outros trocando o identificador; evita-se filtrando a consulta pelo dono/escopo e testando com dois usuários. *(aula 6.07)*
**193. 404 ou 403 para recurso alheio?** 404 quando não se deve revelar que o recurso existe (escopo); 403 quando o usuário já pode ver o objeto mas não executar a ação. *(aula 6.07)*
**194. Como implementar filtros numa API DRF?** Com `django-filter`: um `FilterSet` declara os parâmetros e o `DjangoFilterBackend` valida e aplica; busca com `SearchFilter` e ordenação com `OrderingFilter` e `ordering_fields` explícito. *(aula 6.08)*
**195. Qual o risco de ordenar por qualquer campo vindo da URL?** Expor ou inferir dados sensíveis, erros de consulta e abrir caminho para consultas lentas; por isso usa-se uma lista permitida. *(aula 6.08)*
**196. Filtro ou permissão: quando cada um?** Filtro é conveniência do cliente (pode ser trocado por ele); permissão e visibilidade são regras do servidor, aplicadas no `get_queryset()` antes de qualquer filtro. *(aula 6.08)*
**197. Como saber se a busca ficou lenta?** Contar e medir as consultas (`CaptureQueriesContext`, `EXPLAIN`), verificar índices e considerar busca de texto do banco quando `LIKE '%x%'` não escala. *(aula 6.08)*
**198. Por que paginar uma API e qual estratégia usar?** Para limitar custo de banco, memória e rede. Por página/`OFFSET` quando o cliente precisa “ir à página N” e o total; por cursor para listas grandes ou que mudam, pois evita repetição/omissão e `OFFSET` lento. *(aula 6.09)*
**199. O que é throttling e como é implementado no DRF?** Limitar requisições por tempo para proteger contra abuso e bugs; `AnonRateThrottle` (IP), `UserRateThrottle` (usuário) e `ScopedRateThrottle` (por endpoint), com contador no cache; ao exceder, `429` com `Retry-After`. *(aula 6.09)*
**200. Como você protege o login de força bruta?** Throttle específico por IP e, idealmente, por conta, mensagens de erro iguais para usuário inexistente/senha errada, senhas fortes e bloqueios progressivos; limites também na borda (Nginx/WAF). *(aula 6.09)*
**201. O que acontece com o throttle atrás de um balanceador?** O IP visto é o do balanceador; é preciso configurar proxies confiáveis (`NUM_PROXIES`/`X-Forwarded-For`) e um cache compartilhado. *(aula 6.09)*
**202. Como você documenta uma API Django/DRF?** Gero o schema OpenAPI do próprio código com `drf-spectacular`, complemento com `@extend_schema` (resumos, erros, exemplos), exponho Swagger UI/ReDoc e valido na CI para a documentação nunca divergir do comportamento. *(aula 6.10)*
**203. Como evolui uma API sem quebrar clientes?** Versionando (no caminho, por exemplo `/v1/`), mantendo mudanças compatíveis na versão atual, criando uma nova versão para quebras e anunciando a depreciação da antiga; comparo schemas na CI para detectar quebras. *(aula 6.10)*
**204. O que é uma mudança que quebra?** Remover ou renomear campo/rota, mudar tipo ou significado de campo, tornar obrigatório um campo da requisição. *(aula 6.10)*
**205. Qual a diferença entre a versão da API e a versão do schema?** A da API (URL) só muda em quebras; a do schema/`info.version` acompanha cada release, inclusive as compatíveis. *(aula 6.10)*
**206. O que é CORS e quem o impõe?** Mecanismo em que o servidor, por cabeçalhos HTTP, declara quais origens podem ler suas respostas; é o **navegador** quem aplica. Não protege a API de outros clientes. *(aula 6.11)*
**207. O que é o preflight?** Um `OPTIONS` que o navegador envia antes de requisições não simples (JSON, `Authorization`, `PUT/PATCH/DELETE`) para saber se o servidor aceita; sem autorização, o pedido real não é enviado. *(aula 6.11)*
**208. Como configurar CORS no Django com segurança?** `django-cors-headers` com `CORS_ALLOWED_ORIGINS` explícito por ambiente, restrito a `/api/`, sem `ALLOW_ALL` e sem credenciais desnecessárias; ou evitar CORS servindo front e API pelo mesmo domínio. *(aula 6.11)*
**209. CORS substitui CSRF ou autenticação?** Não. CORS regula quem pode **ler** respostas no navegador; CSRF trata de requisições com cookies enviadas pelo navegador; autenticação/autorização protegem os dados. *(aula 6.11)*
**210. Como você testa uma API REST?** Com o cliente de teste do framework (`APIClient`) e pytest: para cada endpoint, caminho feliz, validação, autenticação, permissão e regra de negócio, conferindo status, corpo e efeitos no banco; mais uma jornada de ponta a ponta e um teste de contrato contra o OpenAPI. *(aula 6.12)*
**211. Diferença entre teste unitário e de API?** Unitário isola uma peça (serviço/serializer); de API atravessa roteamento, autenticação, permissões, serialização e banco para provar que as peças estão ligadas. *(aula 6.12)*
**212. Cobertura alta garante qualidade?** Não: só mostra o que foi executado. Complementa-se com asserções fortes, testes de mutação e de contrato. *(aula 6.12)*
**213. Como evitar testes frágeis ou lentos?** Isolamento por transação, dados determinísticos (seed/factories), controle de tempo e cache, testes pequenos e focados, regra de negócio testada sem HTTP e poucos testes de jornada. *(aula 6.12)*
**214. REST, GraphQL ou gRPC?** REST para APIs públicas e CRUD (simples, cacheável, ecossistema); GraphQL quando vários clientes precisam de formatos diferentes e queremos evitar over/under-fetching (pagando em complexidade de servidor); gRPC para comunicação interna entre serviços, com contrato forte, binário e *streaming*. *(aula 6.13)*
**215. Que problemas o GraphQL traz?** N+1 nos resolvers, consultas profundas/caras (limites de profundidade e complexidade), autorização por campo, cache mais difícil e erros com status `200`. *(aula 6.13)*
**216. O que é um `.proto` e por que o gRPC é compacto?** É o contrato (mensagens e serviços) a partir do qual se gera código; a serialização é binária e identifica campos por número, não por nome. *(aula 6.13)*
**217. Como evitar cobrar duas vezes num `POST` repetido?** Chave de idempotência enviada pelo cliente; o servidor guarda `(usuário, chave) → resposta` na mesma transação e devolve o resultado guardado na repetição, sem executar de novo. *(aula 6.13)*
**218. Como o front lida com token expirado?** Ao receber `401` por token inválido, tenta renovar uma única vez com o refresh (compartilhando a renovação entre chamadas simultâneas), repete a chamada e, se o refresh falhar, limpa a sessão e leva o usuário ao login. *(aula 6.14)*
**219. Onde guardar o JWT no navegador?** Cada opção troca riscos: `localStorage`/`sessionStorage` são legíveis por JavaScript (XSS); cookie `HttpOnly` não é, mas exige proteção contra CSRF e mesmo domínio. Em qualquer caso: tokens curtos, HTTPS e **evitar XSS**. *(aula 6.14)*
**220. Por que uma chamada funciona no Postman e falha no navegador?** O navegador aplica CORS e outras políticas; é preciso olhar o preflight (`OPTIONS`) e os cabeçalhos `Access-Control-*`, inclusive os de cabeçalhos personalizados. *(aula 6.14)*
**221. Como evitar XSS ao exibir dados da API?** Inserir como texto (`textContent`, nós de texto), nunca como HTML; sanitizar quando for inevitável aceitar HTML; e reforçar com CSP. *(aula 6.14)*

## Módulo 7 — Comunicação síncrona e assíncrona

**222. Qual a diferença entre I/O-bound e CPU-bound?** I/O-bound passa a maior parte do tempo esperando disco, rede ou banco (tempo de parede ≫ CPU) e se beneficia de concorrência; CPU-bound passa o tempo calculando (CPU ≈ parede) e se beneficia de paralelismo (vários processos/núcleos) ou de algoritmo melhor. *(aula 7.01)*
**223. O que significa uma chamada bloqueante?** A *thread* que a chama fica parada até a operação terminar; enquanto isso ela não faz outra coisa. A alternativa é não bloquear (async) ou delegar a outra *thread*/processo/fila. *(aula 7.01)*
**224. Meu servidor está com CPU baixa e lento, por quê?** Provavelmente os workers estão esperando I/O (banco, APIs externas). A solução é reduzir/concorrer a espera, adiar trabalho para filas, usar cache e ajustar *timeouts*, e não necessariamente mais CPU. *(aula 7.01)*
**225. Concorrência e paralelismo são a mesma coisa?** Não: concorrência é estrutura (lidar com várias tarefas), paralelismo é execução simultânea; dá para ter concorrência sem paralelismo (um núcleo, `asyncio`). *(aula 7.01)*
**226. O que é o GIL e quando ele atrapalha?** Uma trava global do CPython que permite só uma *thread* executar bytecode Python por vez. Não atrapalha carga I/O-bound (o GIL é liberado nas esperas), mas impede que threads acelerem cálculo em Python puro; para isso usam-se processos, bibliotecas em C ou, a partir do 3.13/3.14, a compilação *free-threaded*. *(aula 7.02)*
**227. Threads ou processos?** Threads para esperar (I/O), por serem leves e compartilharem memória; processos para calcular (paralelismo real), pagando custo de criação, memória e serialização. Para trabalho que pode esperar, uma fila com workers. *(aula 7.02)*
**228. O que é uma condição de corrida e como evitá-la?** Resultado dependente da intercalação de threads (ler-modificar-escrever não atômico). Evita-se com travas, filas, evitar estado compartilhado ou, no banco, operações atômicas (`F()`), transações e `select_for_update()`. *(aula 7.02)*
**229. Como o Django lida com threads e conexões?** Cada thread tem sua própria conexão com o banco; threads criadas manualmente devem fechá-la; e há limite de conexões no banco, então threads demais esgotam o servidor. *(aula 7.02)*
**230. O que é `asyncio` e como funciona?** Concorrência **cooperativa** numa única thread: um laço de eventos executa corrotinas e as alterna nos pontos de `await`, enquanto o sistema operacional avisa quando I/O está pronto; ótimo para muitas esperas de rede, inútil para cálculo. *(aula 7.03)*
**231. Qual a diferença entre `await` e `asyncio.gather`?** `await` executa e espera uma operação de cada vez (em sequência, quando seguidos); `gather` agenda várias ao mesmo tempo e espera todas, sobrepondo as esperas. *(aula 7.03)*
**232. O que acontece se eu chamar `time.sleep` ou `requests.get` dentro de `async def`?** Bloqueia o laço inteiro e congela todas as outras requisições/tarefas; usa-se `await asyncio.sleep`, um cliente assíncrono (`httpx`) ou `asyncio.to_thread`. *(aula 7.03)*
**233. Quando usar threads, processos ou `asyncio`?** `asyncio` para muitas esperas de rede com bibliotecas assíncronas; threads para esperar com código bloqueante; processos para cálculo; e filas para o que pode ser adiado. *(aula 7.03)*
**234. Como o Django lida com `async`?** Views assíncronas, ORM com métodos `a...`, e `SynchronousOnlyOperation` ao usar o ORM síncrono; serviços transacionais ficam síncronos e são chamados com `sync_to_async`. *(aula 7.03)*
**235. Por que sempre definir *timeout* em chamadas externas?** Sem ele, um serviço lento ou travado prende o *worker* indefinidamente e derruba a vazão do seu servidor; *timeouts* (conexão e leitura) limitam o dano e permitem falhar rápido. *(aula 7.04)*
**236. Como implementar retentativas de forma segura?** Repetir só erros transitórios (rede, `429`, `502/503/504`) e métodos idempotentes (ou `POST` com chave de idempotência), com limite de tentativas, *backoff* exponencial com *jitter*, respeitando `Retry-After`, e idealmente fora da requisição web, numa fila. *(aula 7.04)*
**237. O que é um *circuit breaker*?** Um mecanismo que, depois de várias falhas seguidas, para de chamar o serviço por um período (falhando rápido), testa com uma chamada e só então volta ao normal; protege o seu sistema e dá folga ao serviço doente. *(aula 7.04)*
**238. `httpx.Client` ou `httpx.get`?** `Client` (ou `AsyncClient`): reaproveita conexões e configurações, reduzindo latência e custo de TLS; funções de módulo só para *scripts* rápidos. *(aula 7.04)*
**239. Como testar código que chama uma API externa?** Sem rede: `MockTransport`/`respx` para simular respostas e falhas, relógio e `sleep` injetados para os testes não esperarem. *(aula 7.04)*
**240. O que é WSGI e o que é ASGI?** Interfaces padrão entre servidores web e aplicações Python: WSGI é síncrono (`app(environ, start_response)`), uma requisição por *worker*; ASGI é assíncrono (`app(scope, receive, send)`), baseado em eventos, e suporta WebSocket, *streaming* e alta concorrência de conexões em espera. *(aula 7.05)*
**241. Qual a função do Gunicorn, do Uvicorn e do Nginx?** Gunicorn: gerenciador de processos/*workers* para WSGI; Uvicorn: servidor ASGI; Nginx: proxy reverso na frente (TLS, estáticos, *buffering*, balanceamento). *(aula 7.05)*
**242. Uma *view* `async` melhora o desempenho no Django?** Só se servida por ASGI e quando há esperas de I/O a sobrepor; sob WSGI não traz concorrência alguma. *(aula 7.05)*
**243. Como dimensionar *workers*?** Pela razão CPU/espera e pela memória: CPU-bound ≈ número de núcleos; muito I/O → mais *threads* ou *workers* assíncronos; sempre medindo e respeitando o limite de conexões do banco. *(aula 7.05)*
**244. O que é *load shedding*?** Recusar rapidamente (503 + `Retry-After`) o excedente quando o servidor está saturado, para manter a latência de quem já está sendo atendido. *(aula 7.05)*
**245. Como você enviaria um e-mail sem travar a requisição?** Enfileirando uma tarefa (Celery + Redis/RabbitMQ) **depois do commit** da transação, passando só o ID; um worker separado carrega os dados e envia, com retentativas e idempotência. *(aula 7.06)*
**246. Por que `transaction.on_commit`?** Para só enfileirar quando o dado já está confirmado no banco: evita que o worker leia um registro inexistente e evita executar a tarefa se a transação sofrer *rollback*. *(aula 7.06)*
**247. O que é entrega *at-least-once* e o que ela exige?** O broker só remove a mensagem após o *ack*; se o worker cair, ela é reentregue; portanto, a tarefa pode rodar mais de uma vez e deve ser idempotente. *(aula 7.06)*
**248. Qual o papel do broker e do result backend?** O broker guarda as mensagens até um worker consumir; o result backend (opcional) guarda os resultados/estados das tarefas; para tarefas com efeito colateral, geralmente não é necessário. *(aula 7.06)*
**249. Celery ou threads dentro da API?** Threads/`asyncio` só adiam dentro do mesmo processo (e morrem com ele, sem retentativa nem visibilidade); fila + worker sobrevive a *deploys*, escala em separado e permite repetir, agendar e monitorar. *(aula 7.06)*
**250. O que é idempotência e por que importa em filas?** Executar a mesma operação várias vezes tem o mesmo efeito que uma; importa porque filas entregam *pelo menos uma vez* e workers/redes falham, então reentregas e retentativas acontecem; sem idempotência, há e-mails e cobranças duplicadas. *(aula 7.07)*
**251. Como tornar uma tarefa idempotente?** Registrar a execução por uma chave estável (`UNIQUE`), “reclamar” o trabalho com uma atualização atômica, usar operações de estado (e não incrementais) e, para terceiros, a chave de idempotência do provedor. *(aula 7.07)*
**252. Como configurar retentativas com o Celery?** `autoretry_for` com erros transitórios, `retry_backoff` + `retry_jitter`, `max_retries`, `acks_late`, e `on_failure` para tratar a desistência; erros permanentes não são repetidos. *(aula 7.07)*
**253. O que é uma *dead letter queue*?** Uma fila para mensagens que **esgotaram as tentativas** ou são inválidas, permitindo inspeção e reprocessamento sem bloquear a fila principal. *(aula 7.07)*
**254. Exatamente uma vez existe?** Não de ponta a ponta; obtém-se o **efeito** exatamente uma vez combinando entrega *at-least-once* com consumidores idempotentes. *(aula 7.07)*
**255. Como agendar tarefas recorrentes em Django?** Com o Celery beat (a agenda enfileira, os workers executam), ou `cron`/systemd/CronJob chamando comandos de gerenciamento; no beat, `crontab` em UTC e **uma única** instância do agendador. *(aula 7.08)*
**256. O que pode dar errado e como se protege?** Execução duplicada (dois beats, reentrega), sobreposição (tarefa mais lenta que o intervalo), execução perdida (beat fora do ar) e fuso/horário de verão; protege-se com tarefas idempotentes e “de nível”, travas, UTC, monitoramento e um beat só. *(aula 7.08)*
**257. Por que preferir um webhook a consultar periodicamente?** Consultar a cada minuto gasta chamadas, atrasa a reação até um minuto e exige agendamento; o webhook avisa **quando acontece** (aula 09). *(aula 7.08)*
**258. Beat ou cron do sistema?** Beat quando já há Celery e a agenda deve viver no código/banco da aplicação; cron/CronJob para poucos jobs simples ou quando cada execução deve rodar isolada. *(aula 7.08)*
**259. O que é um webhook e como difere do polling?** O provedor chama uma URL sua quando algo acontece; no polling você pergunta periodicamente. O webhook é imediato e mais barato, mas exige endpoint público seguro e tolerância a duplicatas/ordem. *(aula 7.09)*
**260. Como proteger um webhook?** Assinatura HMAC sobre o corpo bruto com segredo compartilhado, comparação em tempo constante, timestamp com tolerância contra *replay*, HTTPS, limite de tamanho, erro genérico e, como camada extra, allowlist de IP; e validar o conteúdo contra o seu banco. *(aula 7.09)*
**261. Como tratar webhooks duplicados e fora de ordem?** Guardar o `event_id` único (idempotência), aplicar transições de estado que só avançam, e responder `2xx` para o que já foi tratado; opcionalmente reconciliar consultando o provedor. *(aula 7.09)*
**262. Por que responder rápido ao webhook?** Provedores têm *timeout* curto e repetem se não houver 2xx; faz-se o mínimo (verificar, registrar, mudar o estado) e o resto vai para uma fila. *(aula 7.09)*
**263. O que fazer se o webhook nunca chega?** Uma rotina agendada de reconciliação que consulta pagamentos pendentes antigos na API do provedor. *(aula 7.09)*
**264. Qual a diferença entre uma fila de tarefas e um broker de mensagens?** A fila de tarefas executa funções em segundo plano (um worker por tarefa); o broker entrega mensagens a consumidores, com roteamento e *pub/sub*, desacoplando produtores e consumidores; ambos garantem entrega *pelo menos uma vez* e exigem idempotência. *(aula 7.10)*
**265. Como garantir que o evento “pedido pago” não se perde?** Com o padrão **outbox transacional**: o evento é gravado na mesma transação que muda o estado e um relé o publica depois (at-least-once); os consumidores deduplicam pelo `message_id`. *(aula 7.10)*
**266. RabbitMQ ou SQS?** RabbitMQ: roteamento rico (exchanges), baixa latência, você opera o broker; SQS: totalmente gerenciado, simples, escala sozinho, ótimo na AWS, com Standard (at-least-once) e FIFO (ordem por grupo); Kafka quando o log retido e o reprocessamento são essenciais. *(aula 7.10)*
**267. O que é uma dead letter queue?** Fila para onde vão mensagens rejeitadas, expiradas ou que esgotaram as tentativas, para análise e reprocessamento sem bloquear a fila principal. *(aula 7.10)*
**268. Como funciona um WebSocket e como protegê-lo?** Um `GET` com `Upgrade` abre uma conexão bidirecional persistente; protege-se com `wss://`, autenticação na conexão (token), autorização por recurso, validação de origem, limites de conexões/mensagens e reconexão com *backoff* no cliente; em vários processos, uma *channel layer* compartilhada (Redis). *(aula 7.10)*
**269. WebSocket, SSE ou polling?** WebSocket para bidirecional e baixa latência; SSE para fluxo só do servidor com reconexão automática; *polling* quando a frequência é baixa e a simplicidade importa. *(aula 7.10)*

## Módulo 8 — Estrutura de projetos e arquitetura

**270. Como você organiza um projeto Django além de `views.py` e `models.py`?** Em camadas: interface fina (views/serializers/consumers), serviços com os casos de uso e as regras (transações, orquestração), modelos/consultas para os dados e adaptadores para a infraestrutura (e-mail, gateway); com a regra de que as dependências só descem, verificada por contratos de importação na CI. *(aula 8.01)*

**271. O que é uma *fat view* e por que é ruim?** Uma *view* que contém regra de negócio, acesso a dados e integrações; é difícil de testar, não é reaproveitável (a regra aparece na API, na tela e na tarefa) e qualquer mudança de regra mexe na camada HTTP. *(aula 8.01)*

**272. O que é dependência circular e como resolver?** Dois módulos/apps que dependem um do outro; resolve-se movendo o código compartilhado para um módulo “de baixo”, invertendo a dependência (interface/evento) ou reposicionando a funcionalidade no app certo. *(aula 8.01)*

**273. Para que serve a complexidade ciclomática?** Indica quantos caminhos independentes há numa função, ou seja, quantos testes ela pede no mínimo; valores altos sinalizam funções a dividir. *(aula 8.01)*

**274. Camadas sempre valem a pena?** Não: num projeto pequeno e de uma só entrada, é cerimônia; elas compensam quando há várias entradas, regras que mudam e necessidade de testes rápidos. *(aula 8.01)*

**275. Qual a diferença entre *service* e *repository*?** O serviço implementa um caso de uso (a sequência de regras e a transação); o repositório abstrai o armazenamento atrás de uma interface, para que o serviço não dependa do ORM/SQL e possa ser testado com um *fake*. *(aula 8.02)*

**276. Vale a pena um repositório em cima do ORM do Django?** Depende: em CRUD simples não (o ORM já é um repositório; seria cerimônia); em casos com regras ricas, necessidade de testes rápidos sem banco ou possibilidade de trocar a persistência, sim. *(aula 8.02)*

**277. Como você testa regras de negócio sem banco?** Isolando-as em funções/objetos puros e, para o caso de uso inteiro, injetando um repositório em memória; os adaptadores reais ficam cobertos por testes de integração. *(aula 8.02)*

**278. Como refatorar sem quebrar nada?** Com testes que cobrem o comportamento atual, passos pequenos com a suíte verde, e verificando contratos externos (OpenAPI, esquemas) e métricas (complexidade, imports) antes e depois. *(aula 8.02)*

**279. O que é injeção de dependência e precisa de framework em Python?** Passar as dependências de fora (parâmetros/construtor) em vez de criá-las dentro; em Python basta um argumento com valor padrão. *(aula 8.02)*

**280. Explique o SOLID com um exemplo seu.** SRP: dividi um caso de uso em domínio, serviço e repositório; OCP: formas de pagamento como estratégias registradas, sem editar o `if/elif`; LSP: um teste de contrato garante que o repositório em memória e o do banco cumprem as mesmas promessas; ISP: um `Protocol` mínimo para o relatório; DIP: o serviço recebe o repositório por parâmetro e depende da porta, não do ORM. *(aula 8.03)*

**281. O que é o princípio de Liskov, na prática?** Um subtipo deve poder ocupar o lugar do tipo base sem quebrar as promessas (pré-condições, pós-condições, invariantes); testa-se com testes de contrato rodando contra todas as implementações. *(aula 8.03)*

**282. DRY significa nunca repetir código?** Não: significa não repetir **conhecimento** (a mesma regra em dois lugares). Trechos parecidos que mudam por razões diferentes não devem ser unificados à força, para não criar a abstração errada. *(aula 8.03)*

**283. O que é YAGNI e como conciliar com “design para extensão”?** Não construir hoje o que ninguém pediu; conciliar mantendo o código **simples e bem testado**, para que a extensão futura seja um refactor pequeno e seguro quando a necessidade aparecer. *(aula 8.03)*

**284. O que é `typing.Protocol`?** Uma interface estrutural: qualquer classe com os métodos exigidos satisfaz o tipo, sem herança; os verificadores (mypy) conferem em tempo de análise. *(aula 8.03)*

**285. Dê um exemplo de Adapter.** O adaptador de gateway de pagamento: define uma interface do MiniShop (`criar_cobranca`, `interpretar_webhook`) e, para cada provedor, uma classe que traduz requisições, estados, valores e assinaturas, para o núcleo não depender de nenhum provedor. *(aula 8.04)*

**286. Qual a diferença entre Strategy e Factory?** Strategy encapsula **variantes de um comportamento** intercambiáveis; Factory decide **qual** objeto criar. Costumam andar juntos: a fábrica escolhe a estratégia. *(aula 8.04)*

**287. Repository ou ORM direto?** Repository quando há regras ricas, necessidade de testes sem banco ou troca de persistência; ORM direto em CRUD simples. *(aula 8.04)*

**288. Como você troca de provedor de pagamento sem reescrever o sistema?** Com uma porta e adaptadores: escreve-se um novo adaptador, ajusta-se a configuração da fábrica e roda-se o teste de contrato. *(aula 8.04)*

**289. Padrões de projeto sempre valem a pena?** Não: cada padrão custa abstração; só se justifica quando o problema (variantes, acoplamento a terceiros, testes lentos) existe. *(aula 8.04)*

**290. Monolito ou microsserviços?** Começo por monolito modular; microsserviços quando há times independentes, escala desigual ou ciclos de deploy conflitantes, medidos, porque trocam transação por consistência eventual e somam custo operacional. *(aula 8.05)*

**291. Qual o principal custo de microsserviços?** Complexidade distribuída: rede que falha, observabilidade, versões, transações e deploy. *(aula 8.05)*

**292. Como impedir que um monolito vire bagunça?** Fronteiras impostas por ferramenta (import-linter), camadas e revisão de ADRs. *(aula 8.05)*

**293. O que é um monolito distribuído?** Serviços separados que precisam ser implantados juntos ou compartilham banco: o pior dos dois mundos. *(aula 8.05)*

**294. O que são os doze fatores?** Um conjunto de práticas para apps que rodam em nuvem: uma base de código, dependências declaradas, configuração no ambiente, serviços como recursos anexados, processos sem estado, logs em stdout, paridade dev/produção, entre outras. *(aula 8.06)*

**295. Onde ficam os segredos?** No ambiente (ou num cofre de segredos), nunca no repositório; a aplicação falha ao subir se faltarem. *(aula 8.06)*

**296. Como encerrar um serviço sem perder requisições?** Tratar `SIGTERM`: parar de aceitar novas conexões, terminar as em andamento (`graceful-timeout`) e só então sair; o orquestrador espera mais que esse prazo antes do `SIGKILL`. *(aula 8.06)*

**297. Por que testar no mesmo banco da produção?** Porque diferenças de travas, sequências, tipos e SQL só aparecem nele (por exemplo, `select_for_update` é ignorado no SQLite). *(aula 8.06)*

**298. Para onde vão os logs numa app em contêiner?** Para stdout/stderr, como fluxo; a plataforma agrega e roteia. *(aula 8.06)*

**299. Como você mexe num código sem testes?** Primeiro crio testes de caracterização (golden master) cobrindo os caminhos, meço a rede com cobertura de ramos e mutação, e refaço em passos pequenos, rodando a rede a cada passo. *(aula 8.07)*

**300. Qual a diferença entre refatorar e corrigir um bug?** Refatorar muda a estrutura sem mudar o comportamento; corrigir muda o comportamento. Faço em commits separados. *(aula 8.07)*

**301. Reescrever do zero ou refatorar?** Quase sempre refatorar e estrangular aos poucos (*Strangler Fig*): reescrever perde regras escondidas e adia o valor. *(aula 8.07)*

**302. O que é injeção de SQL e como evitar?** Entrada do usuário interpretada como SQL; evita-se com consultas parametrizadas (`execute(sql, [params])`) ou o ORM. *(aula 8.07)*

**303. Como você sabe que a refatoração melhorou algo?** Métricas (complexidade ciclomática, linhas, manutenibilidade), a rede continuando verde, e a facilidade de mudar (cupom novo = uma linha). *(aula 8.07)*

## Módulo 9 — Segurança

**304. Cite itens do OWASP Top 10 e como evitá-los.** Controle de acesso quebrado (autorizar no servidor, por objeto), injeção (consultas parametrizadas e escape de saída), falhas de autenticação (hash lento, limite de tentativas, MFA), configuração insegura (cabeçalhos, `DEBUG` desligado, sem rotas de demonstração), dependências vulneráveis (`pip-audit`, lockfile). *(aula 9.01)*

**305. O que é modelagem de ameaças?** Desenhar o sistema (fluxos e fronteiras de confiança), listar o que pode dar errado (STRIDE), decidir mitigações e verificar; faz-se no projeto, não no fim. *(aula 9.01)*

**306. Como priorizar vulnerabilidades?** Por risco: probabilidade × impacto, considerando facilidade de exploração e quantos usuários atinge. *(aula 9.01)*

**307. O que é defesa em profundidade?** Várias camadas independentes, de modo que a falha de uma não comprometa tudo. *(aula 9.01)*

**308. O que fazer ao achar uma vulnerabilidade em produção?** Conter (mitigar), corrigir com teste, avaliar se dados foram expostos (e se há obrigação de comunicar, LGPD) e registrar o aprendizado. *(aula 9.01)*

**309. Como se previne SQL injection?** Consultas parametrizadas (ou ORM), nunca concatenar dado do usuário no SQL; *allowlist* para nomes de coluna/tabela; menor privilégio na conta do banco; validação de entrada como camada extra. *(aula 9.02)*

**310. O ORM do Django protege contra SQL injection?** Sim, ele parametriza; o risco volta com `raw()`, `extra()`, `RawSQL` e `cursor.execute` montados por texto. *(aula 9.02)*

**311. Qual a diferença entre XSS armazenado, refletido e baseado em DOM?** Armazenado: persiste e atinge quem vê; refletido: vem na requisição e volta na resposta; DOM: o JavaScript do cliente insere o dado como HTML. *(aula 9.02)*

**312. Como evitar XSS?** Escape de saída conforme o contexto (o Django faz *autoescape* de HTML), evitar `|safe`/`mark_safe`/`innerHTML` com dado de usuário, CSP e cookies `HttpOnly` como camadas extras. *(aula 9.02)*

**313. O que é defesa em profundidade?** Várias camadas independentes (validação, escape, CSP, privilégios mínimos), de modo que uma falha não seja fatal. *(aula 9.02)*

**314. O que é CSRF e como se previne?** Uma ação indesejada disparada por outro site aproveitando que o navegador anexa o cookie sozinho; previne-se com token CSRF, `SameSite`, conferência de origem e usando o cabeçalho `Authorization` em vez de cookie. *(aula 9.03)*

**315. O CORS protege contra CSRF?** Não. O CORS controla quem pode *ler* respostas entre origens no navegador; o `POST` simples sai e é executado do mesmo jeito. *(aula 9.03)*

**316. Sessão ou JWT?** Sessão: revogação imediata e cookie `HttpOnly`, mas estado no servidor e CSRF; JWT: sem estado e bom para vários clientes, mas revogar é difícil, então usa-se *access* curto e *refresh* com rotação. *(aula 9.03)*

**317. Onde guardar o JWT no navegador?** Não há opção sem risco: `localStorage` é legível por XSS; memória some ao recarregar; cookie `HttpOnly` volta o CSRF. Reduza o XSS e escolha conscientemente. *(aula 9.03)*

**318. O que significam `Secure`, `HttpOnly` e `SameSite`?** Só HTTPS; inacessível ao JavaScript; limita o envio em requisições entre sites. *(aula 9.03)*

**319. Como guardar senhas?** Como hash lento com salt aleatório por usuário (Argon2id, scrypt, bcrypt ou PBKDF2 com muitas iterações), nunca em texto puro nem com hash rápido; comparar em tempo constante e permitir subir o custo ao longo do tempo. *(aula 9.04)*

**320. Para que serve o salt?** Para que a mesma senha gere hashes diferentes e para inutilizar tabelas pré-calculadas; ele não torna o hash mais lento. *(aula 9.04)*

**321. Argon2 ou bcrypt?** Argon2id é a recomendação atual (custo em memória e tempo, resistente a GPU); bcrypt segue aceitável e muito difundido; PBKDF2 quando se exige conformidade com normas. *(aula 9.04)*

**322. Qual a diferença entre autenticação e autorização?** Autenticação confirma quem você é; autorização decide o que você pode fazer. *(aula 9.04)*

**323. O que é enumeração de usuários e como evitar?** Descobrir quais contas existem por diferenças de mensagem ou de tempo; evita-se com respostas idênticas, mesmo trabalho nos dois caminhos e limitação de tentativas. *(aula 9.04)*

**324. Bloquear a conta após N tentativas é boa ideia?** Com ressalvas: pode permitir negação de serviço contra a vítima; prefira limite de taxa, atrasos progressivos e MFA. *(aula 9.04)*

**325. O que é IDOR?** Quando o servidor entrega ou altera um objeto identificado pelo cliente sem verificar que ele pertence a quem pediu; também chamado BOLA em APIs. Corrige-se restringindo a consulta ao dono e testando com um segundo usuário. *(aula 9.05)*

**326. `401`, `403` ou `404`?** `401` não autenticado, `403` autenticado sem permissão (recurso existe), `404` quando não devemos confirmar que o recurso existe, como o objeto de outro usuário. *(aula 9.05)*

**327. Como testar autorização?** Matriz papel × ação × dono com atores adversários, e validação por mutação (remover a proteção e ver o teste falhar). *(aula 9.05)*

**328. O que é *mass assignment*?** O cliente grava campos que só o servidor devia controlar (`is_staff`, `total`); evita-se com serializadores que listam explicitamente os campos graváveis. *(aula 9.05)*

**329. O que é menor privilégio?** Cada papel recebe só o que precisa; o gerente de catálogo não precisa ler pedidos de clientes. *(aula 9.05)*

**330. UUID no lugar de ID sequencial resolve IDOR?** Não. Dificulta adivinhar, mas quem obtiver o UUID (log, e-mail, histórico) continua podendo usá-lo; a autorização por objeto é obrigatória. *(aula 9.05)*

**331. O que fazer quando um segredo vaza no Git?** Revogar e rotacionar imediatamente, verificar o uso indevido nos logs do provedor, e só depois (se necessário) limpar o histórico; apagar o arquivo não basta. *(aula 9.06)*

**332. Como você gerencia vulnerabilidades em dependências?** Versões travadas, auditoria automatizada (`pip-audit`/Dependabot) no CI e periódica, atualizações pequenas e frequentes, e menos dependências. *(aula 9.06)*

**333. O que é CSP?** Uma política enviada pelo servidor que limita de onde scripts, estilos e outros recursos podem ser carregados; é uma camada extra contra XSS. *(aula 9.06)*

**334. O que é HSTS e qual o cuidado?** Instrui o navegador a usar só HTTPS por um tempo; é difícil de desfazer, então se começa com valores baixos. *(aula 9.06)*

**335. Por que o limite de taxa pode falhar com vários workers?** Porque o contador fica no cache; o cache local é por processo, então o limite real é multiplicado. Usa-se um cache compartilhado (Redis). *(aula 9.06)*

**336. O que registrar em logs de segurança?** Eventos (login falho, acesso negado, limites), com quem, de onde e quando; nunca senhas ou tokens, e sanitizando o que vem do usuário. *(aula 9.06)*

**337. O que é HTTPS e o que ele garante?** HTTP sobre TLS: confidencialidade, integridade e autenticidade do servidor (via certificado de uma CA confiável); não protege contra falhas na aplicação. *(aula 9.07)*

**338. Onde termina o TLS e por que isso importa?** Em geral no proxy/balanceador; o Django precisa confiar no `X-Forwarded-Proto` só se o proxy o sobrescrever e a aplicação não estiver exposta diretamente. *(aula 9.07)*

**339. O que é o princípio do menor privilégio? Exemplo.** Dar só o acesso necessário; no banco, a aplicação usa um papel que lê e grava dados mas não altera nem apaga tabelas, e as migrações rodam com outro papel. *(aula 9.07)*

**340. O que é dado pessoal na LGPD?** Informação relacionada a pessoa natural identificada ou identificável (nome, e-mail, IP em alguns contextos); o sensível (saúde, religião etc.) tem proteção reforçada. *(aula 9.07)*

**341. Cite direitos do titular.** Confirmação de tratamento, acesso, correção, anonimização/bloqueio/eliminação de dados desnecessários, portabilidade, informação sobre compartilhamento e revogação do consentimento. *(aula 9.07)*

**342. Todo tratamento de dados precisa de consentimento?** Não; há outras bases legais (contrato, obrigação legal, legítimo interesse etc.), e o consentimento nem sempre é a mais adequada. *(aula 9.07)*

**343. Como você trataria um vazamento de dados?** Conter, avaliar o que e quem foi afetado, corrigir a causa, e comunicar a ANPD e os titulares conforme a lei, com apoio do jurídico e do encarregado. *(aula 9.07)*

## Módulo 10 — Qualidade, testes e boas práticas

**344. O que é a pirâmide de testes?** Muitos testes de unidade (rápidos, baratos, diagnosticam bem), alguns de integração e poucos de ponta a ponta (lentos e frágeis); otimiza velocidade e clareza do diagnóstico. *(aula 10.01)*

**345. Qual a diferença entre teste de unidade e de integração?** Unidade isola uma peça (sem banco/rede); integração exercita peças reais juntas, como serviço e banco. *(aula 10.01)*

**346. O que é uma fixture no pytest?** Uma função que prepara (e limpa) o que o teste precisa, pedida pelo nome como parâmetro; tem escopo (`function`, `module`, `session`) e pode usar `yield` para limpeza. *(aula 10.01)*

**347. Como acelerar uma suíte lenta?** Medir primeiro (`--durations`, perfil), atacar os custos de preparação, usar fábricas e dados mínimos, paralelizar, e mover regra para código puro; sem enfraquecer o que os testes verificam. *(aula 10.01)*

**348. O que é um teste flaky e como evitar?** Um que falha de forma intermitente por dependência de ordem, tempo, rede ou aleatoriedade; evita-se com isolamento, injeção de relógio/semente, *fakes* e rodando em ordem aleatória. *(aula 10.01)*

**349. O que significa AAA?** Arrange, Act, Assert: preparar, agir, verificar. *(aula 10.01)*

**350. Para que serve `parametrize`?** Executar a mesma lógica de teste com vários conjuntos de entrada e saída, gerando um teste independente por caso, com ids legíveis. *(aula 10.02)*

**351. Mock, stub e fake: qual a diferença?** Stub devolve respostas prontas; mock registra e verifica interações; fake é uma implementação funcional simplificada (como um repositório em memória). Prefiro fakes e testes de estado para o que é meu, e mocks para bordas externas. *(aula 10.02)*

**352. Por que `autospec`?** Porque um `Mock` solto aceita qualquer coisa e esconde erros de digitação e de assinatura; `autospec` exige que o uso bata com o objeto real. *(aula 10.02)*

**353. Onde se faz o `patch`?** Onde o nome é **usado**, não onde é definido. *(aula 10.02)*

**354. Como testar código que depende do horário?** Controlando o relógio (trocando `timezone.now` ou usando `freezegun`/`time-machine`), idealmente injetando o relógio; nunca com `sleep`. *(aula 10.02)*

**355. O que é um teste frágil?** Um que quebra quando a implementação muda sem que o comportamento mude; costuma vir de mocks que verificam a sequência interna de chamadas. *(aula 10.02)*

**356. O que é cobertura de testes e qual a meta?** A fração do código executada pelos testes (linhas e ramos); a meta depende do risco, mas costuma-se exigir algo como 80% nas regras de negócio; cobertura alta é necessária, não suficiente. *(aula 10.03)*

**357. Cobertura de linhas × ramos?** Linhas conta o que executou; ramos exige exercitar cada decisão nos dois sentidos. *(aula 10.03)*

**358. Cobertura alta garante qualidade?** Não: um teste sem asserções pode cobrir tudo e não detectar nada; por isso se usa mutação e revisão dos testes. *(aula 10.03)*

**359. O que você testa numa rota de API?** Caminho feliz, autenticação e permissão, validação, erros de negócio, efeitos no banco, idempotência e, em listas, paginação e número de consultas. *(aula 10.03)*

**360. Como testar código que depende de infraestrutura (fila, broker)?** Isolando a lógica e usando um cliente/canal falso em memória nos testes rápidos, mais um teste de ambiente com o serviço real. *(aula 10.03)*

**361. O que é um teste de mutação?** Alterar o código de propósito (um operador, uma constante) e verificar se algum teste falha; se não falha, falta uma asserção. *(aula 10.03)*

**362. O que é TDD?** Desenvolver em ciclos curtos: escrever um teste que falha, escrever o mínimo de código para passar e refatorar com a rede de testes verde. *(aula 10.04)*

**363. Quais os benefícios?** Código mais simples e testável, menos funcionalidades desnecessárias, rede de segurança para refatorar e especificação executável. *(aula 10.04)*

**364. Você pratica TDD sempre?** Uso mais em regras de negócio e correção de bugs; em protótipos faço um *spike* e escrevo os testes depois; o importante é o feedback rápido e os passos pequenos. *(aula 10.04)*

**365. Como corrigir um bug com TDD?** Escrever primeiro o teste que o reproduz (vermelho), corrigir (verde), refatorar, e deixar o teste como proteção contra a volta. *(aula 10.04)*

**366. O que é triangulação?** Usar um segundo exemplo com valores diferentes para forçar a implementação real em vez de uma resposta fixa. *(aula 10.04)*

**367. TDD substitui testes depois?** Não: complementa; testes de integração e de ponta a ponta continuam necessários (pirâmide). *(aula 10.04)*

**368. Para que servem `ruff`, `mypy` e `pre-commit`?** `ruff` formata e aponta problemas de código; `mypy` confere tipos estaticamente; `pre-commit` roda essas verificações antes de cada commit para barrar erros cedo. *(aula 10.05)*

**369. Como introduzir um formatador num projeto existente?** Num commit separado só de formatação, comprovando que o comportamento não mudou, e registrando esse commit no `.git-blame-ignore-revs`. *(aula 10.05)*

**370. Tipos em Python mudam a execução?** Não; as anotações são verificadas por ferramentas como o `mypy` e servem de documentação e de rede de proteção. *(aula 10.05)*

**371. Como adotar tipos em um código legado?** Gradualmente: `check_untyped_defs` no geral, rigor módulo a módulo começando pelo núcleo de regras de negócio, e stubs para as bibliotecas. *(aula 10.05)*

**372. Por que ter CI se já tem `pre-commit`?** Porque o hook local é opcional (pode ser pulado ou não instalado); o CI garante que nada entra sem passar. *(aula 10.05)*

**373. Por que `Decimal` e não `float` para dinheiro?** Porque `float` é binário e aproximado; o `mypy` ajuda a impedir a mistura acidental. *(aula 10.05)*

**374. O que é Conventional Commits e para que serve?** Um padrão de mensagens (`tipo(escopo): descrição`) que torna o histórico legível e permite gerar versão e changelog automaticamente. *(aula 10.06)*

**375. Como você faz code review?** Leio a descrição, depois os testes, depois o código; confiro correção, segurança, testes, design e desempenho; classifico os comentários (bloqueante, sugestão, dúvida, nit), explico o porquê e, quando posso, escrevo um teste que prova o problema. *(aula 10.06)*

**376. O que a automação pega e o que não pega?** Ela pega estilo, tipos, padrões inseguros conhecidos e cobertura; não pega regra de negócio errada nem falhas de autorização e design. *(aula 10.06)*

**377. Como receber uma revisão difícil?** Separo o código de mim, pergunto o que não entendi, respondo a cada comentário (corrigi, discordo com argumento, ou abri uma issue) e agradeço. *(aula 10.06)*

**378. O que tem num bom README?** O que é, como rodar em poucos minutos, como testar, como contribuir e onde há mais detalhes; com comandos que funcionam. *(aula 10.06)*

**379. Por que PRs pequenos?** Revisão melhor, menos conflitos, entrega contínua e reversão simples. *(aula 10.06)*

**380. O que é metodologia ágil?** Uma abordagem de entregar valor em ciclos curtos com feedback frequente, priorizando pessoas, software funcionando, colaboração e adaptação; o Scrum e o Kanban são formas de aplicá-la. *(aula 10.07)*

**381. Diferença entre Scrum e Kanban?** Scrum usa Sprints (ciclos fixos de até um mês), papéis e eventos definidos; Kanban visualiza o fluxo e limita o trabalho em andamento, sem iterações obrigatórias. *(aula 10.07)*

**382. O que é Definição de Pronto?** O acordo do time sobre o que "terminado" significa (testes, revisão, documentação, segurança…), parte dela automatizada. *(aula 10.07)*

**383. Como você pede ajuda?** Depois de tentar por um tempo, com objetivo, o que tentei, o erro completo e minha hipótese, para a pessoa responder sem precisar perguntar de volta. *(aula 10.07)*

**384. Conte uma situação em que recebeu feedback duro.** (Use um exemplo real: o que foi dito, como reagiu, o que mudou depois.) *(aula 10.07)*

**385. Como você usa IA no trabalho?** Para rascunhos, testes, explicações e alternativas; sempre com critérios e testes definidos antes, revisando o resultado como qualquer PR, verificando APIs e dependências, sem compartilhar segredos nem dados pessoais, e assumindo a responsabilidade pelo que commito. *(aula 10.07)*

**386. Quais os riscos do código gerado por IA?** Erros plausíveis, alucinação (inclusive de pacotes), padrões inseguros, desatualização, falta de contexto de negócio, vazamento de dados no prompt e dependência excessiva. *(aula 10.07)*

## Módulo 11 — Docker e containers

**387. Qual a diferença entre um container e uma máquina virtual?** A VM emula um computador e roda o próprio sistema operacional sobre um hipervisor (pesada, isolamento forte). O container é um processo do host com visão restrita (namespaces) e limites (cgroups), compartilhando o kernel: leve, inicia em milissegundos, isolamento mais fraco. *(aula 11.01)*

**388. Qual a diferença entre imagem e container?** A imagem é o pacote imutável, em camadas; o container é uma instância em execução dela, com uma camada gravável descartável. De uma imagem saem vários containers. *(aula 11.01)*

**389. O que acontece com os dados de um container quando ele é removido?** O que foi escrito na camada gravável se perde; dados persistentes ficam em volumes (de preferência nomeados) ou em serviços externos. *(aulas 11.01 e 11.04)*

**390. Como você deixa um build Docker rápido?** Ordenando do que muda menos para o que muda mais (copiar `pyproject.toml`/`uv.lock` e instalar antes do código), usando cache de camadas e de pacotes, imagem `slim`, multi-stage e `.dockerignore`. *(aulas 11.02 e 11.05)*

**391. Por que não rodar o container como root?** Uma falha na aplicação daria ao invasor root dentro do container, que compartilha o kernel com o host; um usuário sem privilégios (UID fixo) reduz o estrago. *(aula 11.02)*

**392. O que é multi-stage build?** Dockerfile com várias etapas em que a imagem final copia só o necessário das anteriores, deixando de fora compiladores e caches: imagem menor e com menos superfície de ataque. *(aula 11.02)*

**393. Por que `CMD ["gunicorn", …]` e não `CMD gunicorn …`?** A forma exec faz o Gunicorn ser o PID 1 e receber o `SIGTERM` do `docker stop` (parada suave); a forma shell deixa o `sh` como PID 1, que não repassa o sinal, e o Docker mata à força após 10 s (código 137). *(aula 11.02)*

**394. O que é Docker Compose e quando usar?** Ferramenta para definir e rodar aplicações multi-container em um YAML. Ótima para desenvolvimento, testes e CI e para pequenos deploys; em larga escala usa-se um orquestrador. *(aula 11.03)*

**395. Como o container da aplicação acha o banco?** Pelo nome do serviço, por DNS da rede do Compose (`db:5432`); `localhost` dentro de um container é ele mesmo. *(aula 11.03)*

**396. `depends_on` garante que o banco está pronto?** Não, só a ordem de início. Usa-se `healthcheck` no banco e `condition: service_healthy`; para tarefas únicas (migração), `service_completed_successfully`. *(aula 11.03)*

**397. Como persistir dados e como passar segredos para um container?** Dados em volumes nomeados (com backup); configuração por variáveis de ambiente; segredos de verdade por arquivos (`secrets`, `*_FILE`) ou gerenciador, pois variáveis aparecem em `docker inspect` e `ARG`/`ENV` ficam em `docker history`. *(aula 11.04)*

**398. Por que um container não consegue escrever num volume?** Permissões são por UID/GID: se a pasta é do root e o processo roda como usuário comum, falha. Cria-se a pasta na imagem com o dono certo (o volume novo herda) ou ajusta-se o dono; em desenvolvimento, `user:` com o UID do host. *(aula 11.04)*

**399. Dois projetos de Compose podem compartilhar dados sem querer?** Sim: volumes são nomeados `projeto_volume`; nomes iguais reaproveitam o mesmo volume sem aviso, e dois servidores de banco sobre o mesmo diretório podem corromper os dados. Use `name:` único e confira `docker volume ls`. *(aula 11.04)*

**400. Um container sobe e cai logo. Como você investiga?** Estado e código de saída (`ps -a`, `inspect`), logs do container que morreu, variáveis e rede, e reprodução com `docker run --rm -it --entrypoint sh`. 137 com `OOMKilled=true` aponta memória; 1 com traceback aponta erro do programa. *(aula 11.05)*

**401. Para que serve o `.dockerignore`?** Para não enviar ao build `.git`, `.env`, `.venv` e caches: build mais rápido, cache preservado e nenhum segredo dentro da imagem. *(aula 11.05)*

**402. O que é um healthcheck e por que "Up" não basta?** É um comando executado periodicamente para saber se o serviço funciona, não só se o processo existe; um processo pode estar vivo e incapaz de atender (sem banco ou broker). *(aulas 11.03 e 11.05)*

**403. Por que Gunicorn/Uvicorn e Nginx em vez do `runserver`?** O `runserver` é só para desenvolvimento. O servidor de aplicação gerencia workers e reinicia os que travam; o Nginx termina o TLS, serve estáticos, limita corpo e *timeouts* e isola a aplicação. *(aula 11.06)*

**404. Qual a diferença entre WSGI e ASGI?** WSGI: interface síncrona (um pedido por vez por worker/thread); ASGI: suporta código assíncrono e conexões longas como WebSocket. Gunicorn é WSGI; Uvicorn e Daphne são ASGI. *(aula 11.06)*

**405. Seu Django atrás de um proxy redireciona em laço ou mostra o IP errado. Por quê?** O Django só vê o proxy; este precisa enviar `X-Forwarded-Proto` e `X-Forwarded-For`, e o Django precisa confiar neles (`SECURE_PROXY_SSL_HEADER`, `NUM_PROXIES`), apenas porque só o proxy o alcança. *(aula 11.06)*

**406. Qual a diferença entre 502 e 504 do Nginx?** 502: o upstream respondeu mal ou recusou a conexão; 504: o upstream não respondeu a tempo. Ambos vêm do proxy, não da aplicação. *(aula 11.06)*


## Módulo 12 — CI/CD

**407. O que é CI/CD?** CI é integrar o código com frequência e validar cada integração com um build automatizado (lint, testes). CD é manter o software sempre pronto para publicar (entrega) ou publicá-lo automaticamente (implantação). *(aula 12.01)*

**408. Diferença entre entrega contínua e implantação contínua?** Na entrega o artefato está sempre pronto e uma pessoa aprova a publicação; na implantação tudo o que passa nos testes vai para produção sozinho. *(aula 12.01)*

**409. Como funciona um workflow do GitHub Actions?** Um YAML em `.github/workflows/` define eventos e jobs com steps; cada job roda em um runner limpo, em paralelo por padrão (ordem com `needs`). O resultado aparece no commit e no PR. *(aula 12.01)*

**410. Como proteger um pipeline?** `permissions` mínimas, actions fixadas por SHA, segredos por ambiente, nenhum segredo em PR de fork (evitar `pull_request_target`), dados externos passados por `env:` e não direto em `run:`, revisão de mudanças em `.github/workflows/`. *(aula 12.01)*

**411. Como validar um workflow sem enviá-lo?** Com o actionlint (sintaxe, expressões, shellcheck) e reproduzindo os comandos de cada job num clone limpo, em container. *(aula 12.01)*

**412. Por que testar em PostgreSQL se o desenvolvimento usa SQLite?** Porque produção usa PostgreSQL e as diferenças (tipos, bloqueios, SQL específico) só aparecem lá; uma matriz com service container vigia a paridade. *(aula 12.02)*

**413. Como é o pipeline do seu projeto?** Lint, tipos, migrações, auditoria de dependências, testes em SQLite e PostgreSQL com cobertura mínima, build da imagem e smoke test; na `main` publica a imagem com tag do commit, vai a staging e, por tag e aprovação, à produção. *(aula 12.02)*

**414. Como você faz rollback?** Reimplantando a imagem anterior (tag de versão/commit). Exige imagens imutáveis e migrações compatíveis com a versão anterior (expandir e contrair); mudanças destrutivas pedem backup. *(aula 12.02)*

**415. Rolling × blue/green × canary?** Rolling troca as instâncias aos poucos; blue/green mantém dois ambientes e vira o tráfego de uma vez (rollback imediato, custo dobrado); canary expõe uma pequena fração do tráfego à nova versão para observar. *(aula 12.02)*

**416. O que são environments no GitHub?** Ambientes nomeados com segredos, variáveis e regras de proteção (revisores obrigatórios); um job com `environment: production` pausa até aprovação. *(aula 12.02)*

## Módulo 13 — Introdução à nuvem com AWS

**417. Qual a diferença entre IaaS, PaaS e SaaS?** Quanto o provedor gerencia: em IaaS você cuida do SO para cima (EC2); em PaaS, da aplicação e dos dados (RDS, App Runner); em SaaS só usa o software. *(aula 13.01)*

**418. O que é o modelo de responsabilidade compartilhada?** O provedor protege a infraestrutura da nuvem; o cliente protege o que coloca nela: acessos, dados, configuração e, em IaaS, o SO. Um bucket público é responsabilidade do cliente. *(aula 13.01)*

**419. Que cuidados você toma ao criar uma conta de nuvem?** MFA na raiz e nenhuma chave nela; identidade comum com permissões mínimas e credenciais temporárias; orçamento e detecção de anomalias; tags, região definida e destruir recursos de estudo no mesmo dia. *(aula 13.01)*

**420. O que é lock-in e como reduzir?** Dependência de serviços proprietários que encarece a saída; reduz-se com contêineres, padrões abertos (PostgreSQL, S3-compatível), configuração por ambiente e IaC, ciente do equilíbrio com o trabalho que os gerenciados poupam. *(aula 13.02)*

**421. Qual a diferença entre usuário IAM e papel?** Usuário tem credenciais permanentes; papel é assumível e dá credenciais temporárias. Aplicações em EC2 usam papel, nunca chave embutida. *(aula 13.03)*

**422. O que é menor privilégio e como aplicar?** Só as ações necessárias, nos recursos exatos, para quem precisa; começar restrito e ampliar guiado pelo `AccessDenied`; condições e revisão de uso. *(aula 13.03)*

**423. Como sua aplicação na EC2 acessa o S3 sem chaves?** Por um papel associado à instância (instance profile): o SDK obtém credenciais temporárias dos metadados (IMDSv2) e as renova; a política limita ao bucket/prefixo. *(aula 13.03)*

**424. Como você protege uma EC2?** Security Group mínimo, sem SSH aberto (Session Manager), IMDSv2 obrigatório, papel IAM mínimo, disco criptografado, patches, logs e tags. *(aula 13.04)*

**425. Security Group × ACL de rede?** SG: com estado, por interface, só permite e pode referenciar outros SGs; ACL: por sub-rede, sem estado, regras ordenadas de permitir/negar. *(aula 13.04)*

**426. Por que usar RDS em vez de PostgreSQL numa EC2?** Automatiza provisionamento, patches, backups com PITR, monitoramento e alta disponibilidade opcional, reduzindo trabalho e risco; custa mais e dá menos controle do SO. *(aula 13.05)*

**427. Como proteger o banco em nuvem?** Sem IP público, SG que só aceita a aplicação, TLS, criptografia em repouso, usuário de aplicação de menor privilégio, senha em gerenciador de segredos, backups testados e proteção contra exclusão. *(aula 13.05)*

**428. Como guardar arquivos de usuários na nuvem?** Em armazenamento de objetos (S3) privado, criptografado, com política IAM restrita ao prefixo e URLs pré-assinadas curtas; o Django usa `django-storages` com configuração por ambiente. *(aula 13.06)*

**429. O que é uma URL pré-assinada?** URL com permissão temporária embutida, assinada com credenciais do servidor, para um objeto e operação; quem a tem acessa até expirar, por isso o prazo deve ser curto. *(aula 13.06)*

**430. Como validar upload de imagem?** Limitar tamanho, verificar o conteúdo com uma biblioteca de imagem, gerar o nome no servidor, restringir quem envia e guardar fora do disco da aplicação. *(aula 13.06)*

**431. Como foi o deploy do seu projeto e por que essa escolha?** Imagem no ECR rodando em Compose numa EC2, PostgreSQL no RDS, mídia no S3 e segredos no Parameter Store, por custo e aprendizado, ciente de ser um servidor só e sem HTTPS sem domínio; em produção usaria Fargate/ECS atrás de um balanceador com certificado gerenciado. *(aula 13.07)*

**432. Como o pipeline faz deploy sem guardar chaves da AWS?** OIDC: o GitHub emite um token efêmero que a AWS troca por credenciais temporárias de um papel cuja confiança restringe repositório e tag. *(aula 13.07)*

**433. Onde ficam as senhas da aplicação na nuvem?** Num gerenciador de segredos (Parameter Store `SecureString` ou Secrets Manager), acesso por IAM restrito ao caminho; a instância os lê com o papel; nada no Git, na imagem nem no user-data. *(aula 13.08)*

**434. Como evitar custos esquecidos em estudo?** Orçamento antes de criar, tags, scripts de criação e destruição versionados, destruição no mesmo dia com conferência por região e conferência do painel no dia seguinte. *(aula 13.08)*

**435. Por que "parar" um RDS ou uma EC2 não zera o custo?** Armazenamento, backups, discos e IPs continuam cobrando, e o RDS pode ser religado automaticamente; para estudo, apague. *(aulas 13.01, 13.05 e 13.08)*

## Módulo 14 — Produção e observabilidade básica

**436. O que são logs estruturados e por que usá-los?** Eventos em formato fixo (JSON) com campos consultáveis; permitem filtrar, agregar e correlacionar por `request_id` em ferramentas como CloudWatch Insights ou Loki. *(aula 14.01)*

**437. Diferença entre liveness e readiness?** Liveness: o processo está vivo (falha → reiniciar), sem checar dependências; readiness: consegue atender, checando banco/cache (falha → sai da rotação). Misturá-las causa reinícios em cascata. *(aula 14.01)*

**438. Como rastrear uma requisição entre componentes?** ID de correlação gerado na borda (proxy), repassado por cabeçalho, registrado em todos os logs e devolvido na resposta; validar o ID recebido evita injeção de log. *(aula 14.01)*

**439. O que nunca vai para o log?** Senhas, tokens, cookies, `Authorization`, chaves e dados pessoais; a query string também (carrega tokens). *(aula 14.01)*

**440. Logs × métricas × erros × traces?** Logs: detalhe de eventos; métricas: agregados no tempo para tendência e alerta; erros (Sentry): exceções agrupadas por release; traces: onde foi o tempo de uma requisição. *(aula 14.02)*

**441. Que cuidados tem com o Sentry?** Só 500 inesperados, `release` e `environment`, sem dados pessoais (configuração restritiva e `before_send` testado), cuidado com código-fonte anexado e controle da cota. *(aula 14.02)*

**442. O que é cardinalidade em métricas?** Número de combinações de rótulos (séries). Valores ilimitados (ID, e-mail, caminho cru) derrubam o servidor; use o padrão da rota. *(aula 14.02)*

**443. Por que a média engana e o que usar?** Esconde a cauda; histogramas e percentis (p95/p99). *(aula 14.02)*

**444. Como implementa cache e como invalida?** Cache-aside com TTL; invalidação por versão na chave, disparada no commit por todo caminho que muda o dado (inclusive `update()` em lote). *(aula 14.03)*

**445. O que acontece se o Redis cair?** O cache é só otimização: leituras seguem sem ele (timeouts curtos), a readiness acusa 503 e a liveness não; limite geral de taxa falha aberto e o de login falha fechado. *(aula 14.03)*

**446. Riscos do cache?** Dados velhos, vazamento entre usuários, stampede, memória sem limite, acoplamento; mitigados por TTL, escopo correto, `maxmemory`+LRU, jitter/locks e falha aberta. *(aula 14.03)*

**447. Como acha uma consulta lenta?** Métricas por rota, depois log de lentas e `pg_stat_statements` por tempo total, `EXPLAIN (ANALYZE, BUFFERS)`, corrige e mede de novo. *(aula 14.04)*

**448. Quando um índice não ajuda?** `COUNT(*)`, `LIKE '%x%'` (precisa de trigramas), coluna que não é prefixo do índice composto, tabelas pequenas; e ele custa nas escritas. *(aula 14.04)*

**449. OFFSET × cursor?** OFFSET produz e descarta N linhas (custo cresce); cursor/keyset salta pelo índice com custo constante, mas não permite ir para a página N. *(aula 14.04)*

**450. O que são RPO e RTO?** RPO: quanto dado se aceita perder; RTO: em quanto tempo se volta ao ar. *(aula 14.04)*

**451. Como garante que o backup funciona?** Arquivo verificado (checksum e leitura), retenção e cópia externa cifrada, teste periódico de restauração que confere o conteúdo e mede o RTO, e alerta se não houver backup recente. *(aula 14.04)*

**452. O que é Pydantic e como o FastAPI o usa?** Biblioteca de validação e serialização por tipos; o FastAPI lê as anotações das rotas e delega a ela a conversão e a validação de caminho, query e corpo, e usa os modelos para gerar o OpenAPI. *(aula 15.01)*

**453. Pydantic ou serializer do DRF?** O serializer é acoplado ao Django (ORM, mensagens traduzidas, erro 400 agrupado por campo); o Pydantic é independente de framework, mais rígido com tipos, e normalmente separa modelos de entrada e saída. *(aula 15.01)*

**454. Por que o FastAPI responde 422 e não 400?** O corpo estava bem formado mas semanticamente inválido; é a escolha do framework (o DRF usa 400). Importa documentar. O 422 também ecoa o `input`, o que pode vazar dado sensível. *(aula 15.01)*

**455. Por que usar `ProductIn` e `ProductOut` separados?** Para não aceitar nem expor campos internos por acidente e para um contrato OpenAPI preciso. *(aula 15.01)*

**456. Qual a diferença entre o ORM do Django e o SQLAlchemy?** Django: active record integrado (migrações e admin inclusos). SQLAlchemy: mapeamento, sessão e consulta separados (unit of work), mais explícito e independente de framework; migrações via Alembic. *(aula 15.02)*

**457. O que é N+1 e como evitar no SQLAlchemy?** Uma consulta para a lista e uma por item; use `joinedload`/`contains_eager` (muitos-para-um) ou `selectinload` (coleções); em async o lazy load nem funciona (`MissingGreenlet`). *(aula 15.02)*

**458. Por que revisar uma migração autogerada?** O autogenerate não entende intenção (renomeação vira drop+add, perdendo dados) e renderiza defaults conforme o dialeto em que rodou (um `server_default` de SQLite quebrou no PostgreSQL). *(aula 15.02)*

**459. O que o `alembic check` faz?** Compara os modelos com o banco e falha se faltar migração; é o equivalente de `makemigrations --check`, bom para a CI. *(aula 15.02)*

**460. `async def` ou `def` numa rota FastAPI?** `async def` roda no laço de eventos e exige bibliotecas async; `def` roda numa thread do pool, adequado para código bloqueante. Bloqueio dentro de `async def` trava todas as requisições do processo. *(aula 15.03)*

**461. Como funciona a injeção de dependências do FastAPI?** `Depends` resolve em árvore, por requisição e com cache por requisição; `yield` faz setup/teardown (sessão do banco); em testes `dependency_overrides` troca qualquer uma. *(aula 15.03)*

**462. Como você testa uma API FastAPI?** `pytest` + `pytest-asyncio`, `httpx.AsyncClient` com `ASGITransport`, banco isolado por `dependency_overrides`, `parametrize` nos casos inválidos e a mesma suíte nos bancos que usa. *(aula 15.04)*

**463. Como testar código que chama um serviço externo?** Injetar o cliente e usar um transporte simulado (`MockTransport`), cobrindo sucesso, timeout, 5xx e resposta inesperada. *(aula 15.04)*

**464. Como garantir que a nova API se comporta como a antiga?** Testes de contrato: as mesmas requisições nas duas, comparação automática (ignorando campos voláteis) e decisão explícita para cada diferença. *(aula 15.05)*

**465. Quando escolher FastAPI em vez de Django?** API focada com muita E/S concorrente ou contrato tipado e documentação automática, sem necessidade de admin/ORM/auth prontos; para sistema completo com admin e regras, Django. *(aula 15.06)*

**466. FastAPI é mais rápido que Django?** Em E/S concorrente pode ser, pelo modelo async; numa API dominada pelo banco, na minha medição ficou empatado (cerca de 330 × 312 req/s com 1 em voo, 469 × 470 com 20). O gargalo costuma ser consulta, índice e cache. *(aula 15.06)*

**467. Você migraria um sistema Django para FastAPI?** Só com gargalo medido que não se resolva dentro do Django, plano por fatias e testes de contrato; por modismo, não. *(aula 15.06)*

## Módulo 16 — Pronto para o mercado

**468. Como deve ser o README de um projeto de portfólio?** Título e frase, selo da CI, print real, o que demonstra (itens verificáveis), como rodar em poucos comandos, decisões técnicas, limitações honestas e contato; e testado num clone limpo. *(aula 16.01)*

**469. Achou uma senha no histórico do Git. E agora?** Revogar e gerar outra (o segredo já foi exposto); só depois, se necessário, limpar o histórico. *(aula 16.01)*

**470. Como transformar "Responsável pelo backend" num bullet melhor?** Verbo + o quê + tecnologia + prova: "Implementei a baixa de estoque transacional (Django, PostgreSQL) e testei a concorrência". *(aula 16.02)*

**471. Por que `LEFT JOIN … WHERE p.status = 'pago'` perde linhas?** O `WHERE` sobre a tabela da direita descarta os `NULL` e o `LEFT` vira `INNER`; ponha o filtro no `ON`. *(aula 16.04)*

**472. Por que `NOT IN` falha com `NULL`?** Se a subconsulta tiver um `NULL`, a comparação vira "desconhecida" e o resultado é vazio; use `NOT EXISTS`. *(aula 16.04)*

**473. `DELETE` é idempotente?** No efeito, sim (o recurso fica apagado), mesmo que o status mude de 204 para 404. *(aula 16.04)*

**474. Como recuperar um commit perdido num `reset --hard`?** `git reflog` para achar o hash/`HEAD@{n}` e `git reset --hard` para ele. *(aula 16.04)*

**475. Como impedir reserva dupla do mesmo horário?** Checar e inserir de forma atômica (trava de escrita ou restrição de exclusão no banco), retornar 409 e testar com requisições concorrentes repetidas. *(aula 16.07)*

**476. Num take-home, o enunciado é omisso. O que faz?** Pergunta, se puder; se não, escolhe, documenta no README e cobre com teste. *(aula 16.06)*

**477. Como apresentar seu projeto em 5 minutos?** Problema, arquitetura, uma decisão difícil, como sabe que funciona, limitações e próximo passo. *(aula 16.07)*
