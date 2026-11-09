# 5. Quebra de controle de acesso (IDOR) e a matriz de autorização

> ⏱️ ~1h30 · Módulo 9 · Pré-requisitos: [9.01](01-owasp-ameacas.md), [9.04](04-senhas-autenticacao.md), [6.07 (permissões no DRF)](../06-apis-rest/07-drf-permissoes.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19, DRF 3.18). **As saídas são reais.** A aula é **defensiva**: em vez de explorar uma falha alheia, você escreve a **política de acesso como uma tabela**, faz o código ser conferido contra ela e **prova, por mutação, que o teste pega o erro** quando a proteção é removida do *seu* código.

## 🎯 Objetivos
- Explicar **IDOR/BOLA** (referência direta insegura a objeto) e por que ele lidera o OWASP Top 10 (A01)
- Distinguir **permissão por papel** (pode criar produtos?) de **permissão por objeto** (este pedido é seu?)
- Escrever a **política de autorização como tabela** e conferi-la com **testes parametrizados** (papel × ação × dono)
- Escolher entre **`404`** e **`403`** conforme o que revelar
- Validar a rede de testes **por mutação** e tratar **conflitos** (`409`) em vez de deixar virar `500`

## 🤔 Por que isso importa
A categoria **A01: Broken Access Control** está em 1º lugar no OWASP desde 2021 e se mantém em 2025: é a falha mais comum e mais cara, porque o código “funciona”: a requisição é válida, o usuário está logado, e mesmo assim lê ou altera o que não é dele. Nenhuma ferramenta automática a encontra sozinha, pois **só você sabe a regra** (“pedido é de quem o criou”). A defesa é transformar essa regra em **teste**.

## 💡 Intuição (explicação simples)
Num hotel, a chave abre o **seu** quarto. Um atacante com uma chave de hóspede não precisa arrombar a porta: basta **tentar maçanetas vizinhas** (quarto 305, 306…). Se o sistema só confere “este hóspede tem uma chave válida?” e não “esta chave é **deste** quarto?”, qualquer chave abre qualquer porta. Mudar o número no endereço (`/orders/1/` → `/orders/2/`) é tentar a maçaneta vizinha. A correção não é esconder os números (IDs “aleatórios” ajudam pouco): é **a porta conferir a quem pertence**.

## 🔬 Como funciona por dentro
- **Autenticar não é autorizar.** O token provou *quem* é a pessoa. A pergunta seguinte é *“esta pessoa pode fazer **esta ação** sobre **este objeto**?”* (aula 04).
- **Dois níveis:**
  1. **Por papel/ação (função):** “quem pode criar produtos?” → permissões do Django/DRF (`DjangoModelPermissions`).
  2. **Por objeto (propriedade):** “este pedido é meu?” → filtrar a consulta pelo dono ou checar `has_object_permission`. Falhar aqui é o **IDOR** (também chamado **BOLA**, *Broken Object Level Authorization*, no OWASP API Top 10).
- **Falhas típicas:** `Order.objects.get(pk=pk)` sem filtrar o dono; rota de ação (`/pay/`, `/cancel/`, `/export/`) esquecida enquanto a de leitura está protegida; ouvir o `user_id` **do corpo** da requisição em vez do usuário autenticado; permitir que o cliente envie campos que só o servidor deveria definir (***mass assignment***: `is_staff`, `status`, `total`, `owner`).
- **Padrão que funciona:** a **consulta base já é restrita ao que o usuário pode ver** (`pedidos_visiveis(user)` no selector, aula 8.02). Se o objeto não está na consulta, ele **“não existe”** (404). Qualquer ação posterior parte dessa consulta.
- **`404` ou `403`?** `403` confirma que o recurso **existe** e que você não pode usá-lo; `404` não confirma nada. Para recursos **de outro usuário**, prefira `404` (não vazar existência); use `403` quando a existência é pública e a ação é que é proibida (cliente tentando criar produto).
- **Mais privilégio do que o necessário:** o papel “Gerente” administra o catálogo; ele precisa ver os pedidos dos clientes? Se não, **não dê**. Menor privilégio também é regra de autorização.
- **A política mora numa tabela, não na cabeça.** Uma matriz *papel × ação* escrita à mão e conferida por testes transforma “achamos que está certo” em “provamos que está certo (para estes casos)”.

