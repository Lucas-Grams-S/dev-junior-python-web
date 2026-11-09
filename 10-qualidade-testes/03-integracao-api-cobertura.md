# 3. Testes de integração, de API e cobertura

> ⏱️ ~1h30 · Módulo 10 · Pré-requisitos: [10.01](01-piramide-fixtures.md), [10.02](02-parametrize-mocks.md), [6.01–6.05 (API REST)](../06-apis-rest/README.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19, `pytest-cov`/`coverage` 7.17, `pytest-xdist` 3.8). **As saídas são reais.** A suíte chegou a **280 passed, 1 skipped, 1 xfailed**. Os experimentos de "mutante" da seção 5 foram feitos num arquivo temporário e numa alteração temporária, ambos desfeitos.

## 🎯 Objetivos
- Escrever testes de **integração** (peças reais juntas, com banco) e de **API** (rota → serialização → permissão → banco)
- Medir **cobertura de linhas e de ramos** e usá-la para **achar buracos**, não para exibir um número
- Definir uma **meta por camada** (≥ 80% nas camadas de negócio) e uma **porta de qualidade** automatizada
- Entender por que cobertura **não mede qualidade** (mutação)
- Usar `django_assert_max_num_queries`, `transaction=True` e **paralelismo** (`xdist`) com consciência

## 🤔 Por que isso importa
"Qual a cobertura de testes do projeto?" é a pergunta mais comum e a mais mal usada. Um número alto pode esconder um módulo inteiro sem teste (a média disfarça) ou testes que não verificam nada. Saber **medir, ler e desconfiar** da cobertura, e transformar o resultado em testes que **pegam bugs**, é uma habilidade que aparece em code reviews e entrevistas.

## 💡 Intuição (explicação simples)
Cobertura é um **mapa de calor das salas visitadas** por um fiscal. Dizer "o fiscal passou por 90% do prédio" não diz se ele **olhou** alguma coisa: pode ter atravessado as salas de olhos fechados. Serve, porém, para uma pergunta útil: **"que salas ninguém visitou?"** Aí vão os testes novos. Já a **mutação** é plantar um defeito de propósito e ver se o fiscal o encontra: aí sim se mede se ele olha.

## 🔬 Como funciona por dentro
- **Teste de integração:** exercita **peças reais** juntas (serviço + banco + transação; tarefa + modelo). No Django/pytest-django: `@pytest.mark.django_db` (cada teste numa transação revertida) ou `transaction=True` (commits reais, necessário para `on_commit`, concorrência e threads).
- **Teste de API:** chama a rota como um cliente (`APIClient`/`Client`): verifica **status**, **corpo** (e o formato de erro), **cabeçalhos** e **efeitos** (o que ficou no banco). Cobre autenticação, permissões, validação e serialização de uma vez. É integração por natureza, mas o *foco* é o contrato HTTP.
- **O que testar em cada rota (lista de bolso):** caminho feliz; sem autenticação (`401`); sem permissão (`403`/`404`); entrada inválida (`400`/`422`); recurso inexistente (`404`); regra de negócio violada (`422`); idempotência (repetir); efeito colateral no banco; e, em listas, **paginação, filtros e número de consultas** (N+1).
- **Cobertura de linhas × de ramos (*branch*):** linhas diz "esta linha executou"; **ramos** diz "o `if` foi verdadeiro **e** falso". Um `if x: y()` com 100% de linhas pode nunca ter testado o caso `x` falso. Use sempre `--cov-branch`.
- **O que a cobertura mostra:** o que **nunca executou** (buracos). **O que não mostra:** se o que executou foi **verificado**. Cobertura alta é necessária para confiança, nunca suficiente.
- **Meta por camada, não global:** o total é diluído por código que não importa (migrações, scripts, telas de demonstração). Defina o limite onde dói: **regras de negócio** (serviços, domínio, repositórios, tarefas) ≥ 80%, com ramos. Outras camadas (interface, configuração) valem menos como número.
- **Omitir arquivos da medição** só com **justificativa por escrito** (código didático, simulador, rotas só de experimento). Omitir para "bater a meta" é trapaça consigo mesmo.
- **Teste de mutação:** troca-se um operador do código (`==` por `!=`) e roda-se a suíte; se **nenhum teste falha**, o mutante "sobreviveu" e há uma asserção faltando. Existem ferramentas (`mutmut`, `cosmic-ray`); aqui fazemos à mão, como na aula 9.05.
- **Paralelismo:** `pytest-xdist` (`-n 4`) distribui testes por processos, cada um com **banco próprio**. Exige testes independentes (aula 01). O ganho é menor que o número de processos (custos de inicialização).

