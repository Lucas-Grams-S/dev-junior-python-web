# 6. Code review, Conventional Commits e README

> ⏱️ ~1h30 · Módulo 10 · Pré-requisitos: [10.05](05-ruff-mypy-precommit.md), [9.05 (controle de acesso)](../09-seguranca/05-controle-acesso-idor.md), [9.06 (segurança)](../09-seguranca/06-segredos-dependencias-headers-rate-limit.md), [Módulo 0 (Git)](../00-ambiente-ferramentas/README.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop, que nesta aula é um **repositório Git de trabalho** (local, só para o curso). Python 3.13, Django 5.2.19, `commitizen` 4.19. O PR da aula é **simulado por mim** (autor e revisor), com código e testes reais; **as saídas são reais**. A suíte terminou em **297 passed, 1 skipped, 1 xfailed**.

## 🎯 Objetivos
- Escrever e **validar** mensagens no padrão **Conventional Commits** e entender como elas viram **versão** e **changelog**
- **Revisar** código de forma útil: o que a máquina já cobre, o que só gente vê, como classificar e redigir comentários
- Provar um comentário de revisão **com um teste que falha**
- Escrever **PRs pequenos**, com descrição que ajuda, e responder a revisões
- Montar um **README** profissional e verificá-lo: "se o README manda rodar, eu rodei"

## 🤔 Por que isso importa
Em equipe, código é lido muito mais do que escrito, e o que você entrega é julgado pela **história** que conta (commits), pela **conversa** que gera (revisão) e pela **porta de entrada** que oferece (README). Um histórico legível permite achar quando um bug nasceu; uma revisão boa evita incidentes; um README honesto economiza horas de quem chega. Tudo isso é visível no seu portfólio e é tema recorrente de entrevistas ("como é uma boa mensagem de commit?", "como você faz code review?").

## 💡 Intuição (explicação simples)
- **Commits** são o **diário de bordo** do projeto: cada entrada diz *o que mudou e por quê*, num formato que dá para ler e para filtrar por máquina.
- **Code review** é uma **segunda leitura por alguém que não está apaixonado pelo texto**: o editor de um livro. Ele não reescreve; aponta onde o leitor vai tropeçar. As ferramentas (corretor ortográfico) já pegaram as vírgulas; o editor cuida do enredo.
- **README** é a **recepção do prédio**: quem chega precisa saber, em um minuto, o que é, como entrar e a quem recorrer.

## 🔬 Como funciona por dentro
### Conventional Commits
- **Formato:** `tipo(escopo): descrição` + corpo opcional + rodapé opcional. Tipos comuns: `feat` (funcionalidade), `fix` (correção), `refactor`, `perf`, `test`, `docs`, `style`, `build`, `ci`, `chore`. `!` depois do tipo (ou `BREAKING CHANGE:` no rodapé) marca **quebra de compatibilidade**.
- **Para que serve ser tão formal:** (1) a **versão** pode ser calculada: `fix` → PATCH, `feat` → MINOR, quebra → MAJOR ([versionamento semântico](https://semver.org/lang/pt-BR/)); (2) o **changelog** sai pronto; (3) a **busca** no histórico funciona (`git log --grep="^fix"`); (4) obriga a pensar *o que* é a mudança.
- **Boas mensagens:** imperativo e específico ("corrige arredondamento do cupom", não "ajustes"); o **porquê** no corpo quando não é óbvio; **um assunto por commit** (formatação e lógica separadas, como na aula 05).
- **Validação automática:** um hook `commit-msg` recusa mensagens fora do padrão (abaixo).

### Code review
- **Objetivo:** melhorar o código **e** espalhar conhecimento, não "achar culpados". A pergunta-guia é: *"este código deixa a base de código melhor do que estava?"*
- **Autor:** PR **pequeno** (uma ideia, idealmente < 400 linhas), descrição que conta o **porquê**, portões automáticos verdes **antes** de pedir revisão, e abertura para o que vier.
- **Revisor, em ordem:** (1) a descrição; (2) **os testes** (dizem o que o autor acha que o código faz); (3) o código. Pergunte por **correção** (bordas, concorrência), **segurança** (quem pode chamar? autorização por objeto? entrada indo para SQL/HTML/CSV/log?), **testes** (falhariam sem a mudança?), **design** (camada certa? testável sem banco?), **desempenho** (N+1, memória) e **operação** (migração segura, logs sem dados sensíveis).
- **Classifique os comentários:** `bloqueante:` (não entra assim), `sugestão:` (a critério do autor), `dúvida:`, `nit:` (detalhe opcional). Comente o **código, não a pessoa**; explique o porquê; **proponha uma saída ou escreva o teste que prova o problema**; elogie o que está bom.
- **O que a máquina cobre** (não gaste revisão humana): formatação, imports, tipos, SQL por concatenação, segredos, cobertura mínima. **O que só gente cobre:** se a regra de negócio está certa, se a segurança de verdade está respeitada, se o design vai envelhecer bem.

### README
- Responde, nesta ordem: **o que é**, **como rodar em 5 minutos**, **como testar**, **como contribuir**, **onde há mais** (arquitetura, decisões, segurança). Comandos **copiáveis**, pré-requisitos explícitos, configuração em tabela, sem segredos.
- **Um README que ninguém executa apodrece.** A regra aqui: todo comando do README foi executado numa cópia limpa.

## 🛠️ Exemplo prático
### Parte A: Conventional Commits com validação
**1. Configuração** (`pyproject.toml` e um hook `commit-msg`; a versão vem da última *tag* do Git):
```toml
[tool.commitizen]
name = "cz_conventional_commits"
version_provider = "scm"                # a versão vem da última tag do Git (não duplicamos em um arquivo)
tag_format = "v$version"
major_version_zero = true               # até a 1.0.0, 'feat!' sobe o MINOR (convenção de pré-1.0)
```
```yaml
      - id: conventional-commit
        name: mensagem de commit (Conventional Commits)
        entry: uv run cz check --allow-abort --commit-msg-file
        language: system
        stages: [commit-msg]
```
**2. O que ele aceita e o que recusa:**
```text
  "ajustes"                                     ❌ recusada
  "Corrigido bug"                               ❌ recusada
  "fix: corrige arredondamento"                 ✅ aceita
  "feat(orders): aplica cupom ao pedido"        ✅ aceita
  "feat(orders)!: muda o formato do total"      ✅ aceita
  "docs: README"                                ✅ aceita
```
E tentando commitar de verdade com uma mensagem ruim:
```text
$ git commit --allow-empty -m "ajustes"
mensagem de commit (Conventional Commits)................................Failed
- hook id: conventional-commit
- exit code: 14
commit validation: failed!
please enter a commit message in the commitizen format.
```
Nenhum commit foi criado. A mensagem de erro mostra até a expressão regular esperada.

### Parte B: um PR do começo ao fim
**Contexto:** a pessoa autora adiciona `GET /api/v1/orders/export/` (CSV dos pedidos). Ela trabalha numa branch `feat/exportar-pedidos`.

**3. Versão 1 do autor** (`apps/orders/export.py`), simples e "funciona":
```python
@api_view(["GET"])
def exportar_pedidos(request):
    resposta = HttpResponse(content_type="text/csv")
    escritor = csv.writer(resposta)
    escritor.writerow(["id", "cliente", "email", "total", "status"])
    for pedido in Order.objects.all():
        escritor.writerow([pedido.id, pedido.user.username, pedido.user.email, pedido.total, pedido.status])
    return resposta
```
**4. Os portões automáticos pegaram duas falhas do próprio autor** (antes de qualquer revisão): a rota levantava `TypeError: exportar_pedidos() got an unexpected keyword argument 'version'` (o versionamento da API passa o parâmetro `version`), e o schema OpenAPI ficou desatualizado (`test_schema_commitado_esta_em_dia` e `test_schema_gera_sem_avisos` falharam). O autor fez um segundo commit (`fix(orders): aceita o parâmetro de versão e documenta o CSV no schema`). Note que o **primeiro commit passou nos hooks** (lint, formato, tipos, segredos): eles não rodam os testes, e isso é de propósito (o commit precisa ser rápido). Quem pega testes quebrados é o `pre-push` e o CI. Depois do conserto:
```text
ruff check: All checks passed!   ruff format: 136 files already formatted
mypy: Success: no issues found in 81 source files
pytest: 293 passed, 1 skipped, 1 xfailed
```
**Todos os portões verdes.** E o PR **ainda tem três problemas sérios**. É aqui que entra a pessoa que revisa.

**5. A revisão** (comentários classificados; cada um tem um teste que o **prova**):
| # | Tipo | Comentário |
|---|---|---|
| 1 | **bloqueante** | "`Order.objects.all()` exporta os pedidos de **todos** os clientes para qualquer usuário autenticado (A01, IDOR). Deve ser só os do usuário. Se o atendimento precisar de uma exportação global, é outro endpoint, com permissão explícita e log de auditoria." |
| 2 | **bloqueante** | "Nome e e-mail vão direto para o CSV. Um nome de usuário como `+cmd` é válido no Django e, aberto numa planilha, é interpretado como **fórmula** (*CSV injection*). Neutralizar células de texto." |
| 3 | **sugestão forte** | "`pedido.user` dentro do laço faz uma consulta por pedido (N+1), e a lista inteira vai para a memória. Use `select_related` e leia em blocos." |
| 4 | dúvida | "Precisamos mesmo do e-mail no CSV? (minimização de dados, LGPD)" |
| 5 | nit | "`escritor`/`resposta` ficariam mais legíveis com um `with`/função auxiliar; opcional." |
| 6 | elogio | "Boa ideia documentar o `text/csv` no schema." |
O revisor **não discute**: escreve três testes que falham (`tests/test_exportar_pedidos.py`), com o código do autor:
```python
def test_o_csv_so_traz_os_pedidos_do_proprio_usuario(api_as, pedidos_de_duas_pessoas):  # comentário 1 (bloqueante)
    linhas = linhas_csv(api_as("cliente").get("/api/v1/orders/export/"))
    assert {linha[1] for linha in linhas[1:]} == {"cliente"} and len(linhas) == 2  # cabeçalho + 1 pedido


def test_celulas_de_texto_nao_viram_formulas_na_planilha(api_as, pedidos_de_duas_pessoas):  # comentário 2 (bloqueante)
    _cliente, outro = pedidos_de_duas_pessoas
    outro.set_password("dev-somente-local-123")
    outro.save()
    linhas = linhas_csv(api_as("+cmd").get("/api/v1/orders/export/"))
    textos = [celula for linha in linhas[1:] for celula in linha[1:3]]
    assert all(not t.startswith(("=", "+", "-", "@")) for t in textos), textos
```
```python
def consultas_da_exportacao(api):
    with CaptureQueriesContext(connection) as ctx:
        api.get("/api/v1/orders/export/")
    return len(ctx)


def test_o_numero_de_consultas_nao_cresce_com_o_numero_de_pedidos(api_as, pedidos_de_duas_pessoas, criar_produto):  # comentário 3
    _cliente, outro = pedidos_de_duas_pessoas
    outro.set_password("dev-somente-local-123")
    outro.save()
    api = api_as("+cmd")
    com_3_pedidos = consultas_da_exportacao(api)
    produto = criar_produto(estoque=50)
    for _ in range(5):  # mais cinco pedidos do mesmo usuário
        carrinho.add_item(outro, produto.pk, 1)
        pedidos.create_order(outro)
    com_8_pedidos = consultas_da_exportacao(api)
    assert com_8_pedidos == com_3_pedidos, f"{com_3_pedidos} consultas com 3 pedidos, {com_8_pedidos} com 8: há consulta por pedido (N+1)"
```
Resultado contra o código do autor (🔴):
```text
E       AssertionError: assert ({'+cmd', 'cliente'} == {'cliente'}
E       AssertionError: ['+cmd', '', '+cmd', '', '+cmd', '', ...]
E       AssertionError: 6 consultas com 3 pedidos, 11 com 8: há consulta por pedido (N+1)
FAILED tests/test_exportar_pedidos.py::test_o_csv_so_traz_os_pedidos_do_proprio_usuario
FAILED tests/test_exportar_pedidos.py::test_celulas_de_texto_nao_viram_formulas_na_planilha
FAILED tests/test_exportar_pedidos.py::test_o_numero_de_consultas_nao_cresce_com_o_numero_de_pedidos
3 failed, 2 passed in 0.65s
```
Os três comentários principais (dois bloqueantes e uma sugestão forte) ficaram **provados**: `{'+cmd', 'cliente'}` onde só `cliente` era esperado; células que começam com `+`; e **6 consultas com 3 pedidos contra 11 com 8**, ou seja, uma consulta a mais por pedido.
> 🔎 **Uma falha do próprio revisor.** Meu primeiro teste de consultas fixava "no máximo 4". Mesmo depois da correção ele falhava, porque uma requisição autenticada já gasta cerca de 4 consultas só com login e permissões. **O número arbitrário estava errado, não o código.** O teste certo não fixa um valor: ele compara o total com 3 pedidos e com 8 e exige que sejam **iguais**. Testes de revisão também precisam ser revisados.
> 🔎 **E os hooks valeram para o revisor.** Meus commits do arquivo de teste foram **barrados pelo `pre-commit`** (nome de variável `l`, ambíguo, e uma variável não usada). Corrigi e commitei de novo.

**6. As correções do autor, um commit por comentário** (cada um deixa os testes mais verdes):
```python
import csv

from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view

from .models import Order

# Planilhas (Excel, Sheets, LibreOffice) executam células que começam com estes caracteres como FÓRMULA (CSV injection).
PREFIXOS_DE_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def celula_segura(valor: object) -> str:
    """Texto controlado pelo usuário (nome, e-mail) é neutralizado com um apóstrofo inicial."""
    texto = str(valor)
    return "'" + texto if texto.startswith(PREFIXOS_DE_FORMULA) else texto


@extend_schema(summary="Exporta pedidos em CSV", responses={(200, "text/csv"): OpenApiTypes.STR})
@api_view(["GET"])
def exportar_pedidos(request, **kwargs):
    resposta = HttpResponse(content_type="text/csv")
    escritor = csv.writer(resposta)
    escritor.writerow(["id", "cliente", "email", "total", "status"])
    pedidos = Order.objects.filter(user=request.user).select_related("user")
    for pedido in pedidos.iterator(chunk_size=500):  # lê em blocos: não carrega tudo na memória
        escritor.writerow([pedido.id, celula_segura(pedido.user.username), celula_segura(pedido.user.email), pedido.total, pedido.status])
    return resposta
```
Resultado (🟢):
```text
5 passed in 0.61s
```
**7. Merge e histórico** (merge com `--no-ff` para preservar o PR como um bloco):
```text
*   3151477 feat(orders): exporta os pedidos do usuário em CSV (#12)
|\
| * 3efb542 perf(orders): carrega o usuário com select_related e lê os pedidos em blocos
| * 7531ecd fix(security): neutraliza fórmulas de planilha nas células de texto do CSV
| * d519f4f fix(orders): limita a exportação aos pedidos do usuário autenticado
| * deeee95 test(orders): testes do revisor para a exportação (acesso, fórmulas e consultas)
| * 5059f3b fix(orders): aceita o parâmetro de versão e documenta o CSV no schema
| * bdb1baa feat(orders): exporta os pedidos em CSV
|/
* 9f11596 build: valida a mensagem de commit com commitizen (Conventional Commits)
```
Cada linha é uma decisão que dá para ler, reverter ou entender depois. Compare com o que seria `git log` com "ajustes", "mais um fix" e "agora vai".

**8. Versão e changelog gerados do histórico** (`cz bump --dry-run`, `cz changelog --dry-run`; a *tag* `v0.9.0` marca o fim do módulo 9):
```text
bump: version 0.9.0 → 0.10.0
tag to create: v0.10.0
increment detected: MINOR

## v0.10.0 (2026-11-08)
```
```text
## Unreleased

### Feat

- **orders**: exporta os pedidos do usuário em CSV (#12)
- **orders**: exporta os pedidos em CSV
- **types**: mypy com django-stubs (estrito nos módulos puros) e correção do bug de 'hoje' nos cupons

### Fix

- **security**: neutraliza fórmulas de planilha nas células de texto do CSV
- **orders**: limita a exportação aos pedidos do usuário autenticado
- **orders**: aceita o parâmetro de versão e documenta o CSV no schema
- **ruff**: force-exclude para o pre-commit respeitar migrações e código gerado

### Refactor

- corrige avisos do ruff (__str__ nos modelos, nomes claros, imports no topo)

### Perf

- **orders**: carrega o usuário com select_related e lê os pedidos em blocos

## v0.9.0 (2026-11-08)
```
O tipo dos commits **decidiu a versão** (`0.9.0 → 0.10.0`, incremento MINOR porque há `feat`) e organizou o changelog em `Feat`, `Fix`, `Refactor` e `Perf`. *(Um tropeço de ambiente: o primeiro `git tag -a` ficou parado porque a minha configuração global manda assinar *tags* com GPG e o comando esperava a senha; desativei a assinatura só neste repositório de teste. Se você usa tags assinadas, lembre que o comando pode ficar esperando.)*

### Parte C: os artefatos de colaboração
**9. Modelo de PR, guia de revisão e `CONTRIBUTING`** (no repositório: `.github/pull_request_template.md`, `docs/code-review.md`, `CONTRIBUTING.md`):
```markdown
## O quê e por quê
<!-- Em 2-3 frases: o problema e a solução. Link para a issue, se houver. -->

## Como testar
<!-- Passos ou comandos para o revisor reproduzir. -->

## Checklist do autor
- [ ] Testes novos/ajustados (regra de negócio e bug: o teste **falhava antes**)
- [ ] `pytest`, `ruff`, `mypy` e `lint-imports` verdes; cobertura das camadas de negócio >= 80%
- [ ] Sem segredos, sem dados pessoais em logs; entradas validadas no servidor
- [ ] Autorização por objeto conferida (um segundo usuário não acessa o que não é dele)
- [ ] Migrações e contrato OpenAPI revisados (`makemigrations --check`, `schema.yml`)
- [ ] Documentação/README/ADR atualizados, se a decisão for relevante
- [ ] Commits no padrão Conventional Commits; formatação em commit separado

## Riscos e pontos de atenção para a revisão
<!-- O que você gostaria que o revisor olhasse com mais cuidado? -->
```
O guia de revisão (tabela "olhe para / pergunte") e a convenção de commits ficam em `docs/code-review.md` e `CONTRIBUTING.md`, que o PR template referencia.

**10. O README, verificado.** O `README.md` do MiniShop traz: o que é, recursos, **Começando**, testes e qualidade, arquitetura, tabela de configuração e licença. Para cumprir a regra "tudo que o README manda, eu rodei", clonei o repositório numa pasta limpa e executei os comandos dele:
```text
uv sync → ok · migrate → ok · seed → "Seed ok: 64 produtos" · runserver → login devolve token (231 caracteres)
GET /api/v1/products/ → {"count":61,...} · /api/docs/ → 200
pytest: 297 passed, 1 skipped, 1 xfailed · pytest -m unidade: 62 passed · pytest -n 4: 297 passed
ruff check: All checks passed! · ruff format --check: 140 files already formatted
mypy: Success: no issues found in 81 source files · lint-imports: 3 contratos cumpridos
```
> 🔎 **O hook de segredos barrou o meu próprio README.** O exemplo de `curl` mostra a senha de **desenvolvimento** (`dev-somente-local-123`) e a tabela mostra `postgres://usuario:senha@host/...`. O `detect-secrets` os reportou como achados novos; conferi um a um (senha documentada que só vale com `DEBUG=1`, e um exemplo com `usuario:senha`) e só então os registrei no *baseline* (de 4 para 6 achados triados). **Triar não é ignorar:** cada entrada do baseline é uma decisão humana que alguém revisou.

**11. Estado final**
```text
297 passed, 1 skipped, 1 xfailed     ruff · mypy · lint-imports: limpos     cobertura das camadas de negócio >= 80%
```

## 🧠 Pausa para lógica
**Problema.** Você recebe um PR de 1 800 linhas, com o título "melhorias" e a descrição vazia, que mistura formatação, renomeações e uma regra de negócio nova. (a) Que comentário geral você faz antes de ler o código? (b) Como o autor deveria reorganizar? (c) Quais três perguntas de segurança você faria para qualquer endpoint novo?

<details><summary>Dica</summary>Pense em tamanho, assunto único, e na lista da aula 9 (quem chama? o que entra? o que sai?).</details>

<details><summary>Solução comentada</summary>

(a) "Este PR está grande demais para eu revisar bem e mistura assuntos; por favor divida e descreva o porquê." Revisar 1 800 linhas misturadas é pedir para passar despercebido um erro. (b) Commits/PRs separados: 1) só formatação (com `.git-blame-ignore-revs`), 2) renomeações mecânicas, 3) a regra de negócio com seus testes; cada um com título no padrão (`style:`, `refactor:`, `feat:`). (c) **Quem pode chamar?** (autenticação e autorização por objeto); **o que entra?** (validação no servidor; o dado do usuário vai para SQL, HTML, CSV, log, comando?); **o que sai?** (campos sensíveis, dados de outras pessoas, volume).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| Mensagens "ajustes", "fix", "wip" | Sem convenção | Conventional Commits + hook `commit-msg` |
| Formatação e lógica no mesmo commit | Pressa | Commits separados; `.git-blame-ignore-revs` |
| PR gigante | Acumular trabalho | Divida: uma ideia por PR, merge frequente |
| PR sem descrição | "O código fala por si" | Conte o porquê, como testar, riscos |
| Revisão que só fala de estilo | Máquina não configurada | Automatize estilo; humano revisa design e segurança |
| Comentário vago ("não gostei") | Falta de critério | Diga o problema, o porquê e uma saída; classifique |
| Discussão sem fim sobre um comentário | Opinião contra opinião | Escreva o **teste que prova**; ou decida por escrito |
| Revisar só o código, não os testes | Ordem errada | Comece pelos testes |
| Aprovar "porque os portões estão verdes" | Confiar na máquina | Verde significa só "nada que a máquina sabe procurar" |
| Levar a revisão para o lado pessoal | Código = identidade | O alvo é o código; agradeça, pergunte, responda |
| README que não funciona | Nunca executado | Rodar numa cópia limpa; automatizar no CI |
| README com segredo ou senha real | Cópia direta de `.env` | Exemplos fictícios; segredos no ambiente; varredura no hook |
| Tag assinada travando | Config global de GPG | Saiba que o comando espera; configure o agente ou desative onde não precisa |