## 🛠️ Exemplo prático
**1. Como o MiniShop decide o acesso a pedidos (já feito nos módulos 6 e 8)**
```python
# apps/orders/selectors.py: a REGRA de visibilidade
def pedidos_visiveis(user):
    qs = Order.objects.prefetch_related("items__product")
    return qs if user.has_perm("orders.view_order") else qs.filter(user=user)      # o alheio "não existe" (404)

# apps/orders/api.py: cancelar exige autenticado E dono (permissão por objeto)
def get_permissions(self):
    if self.action == "cancel":
        return [IsAuthenticated(), IsOwner()]

# apps/payments/api.py: pagar parte da consulta restrita ao dono
order = get_object_or_404(Order.objects.filter(user=request.user), pk=pk)
```

**2. A política escrita à mão, como tabela** (`tests/test_matriz_autorizacao.py`). Cada linha é um *papel*; cada coluna, uma *ação*; o valor é o **código HTTP esperado**:
```python
# ator -> (código por ação). Ações sobre um pedido e um item de carrinho do DONO ("cliente").
POLITICA = {
    #                ver_pedido, cancelar, pagar, mexer_no_item_alheio, criar_produto, apagar_produto
    "anonimo":     (401, 401, 401, 401, 401, 401),
    "dono":        (200, 200, 201, 200, 403, 403),    # pagar cria a cobrança (201); mexer no PRÓPRIO item é permitido
    "outro":       (404, 404, 404, 404, 403, 403),    # recurso alheio "não existe" para ele
    "estoquista":  (404, 404, 404, 404, 403, 403),    # papel de catálogo: NÃO tem acesso a pedidos alheios (menor privilégio)
    "gerente":     (404, 404, 404, 404, 201, 409),    # gerencia catálogo; produto já vendido não pode ser apagado (409)
    "atendimento": (200, 403, 404, 404, 403, 403),    # tem `orders.view_order`: VÊ todos os pedidos, mas não cancela nem paga por ninguém
}
```
Seis ações atravessam o código (ver, cancelar e pagar um pedido; alterar um item do carrinho alheio; criar e apagar produtos), e há **seis papéis**: anônimo, o dono, **outro cliente**, estoquista, gerente e **atendimento** (um papel com a permissão `orders.view_order`). O teste percorre todas as combinações (e mais um: *a lista de pedidos de outro cliente vem vazia*).

**3. Primeira execução: 6 falhas, e a lição de separar “política errada” de “código errado”**
| Falha | Causa real | Quem estava errado |
|---|---|---|
| Estoquista e gerente recebiam `404` ao ver pedido alheio (eu esperava `200`) | Nenhum papel do seed tem `orders.view_order`: eles veem só os próprios pedidos | **A minha tabela.** O código estava certo (menor privilégio) |
| Gerente criando produto dava `400` | O corpo usava `category`, mas o campo de escrita é `category_slug`; depois o `sku` precisa do formato `AAA-123` | **O meu teste** |
| Gerente apagando um produto já vendido: `ProtectedError` | A chave estrangeira `OrderItem.product` é protegida e a exceção **não era tratada** | **O código.** Em produção seria um `500` (A10, condições excepcionais) |
Corrigi a tabela (e acrescentei o papel **Atendimento**, que realmente tem a permissão), o teste, e o **código**: o tratador de erros agora converte `ProtectedError` em `409 Conflict` com o corpo padronizado `{"detail": "...", "code": "in_use"}`:
```python
class ConflictError(APIException):
    """O recurso existe, mas o estado atual impede a operação (ex.: apagar o que ainda é referenciado): 409."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = "O recurso está em uso e não pode ser removido."
    default_code = "in_use"
```
Dois testes novos: o gerente apaga um produto **nunca vendido** (`204`) e recebe `409` com `code: "in_use"` ao apagar um **vendido**.

