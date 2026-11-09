# 4. Hash de senhas, autenticação e autorização

> ⏱️ ~1h30 · Módulo 9 · Pré-requisitos: [9.01](01-owasp-ameacas.md), [9.03](03-csrf-cors-sessao-jwt.md), [6.06 (JWT)](../06-apis-rest/06-autenticacao-token-jwt.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19, `argon2-cffi` e `bcrypt` instalados para a comparação). Os tempos são **deste computador, num núcleo**; mudam de máquina para máquina, mas a **proporção** é o que importa. **As saídas são reais.** O benchmark mede o **custo de verificar** um hash (o que o seu servidor paga em cada login); não há nenhuma ferramenta de quebra de senhas nesta aula.

## 🎯 Objetivos
- Explicar por que senhas são guardadas como **hash lento com salt** e por que `SHA-256` puro é a escolha errada
- Comparar **PBKDF2, bcrypt, scrypt e Argon2id** pelo custo medido e escolher (e justificar)
- Configurar o Django para **Argon2id** sem invalidar as senhas antigas (migração no login)
- Aplicar **validadores de senha** (comprimento, senhas comuns) e corrigir o achado A07 da aula 01
- Diferenciar **autenticação** de **autorização** e usar `401`, `403` e `404` com critério
- Verificar que o login **não revela** se um usuário existe (resposta e tempo)

## 🤔 Por que isso importa
Vazamentos de banco de dados acontecem com empresas de todos os tamanhos. O que separa um incidente administrável de um desastre é **como as senhas estavam guardadas**: texto puro ou hash rápido significam todas as contas comprometidas em horas (e, como as pessoas reaproveitam senhas, em outros sites também); um hash lento e salgado torna cada tentativa cara. E confundir autenticação com autorização é a origem do item nº 1 do OWASP (controle de acesso quebrado). Ambos são tema recorrente de entrevista.

## 💡 Intuição (explicação simples)
**Hash** é um **liquidificador de sentido único**: você coloca a senha, sai uma vitamina; não dá para “desfazer” a vitamina e recuperar as frutas. Para conferir uma senha, o sistema bate a tentativa no mesmo liquidificador e compara as vitaminas. Dois problemas: (1) se o liquidificador é **rápido demais**, alguém com a vitamina roubada testa milhões de combinações por segundo; a solução é um liquidificador **propositalmente lento e pesado**. (2) Duas pessoas com a mesma senha gerariam a mesma vitamina; a solução é jogar um **ingrediente aleatório único (o salt)** em cada uma.
**Autenticação** é a portaria conferindo **quem é você** (crachá e foto). **Autorização** é saber **em que andares você pode entrar**. Estar autenticado não significa estar autorizado.

## 🔬 Como funciona por dentro
- **O que guardar:** nunca a senha (nem criptografada, que é reversível): guarde o **resultado de uma função de derivação de chave** (*password hashing*), com **salt aleatório por usuário** e **parâmetros de custo** gravados junto. No login, repete-se o cálculo com o salt guardado e compara-se em tempo constante.
- **Por que hash comum (SHA-256, MD5) é errado:** foram feitos para serem **rápidos**. Quem rouba a tabela testa bilhões de palpites por segundo em GPUs. O salt evita tabelas pré-calculadas e hashes iguais para senhas iguais, mas **não deixa o hash mais lento**.
- **Funções adequadas** (todas com salt e custo configurável):
  | Algoritmo | Ideia do custo | Observações |
  |---|---|---|
  | **PBKDF2-HMAC-SHA256** | repetir o hash muitas vezes (iterações) | padrão do Django; aprovado em normas (FIPS); só gasta CPU, então GPUs o aceleram bem |
  | **bcrypt** | cifra Blowfish “cara” (fator de custo) | muito usado; limite de **72 bytes** na senha |
  | **scrypt** | exige **muita memória** | dificulta hardware especializado |
  | **Argon2id** | exige **memória + tempo + paralelismo** | vencedor do concurso de 2015; recomendação atual do OWASP; padronizado na RFC 9106 |