- **Pequeno, frequente, reversível.**
- **Revisão é conversa:** pergunte antes de afirmar.
- **O histórico é documentação:** escreva para quem vai ler em seis meses.
- **Comece o README pelo leitor que chega agora.**

## 🧩 Exercícios
**1. Fixação.** (a) Como os tipos de commit definem a versão? (b) Por que a revisão começa pelos testes? (c) O que a máquina cobre e o que só a pessoa revisora cobre? (d) Por que o merge com `--no-ff` ajuda?

<details><summary>Solução</summary>

(a) `fix` incrementa PATCH, `feat` incrementa MINOR e uma quebra (`!` ou `BREAKING CHANGE`) incrementa MAJOR (no pré-1.0, MINOR). (b) Os testes dizem o que o autor acha que o código faz; assim você compara a intenção com a implementação e vê o que não está coberto. (c) Máquina: formatação, imports, tipos, padrões inseguros conhecidos, segredos, cobertura. Pessoa: se a regra está certa, a segurança real (autorização por objeto, fluxo de dados), o design e a clareza. (d) Cria um commit de merge que agrupa os commits do PR, preservando a história do que foi revisado junto e permitindo reverter o PR inteiro de uma vez.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `commitizen` configurado e o hook `commit-msg` barrando uma mensagem ruim (anexar a saída)
- [ ] Um PR **real** no seu repositório (mesmo que você mesmo revise): branch, descrição pelo template, revisão com comentários **classificados** e **pelo menos um teste vermelho do revisor**
- [ ] Histórico do PR com commits convencionais, formatação separada, merge `--no-ff`
- [ ] Uma *tag* e `cz bump --dry-run` / `cz changelog --dry-run` com a saída anexada
- [ ] `README.md` com "Começando" **executado numa cópia limpa** (registrar o que rodou e o resultado)
- [ ] `CONTRIBUTING.md`, `.github/pull_request_template.md` e `docs/code-review.md`
- [ ] Triar o *baseline* de segredos depois de escrever o README
- [ ] Commit `docs: README, CONTRIBUTING, modelo de PR e guia de code review`