## 🛠️ Exemplo prático
**1. O ponto de partida: 90% no total, mas com buracos em código de negócio.** (`pytest --cov --cov-branch --cov-report=term-missing:skip-covered`)
```text
apps/payments/outbox.py                    35   35   10   0    0%   2-50
apps/accounts/management/commands/anonimizar_titular.py   13   13   0   0   0%
apps/cart/services.py                      49    5   18   5   85%   23, 34, 50, 53, 57
apps/payments/services.py                  41    3   16   3   89%   32, 35, 48
apps/orders/tasks.py                       82    6    8   0   93%   20-22, 101-102, 118-119
apps/catalog/estilos.py / orders/email_backend.py / config/views_demo.py   0% e 56%
TOTAL                                    1525  130  232  25   90%
```
Lendo o relatório, não o total:
- **`outbox.py` com 0%:** o relé do outbox (aula 7.10) só tinha sido exercitado com RabbitMQ de verdade, **fora da suíte**. Era a peça que garante que "pedido pago" não se perde, sem nenhum teste automatizado.
- **`cart/services.py` e `payments/services.py`:** exatamente os **ramos de erro** (estoque insuficiente, valor divergente, pagamento desconhecido, pedido já cancelado) estavam sem teste; é onde as regras de negócio moram.
- **`estilos.py`, `email_backend.py`, `views_demo.py`:** arquivos **didáticos/simulados** do laboratório, sem rota. A decisão (documentada em `pyproject.toml`) foi **omitir da medição**, com um comentário ao lado de cada um no `pyproject.toml`; não são código de negócio.

**2. A configuração da medição e a porta de qualidade** (`pyproject.toml` e `scripts/cobertura_negocio.sh`):
```toml
[tool.coverage.run]
branch = true
source = ["apps", "config", "legado"]
omit = [
    "*/migrations/*",
    "apps/catalog/estilos.py",        # arquivo DIDÁTICO da aula 6.04 (4 estilos de view); não tem rota
    "apps/orders/email_backend.py",   # SMTP SIMULADO do laboratório (aula 7.06)
    "config/views_demo.py",           # rotas de experimento da série (só em DEBUG)
]

[tool.coverage.report]
show_missing = true
```
```bash
#!/usr/bin/env bash
# Porta de qualidade: cobertura (linhas + ramos) das CAMADAS DE NEGÓCIO >= 80%. O total do projeto é só informativo.
set -euo pipefail
NEGOCIO="apps/*/services.py,apps/*/domain.py,apps/*/selectors.py,apps/*/repositories.py,apps/*/tasks.py,apps/payments/outbox.py,apps/payments/gateway.py,apps/accounts/lgpd.py,legado/precificacao.py"
uv run pytest -q --cov --cov-branch -p no:randomly > /dev/null
echo "== camadas de negócio (limite 80%)"
uv run coverage report --include="$NEGOCIO" --fail-under=80 --no-skip-covered
echo "== projeto inteiro (informativo)"
uv run coverage report | tail -1
```
O script falha (`--fail-under=80`) se as **camadas de negócio** ficarem abaixo de 80% (linhas **e** ramos); o total do projeto é só informativo.