- **Escolha:** **Argon2id** quando possível; **PBKDF2** quando se exigir conformidade com norma; **bcrypt** em sistemas legados que já o usam. O mais importante é **não ser rápido**, ter **salt** e conseguir **subir o custo** com o tempo.
- **Migração sem dor:** o hash guardado inclui o algoritmo (`argon2$...`, `pbkdf2_sha256$...`). O Django usa o **primeiro** de `PASSWORD_HASHERS` para gravar e os demais só para **verificar**; no login bem-sucedido, se o hash for de um algoritmo antigo (ou de parâmetros antigos), ele é **regravado** no padrão atual, sem pedir nada ao usuário.
- **Política de senha moderna (NIST SP 800-63B):** priorizar **comprimento** (frases longas), recusar senhas **comuns/vazadas**, **não** exigir trocas periódicas nem regras de composição obrigatórias (“1 maiúscula, 1 símbolo”), e incentivar gerenciadores de senhas. Os validadores do Django cobrem comprimento mínimo, lista de senhas comuns, apenas números e semelhança com os dados do usuário.
- **Autenticação × autorização:** autenticar = provar identidade (`401 Unauthorized`, na prática “não autenticado”); autorizar = decidir se aquela identidade pode **aquela ação sobre aquele recurso** (`403 Forbidden`). Quando revelar a existência do recurso é um vazamento, responda `404` (aula 05).
- **Enumeração de usuários:** mensagens diferentes (“usuário não existe” × “senha errada”) ou **tempos** diferentes revelam quais contas existem. A resposta deve ser a mesma; e o servidor deve gastar o mesmo trabalho nos dois casos (o Django executa o hasher mesmo para usuários inexistentes).
- **Outras defesas de autenticação:** limite de tentativas por conta e por IP (já feito: `5/min`), **MFA**, bloqueio com cuidado (bloquear a conta vira ataque de negação de serviço contra a vítima), recuperação de senha com token de uso único e curto, e **registro** de eventos (aula 06).