**4. Resultado e validação**
```bash
uv run pytest -q tests/test_matriz_autorizacao.py
```
```text
39 passed
```
**Um teste que sempre passa não prova nada.** Por isso, três **mutações** no *meu* código (estragar a proteção de propósito e ver a matriz falhar; tudo revertido depois):
| Mutação | Resultado |
|---|---|
| `pedidos_visiveis` devolve `qs` **sem** filtrar o dono (o IDOR clássico) | **7 falhas**: ver e cancelar para `outro`, `estoquista`, `gerente`, e a lista de outro cliente |
| `PagarPedidoView` busca `Order.objects.all()` | **4 falhas** (`pagar` para outro, estoquista, gerente e atendimento) |
| `cancel` sem `IsOwner` | **1 falha**: só o **atendimento**, o único ator que *enxerga* o pedido sem ser o dono |
O terceiro caso é o mais didático: **sem o ator “atendimento” a matriz não pegaria a remoção do `IsOwner`**, porque quem não é dono já levava `404` do filtro da consulta. Escolher bem os atores é parte do teste. Depois de restaurar: `39 passed`.

**5. Suíte e contrato**
```text
218 passed, 1 skipped          (o pulado é o teste de concorrência, que só roda em PostgreSQL)
Contracts: 3 kept, 0 broken.   (lint-imports)
spectacular --validate --fail-on-warn: sem avisos
```
O comportamento de erro é novo só para um caso (409 ao apagar produto em uso), que **antes era um `500`**.

**6. Mass assignment: a mesma ideia nos campos.** O serializador de produto declara `read_only_fields = ["slug", "created_at"]` e o de usuário (`/auth/me/`) é **somente leitura** (a auditoria da aula 01 tentou promover `role` e recebeu `405`). A regra: o cliente só envia o que **você** declara como gravável; `status`, `total`, `owner` e `is_staff` são decididos pelo servidor.

## 🧠 Pausa para lógica
**Problema.** Uma nova rota `GET /api/v1/invoices/{id}/pdf/` gera a nota fiscal. O desenvolvedor reutilizou o `get_object_or_404(Invoice, pk=pk)` e exigiu apenas `IsAuthenticated`. (a) Qual é a falha? (b) Que linhas da matriz você acrescentaria? (c) Que código devolver para a nota de outro cliente?

<details><summary>Dica</summary>Quem tem uma conta válida pode pedir qualquer nota? E o que a resposta revela sobre a existência de notas alheias?</details>

<details><summary>Solução comentada</summary>

(a) **IDOR**: qualquer pessoa autenticada pode pedir a nota de qualquer outra mudando o `id`; a verificação é de *autenticação*, não de *propriedade*. (b) Uma nova coluna `ver_nota` com: anônimo `401`; dono `200`; outro cliente `404`; atendimento (se a política permitir) `200`; e a **mutação** (trocar a consulta por `Invoice.objects.all()`) para provar que o teste falha. (c) `404`: não confirma a existência da nota. Atenção ainda a efeitos laterais: arquivos gerados em pastas públicas com nomes previsíveis (`/media/notas/1.pdf`) **contornam** a rota; o PDF deve ser servido pela rota autorizada (ou por URL assinada e de curta duração).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| `Model.objects.get(pk=pk)` com `pk` da URL | Sem filtro por dono | Consulta base já restrita ao usuário |
| Só a rota de leitura protegida | Ações extras (`/pay/`, `/export/`) esquecidas | Matriz com **todas** as ações; teste de rotas |
| Usar `user_id` vindo do corpo/URL | Confiar no cliente | Usar `request.user` |
| `403` para recurso alheio | Revela que existe | `404` quando a existência é sensível |
| Campos como `is_staff`/`total` graváveis | *Mass assignment* | `read_only_fields`; serializers separados por ação |
| Só testar o “caminho feliz” | Falta de ator adversário | Testar **outro usuário** e papéis intermediários |
| Teste de autorização que nunca falhou | Não validado | **Mutação**: remover a proteção e ver o teste quebrar |
| Papel com mais permissões do que precisa | “Facilitar” | Menor privilégio; revisar os papéis periodicamente |
| Esconder IDs (UUID/aleatório) como única defesa | Segurança por obscuridade | Autorização real; ID não previsível é só camada extra |
| `500` em vez de erro claro (ex.: `ProtectedError`) | Exceção não tratada | Mapear para `409`/`422` com corpo padronizado |
| Arquivos privados em `/media/` público | Contorna a rota autorizada | Servir por rota autorizada ou URL assinada |

- **Negar por padrão:** novas rotas nascem fechadas (`IsAuthenticated` global) e você *abre* conscientemente.
- **Centralize a regra de visibilidade** (selector) para que listas, detalhes e ações usem a mesma.
- **Registre** tentativas de acesso negadas (aula 06) para detectar varredura de IDs.

