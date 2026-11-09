# 7. HTTPS, menor privilégio e LGPD básica

> ⏱️ ~1h30 · Módulo 9 · Pré-requisitos: [9.06](06-segredos-dependencias-headers-rate-limit.md), [8.06 (twelve-factor)](../08-arquitetura/06-twelve-factor.md), [3 (bancos relacionais)](../03-banco-de-dados/README.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19, Gunicorn 26.2, OpenSSL 3.5.5, PostgreSQL 18.6 num contêiner **meu**, removido depois). **As saídas são reais.** A CA e o certificado do exemplo são **de laboratório** (válidos por 2 dias, gerados com `openssl`). Os artigos da LGPD foram conferidos no texto da Lei nº 13.709/2018 publicado pelo Planalto. 
>
> ⚖️ **Esta aula não é aconselhamento jurídico.** Ela dá a base técnica para conversar com quem cuida da conformidade na empresa. Decisões jurídicas (base legal, prazos, comunicação de incidentes) são da empresa, com apoio do jurídico e do encarregado de dados.

## 🎯 Objetivos
- Explicar o que o **TLS** garante (confidencialidade, integridade, autenticidade do servidor) e o que **não** garante
- Montar HTTPS num ambiente local, **verificar** o certificado e as **versões de TLS** aceitas
- Entender a **terminação de TLS no proxy** e o risco do cabeçalho `X-Forwarded-Proto`
- Aplicar o **princípio do menor privilégio** no banco (papéis de dono, aplicação e leitura) e demonstrá-lo
- Reconhecer **dado pessoal**, **princípios** e **direitos do titular** da LGPD e transformá-los em funcionalidades (exportar e anonimizar)

## 🤔 Por que isso importa
Três perguntas de qualquer revisão de segurança: *“o tráfego viaja protegido?”*, *“se esta credencial vazar, o que o atacante consegue fazer?”* e *“que dados de pessoas guardamos, por quê e por quanto tempo?”*. As duas primeiras são técnicas; a terceira é técnica **e** legal: no Brasil, a LGPD obriga empresas de todos os tamanhos. Um dev júnior que sabe **implementar** os direitos do titular (exportar, corrigir, anonimizar) e **limitar o estrago** de um vazamento é muito valorizado.

## 💡 Intuição (explicação simples)
- **HTTPS** é mandar a carta num **malote lacrado e entregue em mãos**: ninguém no caminho lê (confidencialidade), ninguém altera sem romper o lacre (integridade) e o carteiro confere o **documento do destinatário** (certificado). Sem HTTPS, é um cartão-postal: todo mundo na rota lê.
- **Menor privilégio** é dar a cada funcionário **a chave só das salas de que precisa**. O caixa não tem a chave do cofre; a chave-mestra (dono do banco) fica guardada e só sai para obras (migrações). Se o caixa perder a chave, o prejuízo é limitado.
- **LGPD** é a lei que trata os dados das pessoas como **bens delas, emprestados à empresa** para um fim específico: coletar o mínimo, usar para aquilo que foi dito, proteger, e devolver, corrigir ou apagar quando a pessoa pedir (e a lei permitir).