## 🛠️ Exemplo prático
**1. Medindo o custo de um hash** (`hash_bench.py`)
```python
"""Quanto custa UM hash de senha? Lento de propósito = caro para quem tenta adivinhar. Mede neste computador."""
import hashlib
import os
import statistics
import sys
import time

import bcrypt
import django
from argon2 import PasswordHasher

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.environ["LAB"])
django.setup()
from django.contrib.auth.hashers import PBKDF2PasswordHasher, check_password, make_password  # noqa: E402

senha = "correto-cavalo-bateria-grampo"


def medir(f, n=5):
    tempos = []
    for _ in range(n):
        t = time.perf_counter()
        f()
        tempos.append(time.perf_counter() - t)
    return statistics.median(tempos)


salt = os.urandom(16)
alvos = [
    ("SHA-256 puro (ERRADO para senhas)", lambda: hashlib.sha256(senha.encode()).hexdigest(), 2000),
    ("SHA-256 com salt (ainda ERRADO)", lambda: hashlib.sha256(salt + senha.encode()).hexdigest(), 2000),
    (f"PBKDF2-SHA256, {PBKDF2PasswordHasher.iterations:,} iterações (padrão Django 5.2)", lambda: make_password(senha, hasher="pbkdf2_sha256"), 3),
    ("bcrypt, custo 12", lambda: bcrypt.hashpw(senha.encode(), bcrypt.gensalt(12)), 3),
    ("scrypt (n=2^15, r=8, p=1)", lambda: hashlib.scrypt(senha.encode(), salt=salt, n=2**15, r=8, p=1, maxmem=64 * 1024 * 1024), 3),
    ("Argon2id (padrões do argon2-cffi)", lambda: PasswordHasher().hash(senha), 3),
]
print(f"{'algoritmo':<62} {'tempo por hash':>16} {'tentativas/s (1 núcleo)':>26}")
base = None
for nome, f, n in alvos:
    t = medir(f, n)
    if "puro" in nome:
        base = t
    tempo = f"{t * 1000:,.3f} ms" if t >= 0.001 else f"{t * 1e6:,.1f} µs"
    print(f"{nome:<62} {tempo:>16} {1 / t:>26,.0f}")

print("\nFormato guardado no banco (mesma senha, duas vezes → hashes diferentes por causa do SALT):")
a, b = make_password(senha, hasher="pbkdf2_sha256"), make_password(senha, hasher="pbkdf2_sha256")
print("  ", a[:60] + "...")
print("  ", b[:60] + "...")
print("   mesma senha, mesmo hash?", a == b, "· check_password(certa) =", check_password(senha, a), "· check_password(errada) =", check_password("errada", a))
h = PasswordHasher().hash(senha)
print("   Argon2id:", h)
```
```text
algoritmo                                                        tempo por hash    tentativas/s (1 núcleo)
SHA-256 puro (ERRADO para senhas)                                        0.3 µs                  3,448,042
SHA-256 com salt (ainda ERRADO)                                          0.3 µs                  3,164,463
PBKDF2-SHA256, 1,000,000 iterações (padrão Django 5.2)               110.045 ms                          9
bcrypt, custo 12                                                     198.814 ms                          5
scrypt (n=2^15, r=8, p=1)                                             56.060 ms                         18
Argon2id (padrões do argon2-cffi)                                     55.569 ms                         18

Formato guardado no banco (mesma senha, duas vezes → hashes diferentes por causa do SALT):
   pbkdf2_sha256$1000000$8ZBwWvG6DwnfT9EXrgKRhC$uZvI4PRKHU2zelP...
   pbkdf2_sha256$1000000$iB492ZD8xDSTyx9oKqcaiA$NB4ex01+tfln/bp...
   mesma senha, mesmo hash? False · check_password(certa) = True · check_password(errada) = False
   Argon2id: $argon2id$v=19$m=65536,t=3,p=4$1PLOGUk60A3kjEXT8M/XbQ$LM6dHVMB2XC+WsRRN7JV6NOLiubiDCIHdSilL8cn+u0
```
Como ler:
- **SHA-256 puro: 0,3 µs** → ~3,4 **milhões** de tentativas/s em **um** núcleo, em Python; um atacante com GPU e software dedicado faz bilhões. Colocar salt **não muda o custo** (a linha 2 é igual à 1).
- **PBKDF2 (1 milhão de iterações, padrão do Django 5.2): ~110 ms** → **~9 tentativas/s** por núcleo. É por isso que o `check_password` é “lento” de propósito.
- **bcrypt (custo 12): ~200 ms**; **scrypt** e **Argon2id: ~55 ms** nos parâmetros testados. Os tempos só são comparáveis se o **objetivo de segurança** for equivalente; o ponto é que **todos custam ordens de grandeza mais** que o hash rápido, e **Argon2id e scrypt também consomem memória** (o que encarece o ataque em hardware especializado).
- **Salt:** a mesma senha, hasheada duas vezes, deu **hashes diferentes**; `check_password` aceita a certa e recusa a errada. O formato (`algoritmo$iterações$salt$hash`) guarda tudo que é preciso para verificar.
- **Calibragem:** o custo é um compromisso. Muito baixo, fraco; muito alto, o **seu** servidor sofre sob muitos logins (e vira alvo de negação de serviço). Pratica-se mirar algo como dezenas a poucas centenas de milissegundos por verificação e reavaliar a cada poucos anos.

**2. Configurando o Django para Argon2id** (`config/settings.py`; `uv add argon2-cffi`)
```python
# --- Senhas (aula 9.04) ---
# O PRIMEIRO hasher grava as senhas novas; os demais só VERIFICAM as antigas. No login, o Django regrava o hash no primeiro da lista.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
```
O `PBKDF2PasswordHasher` fica na lista para **continuar verificando** as senhas que já existem.