## 🧩 Exercícios
**1. Fixação.** (a) Diferencie permissão por papel e por objeto. (b) O que é IDOR/BOLA? (c) Quando usar `404` em vez de `403`? (d) O que a mutação 3 mostrou sobre a escolha dos atores do teste?

<details><summary>Solução</summary>

(a) Papel: *quem* pode executar um tipo de ação (criar produto); objeto: *sobre qual instância* (este pedido é meu?). (b) Acessar um objeto de outro usuário trocando o identificador porque o servidor só verifica a autenticação. (c) Quando confirmar a existência do recurso já é vazamento (objetos de outros usuários). (d) Que sem um ator que **enxerga** o objeto sem ser o dono (atendimento), a remoção da checagem por objeto passa despercebida: o filtro da consulta mascarava a ausência do `IsOwner`.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `tests/test_matriz_autorizacao.py` com **todos** os papéis e **todas** as ações sensíveis (pedido, pagamento, carrinho, catálogo)
- [ ] Pelo menos **três mutações** documentadas (o teste falha e depois volta a passar)
- [ ] `ConflictError` (409) para exclusões bloqueadas por chave estrangeira, com teste
- [ ] Revisão dos serializers: nenhum campo sensível gravável (`is_staff`, `status`, `total`)
- [ ] Seção “Controle de acesso” em `docs/seguranca.md` com a tabela da política e o `404` × `403` justificado
- [ ] Commit `test(security): authorization matrix and 409 on protected delete`

**3. Desafio (opcional).** Gere a matriz **automaticamente**: percorra as rotas da API (`get_resolver()`), e falhe o teste se uma rota nova não tiver uma linha na política.

## 🎤 Na entrevista
- **O que é IDOR?** Quando o servidor entrega ou altera um objeto identificado pelo cliente sem verificar que ele pertence a quem pediu; também chamado BOLA em APIs. Corrige-se restringindo a consulta ao dono e testando com um segundo usuário.
- **`401`, `403` ou `404`?** `401` não autenticado, `403` autenticado sem permissão (recurso existe), `404` quando não devemos confirmar que o recurso existe, como o objeto de outro usuário.
- **Como testar autorização?** Matriz papel × ação × dono com atores adversários, e validação por mutação (remover a proteção e ver o teste falhar).
- **O que é *mass assignment*?** O cliente grava campos que só o servidor devia controlar (`is_staff`, `total`); evita-se com serializadores que listam explicitamente os campos graváveis.
- **O que é menor privilégio?** Cada papel recebe só o que precisa; o gerente de catálogo não precisa ler pedidos de clientes.
- **UUID no lugar de ID sequencial resolve IDOR?** Não. Dificulta adivinhar, mas quem obtiver o UUID (log, e-mail, histórico) continua podendo usá-lo; a autorização por objeto é obrigatória.

## 📚 Para ir além
- 📄 Referência: [OWASP Top 10:2025 — A01 Broken Access Control](https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/). Descrição, exemplos e prevenção (em inglês).
- 📄 Guia: [OWASP — IDOR Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html). Estratégias e testes (em inglês).
- 📄 Guia: [OWASP — Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html). Menor privilégio e negar por padrão (em inglês).
- 📄 Guia: [OWASP — Mass Assignment Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html). Como evitar (em inglês).
- 📄 Documentação oficial: [DRF — Permissões](https://www.django-rest-framework.org/api-guide/permissions/). Permissões por papel e por objeto.
- 📄 Referência: [MDN — `409 Conflict`](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Reference/Status/409). Quando usar.
- 📑 Verbete: [CWE-639 — Autorização contornada por chave controlada pelo usuário](https://cwe.mitre.org/data/definitions/639.html). O IDOR no catálogo de fraquezas (em inglês).

## ✅ Checklist da aula
- [ ] Sei explicar IDOR/BOLA e a diferença entre autorização por papel e por objeto
- [ ] Tenho a política de acesso escrita como tabela (papel × ação)
- [ ] Os testes cobrem atores adversários (outro usuário, papel intermediário)
- [ ] Validei a matriz por mutação e restaurei o código
- [ ] Erros previsíveis viram `4xx` padronizado, nunca `500`