## 🔬 Como funciona por dentro
### HTTPS e TLS
- **O que o TLS entrega:** (1) **confidencialidade** (cifra o conteúdo), (2) **integridade** (detecta alteração), (3) **autenticidade do servidor** (certificado assinado por uma autoridade em que o cliente confia). **Não** protege contra: um servidor malicioso com certificado válido, um XSS no seu site, um vazamento no banco, nem esconde **quem** você acessa (o nome do servidor e o IP aparecem).
- **Certificado:** liga um **nome** (campo *SAN*, `subjectAltName`) a uma **chave pública**, assinado por uma **CA**. O cliente verifica a **cadeia** até uma CA que ele já confia, a **validade** e se o **nome bate** com o do site. Em produção, usa-se uma CA pública (por exemplo, a Let's Encrypt, que emite e renova de graça via protocolo ACME); no laboratório criamos uma CA própria.
- **Versões:** TLS 1.0 e 1.1 estão obsoletos; o mínimo hoje é **TLS 1.2**, preferindo o **1.3**.
- **Terminação no proxy:** em geral o **Nginx/balanceador** (ou o provedor de nuvem) fala TLS com o navegador e encaminha HTTP ao Django na rede interna. O Django precisa saber que a requisição original era segura: o proxy envia `X-Forwarded-Proto: https` e o Django é configurado com `SECURE_PROXY_SSL_HEADER` para **confiar** nele. **Só é seguro se o proxy sobrescreve o cabeçalho** e o Django **não** está acessível diretamente de fora; senão o cliente forja o cabeçalho.
- **Camadas do Django para HTTPS:** `SECURE_SSL_REDIRECT` (redireciona HTTP para HTTPS), cookies `Secure` (aula 03), HSTS (aula 06).

### Menor privilégio
- **Princípio:** cada pessoa, processo e credencial recebe **apenas** o acesso necessário, **pelo tempo** necessário. Reduz o impacto de erros, de contas vazadas e de injeções (aula 02).
- **No banco:** separe pelo menos três papéis: **dono** (cria/altera estrutura; usado só nas migrações), **aplicação** (lê e grava dados; **não** altera nem apaga tabelas) e **leitura** (relatórios). Em PostgreSQL: `GRANT`/`REVOKE` e `ALTER DEFAULT PRIVILEGES` (para as tabelas futuras já nascerem com os privilégios certos).
- **Em outras camadas:** permissões por papel na aplicação (aula 05), usuário **não-root** no contêiner (módulo 11), políticas de IAM mínimas na nuvem (módulo 13), tokens com escopo e validade curtos.

### LGPD (Lei nº 13.709/2018)
- **Definições (art. 5º):** **dado pessoal** é a “informação relacionada a pessoa natural identificada ou identificável”; **titular** é a pessoa a quem os dados se referem; **controlador** decide sobre o tratamento; **operador** trata em nome do controlador. **Dado pessoal sensível** (origem racial, convicção religiosa, saúde etc.) tem proteção reforçada.
- **Princípios (art. 6º):** finalidade, adequação, **necessidade** (o mínimo), livre acesso, qualidade dos dados, transparência, **segurança**, prevenção, não discriminação e responsabilização e prestação de contas.
- **Bases legais (art. 7º):** o tratamento só é permitido se houver uma base, como **consentimento**, **cumprimento de obrigação legal**, **execução de contrato**, exercício regular de direitos e **legítimo interesse**, entre outras. **Consentimento não é a única base** (e nem sempre a melhor): para processar um pedido de compra, a base é a execução do contrato; para guardar a nota fiscal, a obrigação legal.
- **Direitos do titular (art. 18):** confirmação de que há tratamento, **acesso**, **correção**, **anonimização, bloqueio ou eliminação** de dados desnecessários ou excessivos, **portabilidade**, eliminação dos dados tratados com consentimento (salvo as exceções legais de guarda), informação sobre com quem se compartilhou, e revogação do consentimento.
- **Segurança (art. 46)** e **incidentes (art. 48):** os agentes de tratamento devem adotar medidas de segurança técnicas e administrativas para proteger os dados; o controlador deve **comunicar à ANPD (a autoridade nacional) e ao titular** um incidente que possa acarretar risco ou dano relevante, em prazo definido pela autoridade. É por isso que **logs, detecção e plano de resposta** (aula 06) importam.
- **Como isso vira código:** (1) **inventariar** os dados pessoais e a finalidade de cada um; (2) **coletar o mínimo**; (3) **definir retenção**; (4) **proteger** (tudo o que viu neste módulo); (5) **implementar os direitos** (exportar, corrigir, anonimizar); (6) **não colocar dados pessoais onde não precisam estar** (logs, URLs, mensagens de erro, ambientes de teste com dados reais).
- **Anonimizar não é só trocar o nome:** dado verdadeiramente anonimizado não permite identificar a pessoa por meios razoáveis. Remover o nome e manter e-mail, CPF ou combinações únicas é, no máximo, **pseudonimização** (ainda é dado pessoal).

## 🛠️ Exemplo prático
### Parte A: HTTPS de verdade, em 127.0.0.1
**1. A CA e o certificado do laboratório** (`openssl`; válidos por 2 dias, com `subjectAltName` para `localhost` e `127.0.0.1`):
```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.pem -days 2 -subj "/CN=MiniShop Lab CA"
openssl req -newkey rsa:2048 -nodes -keyout srv.key -out srv.csr -subj "/CN=localhost"
openssl x509 -req -in srv.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out srv.pem -days 2 -extfile ext.cnf   # ext.cnf: SAN, serverAuth
```
```text
subject=CN=localhost   issuer=CN=MiniShop Lab CA   notAfter=Nov 10 22:47:43 2026 GMT
X509v3 Subject Alternative Name: DNS:localhost, IP Address:127.0.0.1
```
**2. O Gunicorn com TLS e o que um cliente enxerga** (`https_demo.sh`; produção simulada: `DEBUG=0`):
```bash
uv run gunicorn config.wsgi -b 127.0.0.1:8164 --certfile srv.pem --keyfile srv.key
```
```text
== 1) Cliente SEM confiar na CA do laboratório (verificação normal do certificado):
   código de saída do curl: 60 (60 = certificado não verificável)
   curl: (60) SSL certificate OpenSSL verify result: unable to get local issuer certificate (20)
== 2) Cliente que confia na CA (--cacert), com o nome certo (localhost):
HTTP/1.1 200 OK
Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'
Strict-Transport-Security: max-age=3600
== 3) Nome errado: o certificado só vale para localhost e 127.0.0.1 (peço o nome outro.exemplo apontando para o mesmo servidor):
curl: (60) SSL: no alternative certificate subject name matches target hostname 'outro.exemplo'
== 4) Versões do TLS (cliente com nível de segurança rebaixado SÓ para este teste):
   TLS 1.0: recusado pelo servidor ([SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert protocol version (_ssl)
   TLS 1.1: recusado pelo servidor ([SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert protocol version (_ssl)
   TLS 1.2: ACEITO pelo servidor (TLSv1.2, ECDHE-RSA-AES256-GCM-SHA384)
   TLS 1.3: ACEITO pelo servidor (TLSv1.3, TLS_AES_256_GCM_SHA384)
== 5) HTTP puro com SECURE_SSL_REDIRECT=1 (porta 8165):
HTTP/1.1 301 Moved Permanently
Location: https://127.0.0.1:8165/api/v1/categories/
== 6) O mesmo servidor exposto DIRETO, com um cabeçalho X-Forwarded-Proto forjado pelo cliente:
HTTP/1.1 200 OK
```
Como ler cada bloco:
1. **Cliente sem confiar na CA:** o `curl` **recusou** (código `60`, “unable to get local issuer certificate”). É a verificação funcionando: um certificado de uma CA desconhecida **não** é aceito. *(A tentação de resolver com a opção que desliga a verificação é exatamente o erro que anula o HTTPS: o certo é dar ao cliente a CA em que ele deve confiar, como no bloco 2.)*
2. **Cliente que confia na CA** (`--cacert ca.pem`): `200 OK`, com `Strict-Transport-Security` e a CSP da aula 06.
3. **Nome errado:** o certificado só vale para `localhost` e `127.0.0.1`; pedir `outro.exemplo` (mesmo servidor) foi recusado: “no alternative certificate subject name matches target hostname”. O cliente confere o **nome**, não só a assinatura.
4. **Versões de TLS:** o servidor **recusou TLS 1.0 e 1.1** (`tlsv1 alert protocol version`) e **aceitou 1.2 e 1.3** (`TLS_AES_256_GCM_SHA384` no 1.3). > 🔎 *Detalhe de método:* a minha primeira tentativa usou `openssl s_client -tls1_1` e “falhou com `no protocols available`”, mas isso era o **cliente** OpenSSL 3.5 que nem oferece TLS 1.1, **não** uma prova de que o servidor recusa. Refiz com um cliente Python que rebaixa o nível de segurança **só neste teste** (`tls_versoes.py`) para realmente tentar as versões velhas: aí a recusa veio **do servidor**.
5. **HTTP puro com `SECURE_SSL_REDIRECT`:** `301` para `https://…`.
6. **O risco do cabeçalho forjado:** o mesmo servidor, exposto diretamente, recebeu `X-Forwarded-Proto: https` **escrito pelo cliente** e respondeu `200` (aceitou como se fosse seguro, sem redirecionar). Isso mostra por que a configuração correta tem três partes: (a) o Django confia no cabeçalho **só** se existir um proxy à frente; (b) o proxy **sobrescreve** o `X-Forwarded-Proto` (no Nginx: `proxy_set_header X-Forwarded-Proto $scheme;`); (c) o Gunicorn escuta apenas em `127.0.0.1` ou numa rede privada, **inacessível de fora**.

**3. Em produção:** TLS no Nginx ou no balanceador (Let's Encrypt, ou o gerenciador de certificados da nuvem), renovação automática, `SECURE_SSL_REDIRECT`, cookies `Secure`, HSTS crescente (aula 06). A configuração do servidor (cifras e versões) pode ser gerada e conferida com ferramentas (links abaixo).

### Parte B: menor privilégio no banco
**4. Três papéis** (`roles.sql`; as senhas são de laboratório):
```sql
-- Três papéis, três poderes. A aplicação NÃO é dona das tabelas: não pode apagá-las nem alterá-las.
CREATE ROLE minishop_owner LOGIN PASSWORD 'owner-lab-apenas' ;
CREATE ROLE minishop_app   LOGIN PASSWORD 'app-lab-apenas'   NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE minishop_ro    LOGIN PASSWORD 'ro-lab-apenas'    NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE DATABASE minishop_m9 OWNER minishop_owner;
\c minishop_m9
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT  ALL ON SCHEMA public TO minishop_owner;
GRANT  USAGE ON SCHEMA public TO minishop_app, minishop_ro;
-- tabelas FUTURAS (criadas pelo dono nas migrações) já nascem com os privilégios certos:
ALTER DEFAULT PRIVILEGES FOR ROLE minishop_owner IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO minishop_app;
ALTER DEFAULT PRIVILEGES FOR ROLE minishop_owner IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO minishop_app;
ALTER DEFAULT PRIVILEGES FOR ROLE minishop_owner IN SCHEMA public GRANT SELECT ON TABLES TO minishop_ro;
```
O `ALTER DEFAULT PRIVILEGES` é o detalhe que evita o esquecimento: as tabelas que as **migrações** criarem depois já nascem com `SELECT/INSERT/UPDATE/DELETE` para a aplicação e só `SELECT` para o papel de leitura.

**5. O que cada papel consegue** (`privilegios.py`; conexões reais ao PostgreSQL 18):
```text
papel         operação                           resultado
minishop_app  ler produtos                       permitido (retornou 64)
minishop_app  atualizar um produto               permitido
minishop_app  inserir categoria                  permitido
minishop_app  apagar a categoria de teste        permitido
minishop_app  ALTERAR a estrutura da tabela      NEGADO  → must be owner of table catalog_product
minishop_app  APAGAR a tabela de produtos        NEGADO  → must be owner of table catalog_product
minishop_app  ESVAZIAR a tabela de produtos      NEGADO  → permission denied for table catalog_product
minishop_app  CRIAR uma tabela nova              NEGADO  → permission denied for schema public
minishop_app  criar um papel                     NEGADO  → permission denied to create role

minishop_ro   ler produtos                       permitido (retornou 64)
minishop_ro   atualizar um produto               NEGADO  → permission denied for table catalog_product
minishop_ro   inserir categoria                  NEGADO  → permission denied for table catalog_category
minishop_ro   apagar a categoria de teste        NEGADO  → permission denied for table catalog_category
minishop_ro   ALTERAR a estrutura da tabela      NEGADO  → must be owner of table catalog_product
minishop_ro   APAGAR a tabela de produtos        NEGADO  → must be owner of table catalog_product
minishop_ro   ESVAZIAR a tabela de produtos      NEGADO  → permission denied for table catalog_product
minishop_ro   CRIAR uma tabela nova              NEGADO  → permission denied for schema public
minishop_ro   criar um papel                     NEGADO  → permission denied to create role
```
- **A aplicação** lê, atualiza, insere e apaga **dados**, mas **não** altera a estrutura, não apaga nem esvazia tabelas, não cria tabelas e não cria papéis: uma injeção de SQL (aula 02) ou uma conta vazada **não consegue destruir o esquema**. Conferi depois, como dono: a tabela continuava lá, com os 64 produtos.
- **O papel de leitura** só consegue `SELECT`.
- **As migrações** rodam com o papel **dono** (`DATABASE_URL` diferente na etapa de *deploy*); a aplicação em execução usa o papel `minishop_app`. Observação honesta: rodei o `migrate` como aplicação e ele terminou com “No migrations to apply” (nada pendente, só leu a tabela de controle); **não** testei uma migração pendente, que deveria falhar por falta de privilégio. Outro limite: a suíte de testes cria um banco de teste, então precisa de um papel com `CREATEDB` (não é o da aplicação).

### Parte C: LGPD no código
**6. Inventário de dados pessoais do MiniShop** (o primeiro artefato de qualquer programa de conformidade):
| Dado | Onde | Finalidade | Base legal (a confirmar com o jurídico) | Retenção |
|---|---|---|---|---|
| Nome de usuário, e-mail, nome | `accounts_user` | identificar a conta e enviar a confirmação | execução de contrato | enquanto a conta existir; anonimizar ao pedido |
| Hash da senha | `accounts_user.password` | autenticar | execução de contrato / segurança | idem; **nunca** exportar |
| Pedidos, itens, pagamentos | `orders_*`, `payments_*` | vender e emitir documento fiscal | **obrigação legal** e contrato | prazos legais de guarda (definidos pelo jurídico) |
| Carrinho | `cart_*` | compra em andamento | execução de contrato | apagar ao anonimizar |
| IP e nome de usuário em logs de segurança (aula 06) | logs | detectar abusos | legítimo interesse / segurança | curta (ex.: dias a meses), com acesso restrito |
| Tokens JWT | `token_blacklist_*` | sessão | execução de contrato | até expirar |
Note: o **IP nos logs de segurança que criamos na aula 06 é dado pessoal**. Cada controle de segurança que registra dados cria um novo dado a proteger e a expirar.

**7. Direito de acesso e portabilidade** (`apps/accounts/lgpd.py` + `manage.py exportar_dados_titular`): devolve os dados da pessoa em JSON estruturado, **sem** o hash da senha nem tokens. **8. Eliminação/anonimização** (`manage.py anonimizar_titular`). A decisão de projeto: **não apagamos** quem tem pedidos (a chave estrangeira é `PROTECT`, e a venda é registro que a lei manda guardar), então **anonimizamos** a conta e **mantemos** os pedidos.
```python
"""Direitos do titular (LGPD, art. 18): acesso/portabilidade e anonimização. Regras de negócio, sem HTTP.

Decisão de projeto: NÃO apagamos o usuário que tem pedidos. O pedido é registro de uma venda, que precisa ser mantido por
obrigação legal/fiscal (LGPD, art. 7º, II). Em vez disso, ANONIMIZAMOS os dados pessoais e deixamos o pedido intacto."""
import logging

from django.db import transaction
from django.utils import timezone

seguranca = logging.getLogger("security")


def exportar_dados(user):
    """Tudo que guardamos SOBRE a pessoa, em formato estruturado (JSON). Nunca inclui o hash da senha nem tokens."""
    pedidos = []
    for o in user.orders.prefetch_related("items__product").select_related("payment"):
        pagamento = getattr(o, "payment", None)
        pedidos.append({
            "id": o.pk, "status": o.status, "total": str(o.total), "criado_em": o.created_at.isoformat(),
            "itens": [{"sku": i.product.sku, "produto": i.product.name, "quantidade": i.quantity, "preco_unitario": str(i.unit_price)} for i in o.items.all()],
            "pagamento": {"status": pagamento.status, "valor": str(pagamento.amount)} if pagamento else None,
        })
    carrinho = getattr(user, "cart", None)
    return {
        "gerado_em": timezone.now().isoformat(),
        "conta": {"usuario": user.username, "email": user.email, "nome": user.get_full_name(), "cadastrado_em": user.date_joined.isoformat(),
                  "ultimo_acesso": user.last_login.isoformat() if user.last_login else None},
        "pedidos": pedidos,
        "carrinho": [{"sku": i.product.sku, "quantidade": i.quantity} for i in carrinho.items.select_related("product")] if carrinho else [],
    }


@transaction.atomic
def anonimizar(user):
    """Remove os dados pessoais e desativa a conta, mantendo os pedidos (obrigação legal). Idempotente."""
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
    if user.username.startswith("anonimo-"):
        return False
    user.username = f"anonimo-{user.pk}"
    user.email = ""
    user.first_name = user.last_name = ""
    user.is_active = False
    user.set_unusable_password()
    user.save()
    if hasattr(user, "cart"):
        user.cart.delete()                                          # carrinho não é registro fiscal
    for token in OutstandingToken.objects.filter(user=user):        # derruba as sessões abertas
        BlacklistedToken.objects.get_or_create(token=token)
    seguranca.info("titular_anonimizado user_id=%s", user.pk)
    return True
```
Execução real no laboratório (a pessoa de teste tinha um pedido e um item no carrinho):
```text
$ manage.py exportar_dados_titular cliente
{
  "gerado_em": "2026-11-08T22:49:59.898120+00:00",
  "conta": {
    "usuario": "cliente",
    "email": "cliente@minishop.local",
    "nome": "Maria Souza",
    "cadastrado_em": "2026-11-08T22:49:59.058204+00:00",
    "ultimo_acesso": null
  },
  "pedidos": [
    {
      "id": 1,
      "status": "pending",
      "total": "1402.40",
      "criado_em": "2026-11-08T22:49:59.466788+00:00",
      "itens": [
        {
          "sku": "CAS-049",
          "produto": "Cadeira Básico",
          "quantidade": 2,
          "preco_unitario": "701.20"
        }
      ],
      "pagamento": null
    }
  ],
  "carrinho": [
    {
      "sku": "CAS-049",
      "quantidade": 1
    }
  ]
}
$ manage.py anonimizar_titular cliente
(log de segurança) titular_anonimizado user_id=3
anonimizado
$ (conferência no banco depois)
{'username': 'anonimo-3', 'email': '', 'nome': '', 'ativo': False, 'senha_utilizavel': False, 'pedidos_mantidos': 1}
```
Antes: nome, e-mail, pedido, item no carrinho. Depois: `username` vira `anonimo-3`, e-mail e nome vazios, conta **inativa**, **sem senha utilizável**, o carrinho **apagado**, os *refresh tokens* **revogados** e o **pedido mantido** (`pedidos_mantidos: 1`). A rotina é **idempotente** (rodar de novo diz “já estava anonimizado”) e registra o evento `titular_anonimizado` no log de segurança (só o ID, sem dados pessoais).

**9. Testes** (`tests/test_lgpd.py`, 6 testes): a exportação traz conta, pedidos e carrinho e **não** contém hash de senha; o comando imprime JSON válido; a anonimização limpa os dados e **mantém** o pedido; é idempotente; depois dela o **login e o refresh deixam de funcionar**; e o e-mail liberado pode ser reutilizado por outra conta.

**10. Fechando o módulo: estado do laboratório**
```text
SQLite:      235 passed, 1 skipped
PostgreSQL:  232 passed, 4 skipped          (os pulados são os do legado, só SQLite)
lint-imports: 3 contratos cumpridos · ruff S e bandit: sem achados · spectacular --validate --fail-on-warn: limpo
```
> 🛠️ **Um erro meu, achado pelo PostgreSQL.** Ao criar o papel “Atendimento” num teste, a suíte quebrou no PostgreSQL com `duplicate key value violates unique constraint "auth_group_pkey"`. A causa estava no `conftest.py` que escrevi na aula 8.06: eu zerava as sequências com `sequence_reset_by_name_sql`, que as põe em 1 **inclusive nas tabelas que já têm linhas vindas das migrações** (grupos, permissões). O correto é `sequence_reset_sql`, que parte do maior id existente. Corrigi aqui e na aula 8.06 (que ganhou uma nota de correção) e na referência do módulo 8. O mesmo teste revelou duas diferenças de SQL cru entre os bancos (`is_active = 1` → `TRUE`; `LIKE` com maiúsculas → `LOWER()` dos dois lados).

## 🧠 Pausa para lógica
**Problema.** O marketing pede: “exporte todos os e-mails dos clientes, inclusive dos que pediram para ser esquecidos, para uma campanha”. (a) O que a LGPD sugere sobre isso? (b) Como o código deve **impedir** o erro, em vez de depender de memória? (c) E se o cliente anonimizado reaparece com o mesmo e-mail?

<details><summary>Dica</summary>Pense em finalidade, base legal, e em como uma consulta pode excluir quem pediu eliminação.</details>

<details><summary>Solução comentada</summary>

(a) Quem pediu a eliminação/anonimização **não pode** ser alvo de nova finalidade (marketing) sem base legal; o princípio da **finalidade** e o direito do titular se aplicam. (b) Torne a regra **parte da consulta**: uma função única (`clientes_para_campanha()`) que filtra `is_active=True` e quem não revogou o consentimento de marketing (um campo `aceita_marketing`, que **é** a base legal dessa finalidade), coberta por teste; ninguém escreve `User.objects.all()` para campanhas. (c) O e-mail anonimizado foi **apagado** da conta antiga (`email=""`); se a pessoa voltar com o mesmo e-mail, é um **novo cadastro** com nova base legal, sem herdar o histórico (o que é correto), e a unicidade de e-mail da aplicação continua valendo (há teste para o reuso).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| Desligar a verificação do certificado “para funcionar” | Atalho em desenvolvimento | Dar a CA ao cliente (`--cacert`) ou usar uma CA local confiável |
| HTTPS só no login | “Só o formulário precisa” | HTTPS em **todo** o site; HSTS |
| Certificado expirado em produção | Renovação manual | Automatizar (ACME) e alertar antes de vencer |
| `X-Forwarded-Proto` confiado sem proxy | Servidor da aplicação exposto | Proxy sobrescreve o cabeçalho; Gunicorn só na rede interna |
| TLS 1.0/1.1 habilitado | Compatibilidade antiga | Mínimo TLS 1.2; preferir 1.3; conferir com ferramenta |
| A aplicação conecta ao banco como superusuário ou dono | “Funciona e pronto” | Papéis separados: dono (migrações), aplicação (DML), leitura (relatórios) |
| Privilégios só nas tabelas existentes | Esquecer as futuras | `ALTER DEFAULT PRIVILEGES` |
| Mesma credencial em todos os ambientes | Reuso | Credenciais por ambiente e por função, rotacionáveis |
| Dados reais em ambiente de teste/dev | Cópia do banco de produção | Dados sintéticos ou anonimizados |
| IP/e-mail/CPF em logs, URLs e mensagens de erro | Registrar “tudo” | Registrar identificadores e eventos, não dados pessoais; retenção curta |
| Excluir o usuário e quebrar pedidos (ou, ao contrário, nunca poder apagar nada) | Sem política de retenção | Anonimizar mantendo o registro legal; definir prazos com o jurídico |
| “Anonimizamos”, mas ficou o e-mail e o CPF | Pseudonimização confundida com anonimização | Remover tudo que identifica, ou tratar como dado pessoal |
| Consentimento como base para tudo | Confusão sobre bases legais | Escolher a base certa para cada finalidade, com o jurídico |
| Vazamento sem plano de resposta | Ninguém sabe o que fazer | Plano: conter, avaliar o risco, comunicar ANPD e titulares conforme a lei |

- **Privacidade desde o desenho:** pense nos dados que vai guardar **antes** de criar a tabela.
- **Registre as decisões** (ADR) sobre retenção e base legal.
- **Menos dado, menos risco:** o dado que você não coleta não vaza.

## 🧩 Exercícios
**1. Fixação.** (a) O que o TLS não protege? (b) Por que um certificado precisa de `subjectAltName`? (c) Por que a aplicação não deve conectar ao banco com o papel dono? (d) Cite três direitos do titular (art. 18) e como o MiniShop atende dois deles.

<details><summary>Solução</summary>

(a) Contra um servidor malicioso com certificado válido, XSS no site, vazamento no banco, nem esconde com quem você conversa (nome/IP). (b) O cliente confere o **nome** do site contra os nomes do certificado (SAN); sem bater, recusa. (c) Uma injeção de SQL ou credencial vazada poderia alterar/apagar a estrutura; com papel só de dados, o dano fica limitado. (d) Ex.: acesso/portabilidade (`exportar_dados_titular`), anonimização/eliminação (`anonimizar_titular`), correção (edição do cadastro), confirmação de tratamento (inventário e política de privacidade).
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] HTTPS local verificado (CA de laboratório, SAN correto) com a saída anexada e as versões de TLS testadas
- [ ] Documentar a topologia: TLS no proxy, `X-Forwarded-Proto` sobrescrito, Gunicorn só na rede interna
- [ ] Três papéis no PostgreSQL com `ALTER DEFAULT PRIVILEGES` e o relatório de privilégios (permitido × negado)
- [ ] `DATABASE_URL` de migração (dono) separada da de execução (aplicação) no processo de *deploy*
- [ ] Inventário de dados pessoais (tabela acima) em `docs/privacidade.md`, com finalidade, base legal (a confirmar) e retenção
- [ ] `exportar_dados_titular` e `anonimizar_titular` com testes; idempotência e login bloqueado depois de anonimizar
- [ ] Política para logs de segurança: o que registra, por quanto tempo e quem acessa
- [ ] Fechar `docs/seguranca.md`: cada achado do OWASP com evidência antes/depois e as decisões conscientes restantes
- [ ] Commit `feat(privacy): data export and anonymization; docs: https and least privilege`

**3. Desafio (opcional).** Faça os dois comandos virarem **endpoints autenticados** (`GET /api/v1/auth/me/export/`, `POST /api/v1/auth/me/anonymize/`) que exigem a **senha atual** (reautenticação) antes de agir, registram o evento e têm testes de autorização na matriz da aula 05.

## 🎤 Na entrevista
- **O que é HTTPS e o que ele garante?** HTTP sobre TLS: confidencialidade, integridade e autenticidade do servidor (via certificado de uma CA confiável); não protege contra falhas na aplicação.
- **Onde termina o TLS e por que isso importa?** Em geral no proxy/balanceador; o Django precisa confiar no `X-Forwarded-Proto` só se o proxy o sobrescrever e a aplicação não estiver exposta diretamente.
- **O que é o princípio do menor privilégio? Exemplo.** Dar só o acesso necessário; no banco, a aplicação usa um papel que lê e grava dados mas não altera nem apaga tabelas, e as migrações rodam com outro papel.
- **O que é dado pessoal na LGPD?** Informação relacionada a pessoa natural identificada ou identificável (nome, e-mail, IP em alguns contextos); o sensível (saúde, religião etc.) tem proteção reforçada.
- **Cite direitos do titular.** Confirmação de tratamento, acesso, correção, anonimização/bloqueio/eliminação de dados desnecessários, portabilidade, informação sobre compartilhamento e revogação do consentimento.
- **Todo tratamento de dados precisa de consentimento?** Não; há outras bases legais (contrato, obrigação legal, legítimo interesse etc.), e o consentimento nem sempre é a mais adequada.
- **Como você trataria um vazamento de dados?** Conter, avaliar o que e quem foi afetado, corrigir a causa, e comunicar a ANPD e os titulares conforme a lei, com apoio do jurídico e do encarregado.

## 📚 Para ir além
- 📄 Lei: [Lei nº 13.709/2018 (LGPD)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm). O texto oficial (arts. 5º, 6º, 7º, 18, 46 e 48 usados nesta aula). *Nesta máquina o `curl` não completou a conexão com esse site; o conteúdo foi lido por outra ferramenta de busca de páginas, e o endereço é o oficial do Planalto.*
- 📄 Órgão: [ANPD — Autoridade Nacional de Proteção de Dados](https://www.gov.br/anpd/pt-br) e [Comunicação de incidente de segurança](https://www.gov.br/anpd/pt-br/assuntos/incidente-de-seguranca). Orientações e prazos vigentes.
- 📄 Guia: [OWASP — Transport Layer Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html). Versões, cifras e certificados (em inglês).
- 🧰 Ferramenta: [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/). Configurações de Nginx/Apache por perfil (em inglês).
- 🧰 Ferramenta: [Qualys SSL Labs — SSL Test](https://www.ssllabs.com/ssltest/). Avalia um servidor público (use só em sites seus).
- 📄 Documentação: [Let's Encrypt](https://letsencrypt.org/docs/). Certificados gratuitos e renovação automática (em inglês).
- 📄 Documentação oficial: [Django — Checklist de implantação (HTTPS)](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/#https) e [`SECURE_PROXY_SSL_HEADER`](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header).
- 📄 Documentação oficial: [PostgreSQL 18 — Privilégios](https://www.postgresql.org/docs/18/ddl-priv.html) e [`ALTER DEFAULT PRIVILEGES`](https://www.postgresql.org/docs/18/sql-alterdefaultprivileges.html) (em inglês).
- 📄 Guia: [OWASP — Database Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Database_Security_Cheat_Sheet.html). Contas, privilégios e rede (em inglês).

## ✅ Checklist da aula
- [ ] Sei o que o TLS garante e o que não garante, e verifiquei certificado, nome e versões
- [ ] Entendo a terminação de TLS no proxy e o risco do cabeçalho forjado
- [ ] A aplicação usa um papel de banco sem poder de alterar a estrutura
- [ ] Tenho um inventário de dados pessoais com finalidade, base e retenção
- [ ] Implementei exportar e anonimizar, com testes
- [ ] Fechei o relatório `docs/seguranca.md` com evidências