**3. Provando a migração e a política de senhas** (`tests/test_senhas.py`)
```python
def test_senhas_novas_usam_argon2id():
    h = make_password("uma-senha-bem-longa-123")
    assert h.startswith("argon2$argon2id$") and identify_hasher(h).algorithm == "argon2"


def test_mesma_senha_gera_hashes_diferentes_por_causa_do_salt():
    assert make_password("igual-igual-igual") != make_password("igual-igual-igual")


def test_senha_antiga_em_pbkdf2_ainda_e_aceita_e_regravada_em_argon2_no_login(django_user_model):
    u = django_user_model.objects.create(username="antigo")
    u.password = make_password("senha-antiga-segura-1", hasher="pbkdf2_sha256")
    u.save()
    assert u.password.startswith("pbkdf2_sha256$")
    r = Client().post("/api/v1/auth/token/", {"username": "antigo", "password": "senha-antiga-segura-1"}, content_type="application/json")
    assert r.status_code == 200
    u.refresh_from_db()
    assert u.password.startswith("argon2$argon2id$") and check_password("senha-antiga-segura-1", u.password)


@pytest.mark.parametrize("fraca", ["123", "12345678", "password", "senha123", "abc", "11111111111111"])
def test_senhas_fracas_sao_recusadas(fraca):
    with pytest.raises(ValidationError):
        validate_password(fraca)


def test_senha_parecida_com_o_usuario_e_recusada(django_user_model):
    u = django_user_model(username="mariaoliveira", email="maria@exemplo.com")
    with pytest.raises(ValidationError):
        validate_password("mariaoliveira2024", user=u)
```
```text
11 passed
```
Pontos-chave: (a) senhas novas saem como `argon2$argon2id$...` (o Django grava os parâmetros próprios: 100 MiB de memória, `t=2`, `p=8`); (b) um usuário **antigo em PBKDF2** consegue fazer login e, **no mesmo login**, o hash é regravado em Argon2id; (c) senhas como `123`, `password` e `senha123` são recusadas; uma **frase longa** é aceita; (d) uma senha parecida com o nome de usuário é recusada.

**4. Autenticação sem vazar quem existe** (`timing_login.py`: mediana de 15 tentativas com senha errada, limpando o contador de tentativas entre elas para não medir o `429`)
```text
usuário existente, senha errada : mediana    49.4 ms
usuário inexistente             : mediana    50.6 ms
diferença                       :     1.2 ms (2% do maior)
```
Usuário existente e inexistente: **~49 ms** e **~51 ms**, diferença de ~2% (dentro do ruído). O Django executa o hasher mesmo quando o usuário não existe, então o **tempo** não entrega a informação, e as **respostas** são idênticas (verificado na auditoria da aula 01).

**5. O achado A07 fechado.** Reexecutei a auditoria da aula 01:
```text
A04   OK          Algoritmo de hash de senhas → Argon2PasswordHasher (primeiro da lista PASSWORD_HASHERS; os demais só verificam senhas antigas)
A07   OK          Há validadores de senha? → AUTH_PASSWORD_VALIDATORS = [... MinimumLengthValidator (12), CommonPasswordValidator ...]
resumo: {"OK": 15, "FALHA": 2, "ATENÇÃO": 6, "NÃO MEDIDO": 1}
```
De 14 para 15 sondagens `OK` e de 3 para 2 `FALHA` (restam cabeçalhos e log de login falho, aula 06). Suíte do laboratório: **179 passed, 1 skipped**.