**3. Desafio (opcional).** Faça o CI (módulo 12) rodar `cz check --rev-range origin/main..HEAD` para validar **todas** as mensagens do PR, e um passo que executa os comandos do "Começando" do README numa máquina limpa.

## 🎤 Na entrevista
- **O que é Conventional Commits e para que serve?** Um padrão de mensagens (`tipo(escopo): descrição`) que torna o histórico legível e permite gerar versão e changelog automaticamente.
- **Como você faz code review?** Leio a descrição, depois os testes, depois o código; confiro correção, segurança, testes, design e desempenho; classifico os comentários (bloqueante, sugestão, dúvida, nit), explico o porquê e, quando posso, escrevo um teste que prova o problema.
- **O que a automação pega e o que não pega?** Ela pega estilo, tipos, padrões inseguros conhecidos e cobertura; não pega regra de negócio errada nem falhas de autorização e design.
- **Como receber uma revisão difícil?** Separo o código de mim, pergunto o que não entendi, respondo a cada comentário (corrigi, discordo com argumento, ou abri uma issue) e agradeço.
- **O que tem num bom README?** O que é, como rodar em poucos minutos, como testar, como contribuir e onde há mais detalhes; com comandos que funcionam.
- **Por que PRs pequenos?** Revisão melhor, menos conflitos, entrega contínua e reversão simples.