**3. Fechando os buracos com testes que verificam.** Quatro arquivos novos, todos com asserções sobre o **resultado**:
- `tests/test_servico_carrinho.py` (11 casos): quantidade inválida, produto inativo/inexistente, estoque, máximo, somar ao item, `set_quantity` (zero remove, negativa, não está no carrinho, acima do máximo), com `parametrize`.
- `tests/test_pagamentos_servico.py` (7 casos): evento de tipo sem efeito, pagamento desconhecido, **valor divergente**, pago atualiza o pedido **e** grava o evento de domínio na mesma transação, duplicata, estado que não retrocede, pagamento de pedido já cancelado (loga o aviso e **não ressuscita** o pedido).
- `tests/test_outbox_rele.py` (5 casos): o relé com um **canal falso em memória** (sem RabbitMQ): publica e marca, respeita o lote, queda entre publicar e marcar → **republica** (at-least-once), consumidor idempotente ignora duplicata pelo `message_id`.
- `tests/test_comandos_e_tarefas.py` (7 casos): comandos de LGPD (inclusive usuário inexistente), `MarcaFalha`, limpeza de chaves antigas e o batimento.
O relé merece destaque: o canal falso tem só 3 métodos e transforma uma peça que exigia infraestrutura em testes de milissegundos:
```python
class CanalFalso:
    """Imita só o que o relé usa do pika: publicar, buscar e confirmar."""
    def __init__(self):
        self.fila, self.confirmadas = [], []

    def basic_publish(self, exchange, routing_key, corpo, propriedades, mandatory=False):
        self.fila.append((routing_key, corpo, propriedades))

    def basic_get(self, nome_da_fila, auto_ack=False):
        if not self.fila:
            return None, None, None
        tipo, corpo, props = self.fila.pop(0)
        return SimpleNamespace(delivery_tag=len(self.confirmadas) + 1), props, corpo

    def basic_ack(self, tag):
        self.confirmadas.append(tag)
```
Resultado:
```text
== camadas de negócio (limite 80%)
Name                          Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------------
apps/accounts/lgpd.py            28      0      8      0   100%
apps/cart/services.py            49      0     18      0   100%
apps/orders/domain.py            45      0     12      0   100%
apps/orders/repositories.py      65      0      2      0   100%
apps/orders/selectors.py          4      0      0      0   100%
apps/orders/services.py          46      2     12      0    97%   53-54
apps/orders/tasks.py             82      2      8      0    98%   101-102
apps/payments/gateway.py         71      2     14      0    98%   77-78
apps/payments/outbox.py          35      5     10      1    87%   14-18, 38->50
apps/payments/services.py        41      0     16      0   100%
legado/precificacao.py           24      0      8      0   100%
-------------------------------------------------------------------------
TOTAL                           490     11    108      1    98%
== projeto inteiro (informativo)
TOTAL                                                          1415     35    224     17    97%
```
**Camadas de negócio de 88% para 98%**, projeto de 90% para 97%. Decomposição honesta do total: **90%** no início → **92%** só com o `omit` dos três arquivos didáticos → **97%** com os testes novos. O limite de 80% passa com folga; o que sobra (`orders/tasks.py` linhas 101-102, `outbox.py` linhas 14-18 que abrem a conexão real) é código de **infraestrutura** que exigiria o RabbitMQ/Celery reais e fica para testes de integração de ambiente.

**4. Testes de API: a lista de bolso aplicada.** O MiniShop já tinha estes padrões (aulas 6 e 9): `api_as("cliente")` autentica de verdade (JWT real), a **matriz de autorização** (9.05) cobre 401/403/404, os erros seguem o formato `{"detail", "code"}`, e a lista de produtos tem um guarda contra N+1:
```python
def test_lista_de_produtos_nao_faz_n_mais_1(api, django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        assert api.get("/api/v1/products/").status_code == 200
```
`django_assert_max_num_queries(4)` falha se alguém reintroduzir uma consulta por item, e é um teste de **desempenho que ninguém precisa lembrar de rodar**. Quando um teste precisa de **commits reais** (`on_commit`, threads, concorrência), usa-se `transaction=True`, como no teste de concorrência da aula 8.06 (que então precisa de `serialized_rollback=True` para não apagar os dados das migrações).

**5. O número que mente: cobertura sem verificação.** Escrevi um teste **temporário** que executa todos os ramos de `processar_evento` **sem uma única asserção**, e comparei com os testes reais:
```text
SÓ o teste vazio :  apps/payments/services.py   41  1  16  3   93%    (1 passed)
SÓ os testes reais: apps/payments/services.py   41  0  16  2   96%    (7 passed)
```
O teste que **não verifica nada** deu **93% de cobertura**. Depois, o mutante: inverti a checagem de valor (`evento.valor != pagamento.amount` → `==`, ou seja, passar a aceitar valor divergente, uma falha de segurança de verdade):
```text
teste vazio  → 1 passed          (o bug passou despercebido)
testes reais → 5 failed, 2 passed (o bug foi pego)
```
(O arquivo temporário e o mutante foram removidos; confirmei.) **Moral:** cobertura é um detector de **buracos**, não um certificado de qualidade. Quando for preciso medir qualidade de verdade, é a mutação.