**6. Autenticação e autorização nos códigos de resposta do MiniShop** (todos observados na auditoria)
| Situação | Código | Por quê |
|---|---|---|
| Sem token em `/orders/` | `401` | não autenticado: “quem é você?” |
| Token válido, cliente cria produto | `403` | autenticado, **sem permissão** para a ação |
| Token válido, pedido de **outro** usuário | `404` | autorizado a ver só os seus; não confirmamos que o outro existe |
| Login com senha errada ou usuário inexistente | `401`, corpo idêntico | não revelar quais contas existem |
| Muitas tentativas de login | `429` | limitação de taxa |

## 🧠 Pausa para lógica
**Problema.** Seu banco guarda `md5(senha)` sem salt. Descreva três consequências de um vazamento, e então o **plano de migração** para Argon2id **sem** forçar todos os usuários a trocarem a senha de uma vez (você não tem a senha em texto puro).

<details><summary>Dica</summary>Você não consegue converter o hash antigo em Argon2id, mas consegue <em>embrulhar</em> um hash dentro do outro, e também migrar no login.</details>

<details><summary>Solução comentada</summary>

Consequências: (1) senhas iguais têm hashes iguais, então quebrar uma revela todas as contas que a usam; (2) tabelas pré-calculadas e GPUs quebram a maior parte em horas; (3) a reutilização de senhas compromete as contas dos usuários em outros sites. Migração: **(a) embrulhar já:** trocar cada hash por `argon2(md5_antigo)` em um *script* (o hash antigo vira a “senha” da nova camada), e registrar no formato qual esquema é; **(b) no login:** verificar `argon2(md5(senha_digitada))` e, se OK, **regravar** como `argon2(senha_digitada)` e descartar o embrulho. Contas inativas ficam protegidas já pela camada nova; ativas migram sozinhas. Além disso, considerar forçar a troca das contas de maior risco e notificar conforme a LGPD, se houve vazamento (aula 07).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| Senha em texto puro ou criptografada | “Preciso mostrar de volta” | Nunca; use fluxo de redefinição |
| `sha256(senha)` ou `md5` | Hash rápido | Argon2id / PBKDF2 / bcrypt / scrypt |
| Mesmo salt para todos (ou sem salt) | “Simplificar” | Salt aleatório por usuário (as bibliotecas já fazem) |
| Implementar o próprio hash | Reinventar | Usar a biblioteca e o `make_password` do framework |
| Custo ajustado uma vez e esquecido | Hardware evolui | Reavaliar os parâmetros periodicamente |
| Regras de composição + troca obrigatória a cada 90 dias | Política antiga | Comprimento, lista de comuns, sem expiração arbitrária |
| “Usuário não encontrado” × “senha incorreta” | Mensagens diferentes | Mensagem única; mesmo trabalho nos dois caminhos |
| Bloquear a conta após 3 erros | Parece seguro | Vira DoS contra a vítima: limitar a taxa e usar atraso/CAPTCHA/MFA |
| Confundir 401 e 403 | Falta do conceito | 401 = não autenticado; 403 = autenticado sem permissão |
| Confiar em `is_authenticated` como autorização | Atalho | Verificar também a **permissão** e o **dono** do objeto |
| Senhas limitadas a 8 caracteres | Regra antiga | Permitir frases longas (64+ caracteres) |

- **Hash não é criptografia:** a senha nunca deve ser recuperável.
- **MFA** é a melhor camada extra (um vazamento de senha deixa de bastar).
- **Compare em tempo constante** (as bibliotecas de hash já o fazem; para outros segredos, `hmac.compare_digest`).

## 🧩 Exercícios
**1. Fixação.** (a) Por que o salt não torna o hash mais lento, e então para que ele serve? (b) Por que um hash “mais rápido” é pior para senhas? (c) Como o Django migra as senhas para um novo algoritmo sem pedir nada ao usuário? (d) Diferencie 401, 403 e 404 no contexto de autorização.

<details><summary>Solução</summary>