## 📚 Para ir além
- 📄 Especificação: [Conventional Commits 1.0.0 (pt-br)](https://www.conventionalcommits.org/pt-br/v1.0.0/) e [Versionamento Semântico (pt-br)](https://semver.org/lang/pt-BR/).
- 📄 Ferramenta: [commitizen](https://commitizen-tools.github.io/commitizen/). Validação, versão e changelog (em inglês).
- 📄 Guia: [Google — Engineering Practices: Code Review](https://google.github.io/eng-practices/review/) e [como revisar](https://google.github.io/eng-practices/review/reviewer/). O que olhar e como comentar (em inglês).
- 📄 Artigo: [GitHub — How to write the perfect pull request](https://github.blog/developer-skills/github/how-to-write-the-perfect-pull-request/) (em inglês).
- 📄 Documentação: [Modelos de Pull Request no GitHub](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository) (em inglês).
- 📄 Referência: [OWASP — CSV Injection](https://owasp.org/www-community/attacks/CSV_Injection). Por que células que começam com `=`, `+`, `-` ou `@` são perigosas (em inglês).
- 📄 Guia: [Keep a Changelog (pt-br)](https://keepachangelog.com/pt-BR/1.1.0/) e [Make a README](https://www.makeareadme.com/).
- 📘 Livro: [Pro Git (pt-br)](https://git-scm.com/book/pt-br/v2), gratuito. Ramos, *merge* e histórico.
- 📄 Tutorial: [Atlassian — Fluxo de trabalho com feature branch](https://www.atlassian.com/br/git/tutorials/comparing-workflows/feature-branch-workflow).

## ✅ Checklist da aula
- [ ] Escrevo mensagens no padrão e um hook as valida
- [ ] Sei como o tipo do commit vira versão e changelog
- [ ] Revisei um PR classificando comentários e provando o principal com um teste
- [ ] Abri PRs pequenos, com descrição e portões verdes
- [ ] Meu README foi executado numa cópia limpa