**6. Paralelizando** (`pytest-xdist`; máquina com 12 núcleos, SQLite em memória):
```text
serial    → 280 passed, 1 skipped, 1 xfailed in 10.07s 10.91 s 
xdist -n 2 → 280 passed, 1 skipped, 1 xfailed in 6.82s 7.40 s 
xdist -n 4 → 280 passed, 1 skipped, 1 xfailed in 5.04s 5.62 s 
```
Serial: 10,9 s; com 2 processos: 7,4 s; com 4: 5,6 s. O ganho é **sublinear** (2× de processos não dá 2× de velocidade) por causa da inicialização de cada processo e do banco de cada um. Funcionou sem alterar nenhum teste, **porque os testes são independentes** (aula 01). Em PostgreSQL, o xdist cria um banco de teste por processo (`test_<nome>_gw0`, `_gw1`…); não medi aqui.

> 🔎 **Higiene de medição.** Numa verificação posterior, em outra cópia do projeto, o mesmo `-n 4` levou **75 s** uma única vez. Repetido, voltou a **4,7 s** (duas execuções) contra 9,9 s em série. Naquele momento o computador estava sob pressão de memória (muita carga e *swap* por outros programas), não era o código. Por isso, **meça mais de uma vez** antes de tirar conclusões sobre tempo, e desconfie de um único número fora da curva.

**7. Estado final**
```text
280 passed, 1 skipped, 1 xfailed          (pytest-randomly, semente 2024; ~9,7 s em série)
```

## 🧠 Pausa para lógica
**Problema.** Um módulo tem 10 linhas executáveis e este código: `def desconto(total, vip): d = 0; if vip: d = total*0.1; if total > 100: d += 5; return d`. Um único teste `desconto(200, True)` dá 100% de **linhas**. (a) Qual é a cobertura de **ramos**? (b) Quais testes faltam? (c) Dê um mutante que esse teste único não pega.

<details><summary>Dica</summary>Cada `if` tem dois ramos (verdadeiro e falso); o teste só entra pelo verdadeiro nos dois. Pense em trocar `>` por `>=` ou `0.1` por `0.2`.</details>

<details><summary>Solução comentada</summary>

(a) Há 2 `if`, logo 4 ramos; o teste cobre apenas os dois "verdadeiros": **50% dos ramos**, mesmo com 100% das linhas. (b) `desconto(50, False)` (os dois falsos) e, para as fronteiras, `desconto(100, False)` e `desconto(101, False)` (exatamente 100 e logo acima), e `desconto(200, False)` para isolar os efeitos. (c) Trocar `total > 100` por `total >= 100`: com 200 o resultado é o mesmo, e o teste único passa; só o caso `total == 100` revela. Trocar `0.1` por `0.2` também sobrevive se a asserção for fraca (por exemplo `assert desconto(200, True) > 0`).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| "Temos 90% de cobertura" e um módulo inteiro a 0% | Olhar só o total | Ler o relatório por arquivo; meta por camada |
| Cobertura alta, bugs passam | Testes sem asserções fortes | Mutação (manual ou `mutmut`); asserir resultados |
| Linhas 100%, ramos 50% | Só cobertura de linhas | `--cov-branch` sempre |
| Omitir arquivos para atingir a meta | Número como objetivo | Omitir só o que não é código de negócio, com justificativa escrita |
| Testes escritos só para "subir a barra" | Cobertura como meta | Escrever pelo risco (regra de negócio, dinheiro, segurança) |
| Testar a implementação (`assert mock.called`) | Acoplar ao interno | Testar estado e contrato (aula 02) |
| Teste de API que só confere `status_code == 200` | Asserção rasa | Conferir corpo, formato do erro, efeito no banco |
| Lista sem guarda de N+1 | Desempenho não testado | `django_assert_max_num_queries` |
| `transaction=True` em tudo | Medo de transação | Só quando preciso (commit real); é mais lento e exige limpeza |
| xdist e testes que compartilham arquivo/porta | Estado global | Isolar recursos por processo; testes independentes |
| Peça de infraestrutura sem teste (relé, fila) | "Precisa do broker" | Canal/cliente falso em memória + teste de ambiente à parte |
| Porta de cobertura que ninguém roda | Só local | Rodar no CI (módulo 12) e falhar o PR |

- **Cobertura serve para achar buracos.** Meça, leia o relatório, escreva o teste que importa.
- **Meta por camada**, medida com ramos, e **automatizada**.
- **Desconfie do verde:** valide testes críticos por mutação.

## 🧩 Exercícios
**1. Fixação.** (a) Qual a diferença entre cobertura de linhas e de ramos? (b) Por que o total do projeto é uma métrica ruim sozinha? (c) O que um teste de API deve verificar além do status? (d) Quando usar `transaction=True`?

<details><summary>Solução</summary>