(a) Serve para que senhas iguais gerem hashes diferentes e para invalidar tabelas pré-calculadas; o custo vem dos parâmetros do algoritmo. (b) Porque quem rouba a tabela testa mais palpites por segundo. (c) O hash guardado indica o algoritmo; no login correto, se não for o primeiro de `PASSWORD_HASHERS`, o Django regrava no padrão atual. (d) 401: não autenticado; 403: autenticado mas sem permissão; 404: o recurso “não existe” para você (evita confirmar a existência de recursos alheios).
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `PASSWORD_HASHERS` com Argon2id primeiro e PBKDF2 depois, e o teste da migração no login
- [ ] `AUTH_PASSWORD_VALIDATORS` ativos (mínimo de 12) e testes de senhas fracas/longas
- [ ] Benchmark de hash anexado a `docs/seguranca.md`, com a escolha justificada
- [ ] Medição do tempo de login existente × inexistente (diferença dentro do ruído)
- [ ] Tabela 401/403/404 do projeto, com o teste de cada linha
- [ ] Fechar o achado A07 no relatório
- [ ] Commit `feat(security): argon2id hashing and password validators`

**3. Desafio (opcional).** Implemente `POST /api/v1/auth/password/change/` que exige a senha atual, valida a nova com os validadores, regrava o hash e **invalida os *refresh tokens* existentes** do usuário. Escreva os testes (incluindo o que acontece com o *access* antigo, aula 03).

## 🎤 Na entrevista
- **Como guardar senhas?** Como hash lento com salt aleatório por usuário (Argon2id, scrypt, bcrypt ou PBKDF2 com muitas iterações), nunca em texto puro nem com hash rápido; comparar em tempo constante e permitir subir o custo ao longo do tempo.
- **Para que serve o salt?** Para que a mesma senha gere hashes diferentes e para inutilizar tabelas pré-calculadas; ele não torna o hash mais lento.
- **Argon2 ou bcrypt?** Argon2id é a recomendação atual (custo em memória e tempo, resistente a GPU); bcrypt segue aceitável e muito difundido; PBKDF2 quando se exige conformidade com normas.
- **Qual a diferença entre autenticação e autorização?** Autenticação confirma quem você é; autorização decide o que você pode fazer.
- **O que é enumeração de usuários e como evitar?** Descobrir quais contas existem por diferenças de mensagem ou de tempo; evita-se com respostas idênticas, mesmo trabalho nos dois caminhos e limitação de tentativas.
- **Bloquear a conta após N tentativas é boa ideia?** Com ressalvas: pode permitir negação de serviço contra a vítima; prefira limite de taxa, atrasos progressivos e MFA.

## 📚 Para ir além
- 📄 Documentação oficial: [Django — Gerenciamento de senhas](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/). Hashers, validadores e migração.
- 📄 Documentação oficial: [Django — Autenticação](https://docs.djangoproject.com/en/5.2/topics/auth/default/). Usuários, permissões e grupos.
- 📄 Guia: [OWASP — Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html). Parâmetros recomendados (em inglês).
- 📄 Guia: [OWASP — Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html). Mensagens de erro, limitação e MFA (em inglês).
- 📄 Guia: [OWASP — Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html). Menor privilégio e checagem por objeto (em inglês).
- 📄 Norma: [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html). Política moderna de senhas (em inglês).
- 📄 Norma: [RFC 9106 — Argon2](https://datatracker.ietf.org/doc/html/rfc9106). Especificação do algoritmo (em inglês).
- 📄 Documentação: [argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/). A biblioteca usada pelo Django (em inglês).

## ✅ Checklist da aula
- [ ] Sei por que hash rápido e sem salt é inaceitável para senhas
- [ ] Medi o custo de PBKDF2, bcrypt, scrypt e Argon2id e justifiquei a escolha
- [ ] Configurei Argon2id sem invalidar as senhas antigas e testei a migração no login
- [ ] Ativei validadores de senha e testei senhas fracas e frases longas
- [ ] Verifiquei que o login não revela quem existe (resposta e tempo)
- [ ] Sei diferenciar 401, 403 e 404 e quando usar cada um