(a) Linhas: a linha executou. Ramos: cada decisão foi exercitada nos dois sentidos (verdadeiro e falso). (b) A média dilui módulos críticos sem teste entre muitas linhas triviais; uma meta por camada expõe o buraco. (c) O corpo (e o formato de erro), cabeçalhos relevantes, e o efeito no banco; além dos casos 401/403/404/400/422. (d) Quando o teste precisa de commits reais: `on_commit`, threads/concorrência, ou observar de outra conexão.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `[tool.coverage]` configurado (ramos, `omit` com **comentário justificando cada item**)
- [ ] `scripts/cobertura_negocio.sh` falhando abaixo de 80% nas camadas de negócio (e a lista dos arquivos incluídos)
- [ ] Relatório **antes/depois** por arquivo, com a decomposição (efeito do `omit` × efeito dos testes novos)
- [ ] Testes novos para **todos** os arquivos de negócio abaixo da meta, incluindo um relé/cliente de infraestrutura com **canal falso**
- [ ] **Um** teste de "cobertura sem verificação" demonstrado e desfeito, com o mutante registrado
- [ ] Guarda de N+1 em cada lista da API (`django_assert_max_num_queries`)
- [ ] `pytest -n 4` funcionando e o ganho de tempo medido
- [ ] Commit `test: close business-layer coverage gaps and add quality gate`

**3. Desafio (opcional).** Instale `mutmut` e rode-o em `apps/payments/services.py`. Compare os mutantes sobreviventes com os testes que você tem e escreva os que faltam até a pontuação de mutação passar de 90%.

## 🎤 Na entrevista
- **O que é cobertura de testes e qual a meta?** A fração do código executada pelos testes (linhas e ramos); a meta depende do risco, mas costuma-se exigir algo como 80% nas regras de negócio; cobertura alta é necessária, não suficiente.
- **Cobertura de linhas × ramos?** Linhas conta o que executou; ramos exige exercitar cada decisão nos dois sentidos.
- **Cobertura alta garante qualidade?** Não: um teste sem asserções pode cobrir tudo e não detectar nada; por isso se usa mutação e revisão dos testes.
- **O que você testa numa rota de API?** Caminho feliz, autenticação e permissão, validação, erros de negócio, efeitos no banco, idempotência e, em listas, paginação e número de consultas.
- **Como testar código que depende de infraestrutura (fila, broker)?** Isolando a lógica e usando um cliente/canal falso em memória nos testes rápidos, mais um teste de ambiente com o serviço real.
- **O que é um teste de mutação?** Alterar o código de propósito (um operador, uma constante) e verificar se algum teste falha; se não falha, falta uma asserção.

## 📚 Para ir além
- 📄 Documentação: [Coverage.py](https://coverage.readthedocs.io/en/latest/) e [cobertura de ramos](https://coverage.readthedocs.io/en/latest/branch.html). Configuração, `omit` e relatórios (em inglês).
- 📄 Documentação: [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/) e [pytest-xdist](https://pytest-xdist.readthedocs.io/en/stable/). Cobertura e paralelismo (em inglês).
- 📄 Documentação oficial: [DRF — Testes](https://www.django-rest-framework.org/api-guide/testing/) e [Django — Ferramentas de teste](https://docs.djangoproject.com/en/5.2/topics/testing/tools/). `APIClient`, `Client`, `assertNumQueries`.
- 📄 Documentação: [pytest-django — Helpers](https://pytest-django.readthedocs.io/en/latest/helpers.html). `django_assert_max_num_queries`, `django_capture_on_commit_callbacks`.
- 📄 Artigo: [Google Testing Blog — Code Coverage Best Practices](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html). O que a cobertura diz e não diz (em inglês).
- 📄 Artigo: [Martin Fowler — Test Coverage](https://martinfowler.com/bliki/TestCoverage.html). Para que serve (em inglês).
- 🧰 Ferramenta: [mutmut](https://mutmut.readthedocs.io/en/latest/). Teste de mutação para Python (em inglês).

## ✅ Checklist da aula
- [ ] Medi a cobertura com ramos e li o relatório por arquivo
- [ ] Tenho uma meta por camada (≥ 80% nas de negócio) e um script que a verifica
- [ ] Fechei os buracos de negócio com testes que verificam resultados
- [ ] Testei uma peça de infraestrutura com um canal/cliente falso
- [ ] Demonstrei, por mutação, que cobertura não é qualidade
- [ ] Medi o ganho de tempo do paralelismo
