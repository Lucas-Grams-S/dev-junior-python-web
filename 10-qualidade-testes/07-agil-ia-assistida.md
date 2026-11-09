# 7. Metodologias ágeis, trabalho em time e IA assistida

> ⏱️ ~1h30 · Módulo 10 · Pré-requisitos: [10.04 (TDD)](04-tdd.md), [10.05](05-ruff-mypy-precommit.md), [10.06](06-code-review-commits-readme.md), [9.06 (segredos)](../09-seguranca/06-segredos-dependencias-headers-rate-limit.md), [9.07 (LGPD)](../09-seguranca/07-https-lgpd.md)

> ✅ **Verificação.** Os trechos de código, ferramentas e medições abaixo foram **executados** em 2026-11-08 no laboratório do MiniShop (Python 3.13); **as saídas são reais**. As descrições de **Scrum** e do **Manifesto Ágil** foram conferidas nos textos oficiais (Guia Scrum, edição de novembro de 2020; Manifesto Ágil em português). Esta aula é mais de **prática de trabalho** do que de código; onde não há como "executar" (cultura de time, metodologia), digo isso e me apoio nas fontes. A sugestão de IA usada no exercício foi **escrita por mim, para a aula, imitando padrões comuns**; ela não vem de uma ferramenta específica.

## 🎯 Objetivos
- Explicar o que o **Manifesto Ágil**, o **Scrum**, o **Kanban** e o **XP** propõem, e como cada um aparece no dia a dia de um(a) dev júnior
- Transformar uma necessidade em **história de usuário** com **critérios de aceitação executáveis** e uma **definição de pronto** automatizada
- **Pedir ajuda**, dar e receber feedback e trabalhar de forma **assíncrona** sem virar gargalo
- Usar **IA como assistente** com método: acelerar o rascunho sem terceirizar a responsabilidade
- Reconhecer os riscos de código gerado por IA (erro plausível, dependência inventada, falha de segurança, dado vazado) e como **verificar** cada um

## 🤔 Por que isso importa
Seu primeiro emprego será menos sobre "saber tudo" e mais sobre **entregar em equipe**: entender o que pedem, quebrar em pedaços pequenos, pedir ajuda no tempo certo, revisar e ser revisado. E você vai trabalhar com assistentes de IA, que aceleram muito e erram com muita confiança. A diferença entre quem cresce e quem se complica é **método**: tratar a IA como um colega rápido que **você supervisiona**, não como um oráculo. Esses temas também são o centro das perguntas comportamentais de entrevista.

## 💡 Intuição (explicação simples)
- **Ágil** é navegar com **bússola e mapa que você atualiza**, em vez de traçar a rota inteira antes de sair: viagens curtas (iterações), olhar o terreno (feedback do usuário), corrigir o rumo.
- **Scrum** é uma **cadência**: um ritmo fixo de planejar, fazer, mostrar e melhorar. **Kanban** é um **quadro de fluxo**: mostra o trabalho andando e limita quanto fica "no ar" ao mesmo tempo. **XP** é o conjunto de **hábitos de engenharia** (testes, integração contínua, programar em par) que tornam as viagens curtas seguras.
- **IA assistida** é pedir ajuda a um **estagiário brilhante, incansável e excessivamente confiante**: rascunha em segundos, mas nunca diz "não sei", às vezes inventa, e **quem assina o commit é você**.

## 🔬 Como funciona por dentro
### Agilidade
- **Manifesto Ágil (2001):** valoriza *"Indivíduos e interações mais que processos e ferramentas"*, *"Software em funcionamento mais que documentação abrangente"*, *"Colaboração com o cliente mais que negociação de contratos"* e *"Responder a mudanças mais que seguir um plano"*, e conclui: *"mesmo havendo valor nos itens à direita, valorizamos mais os itens à esquerda"*. Não é "sem processo nem documentação": é prioridade.
- **Scrum (Guia de 2020):** um time com três responsabilidades (**Desenvolvedores, Product Owner e Scrum Master**) trabalha em **Sprints** de *"um mês ou menos"*, com cinco eventos: o próprio **Sprint**, a **Sprint Planning**, a **Daily Scrum** (15 minutos), a **Sprint Review** e a **Sprint Retrospective**. Três artefatos, cada um com um **compromisso**: **Product Backlog** → *Product Goal*; **Sprint Backlog** → *Sprint Goal*; **Incremento** → **Definição de Pronto** (*Definition of Done*).
- **Kanban:** visualizar o fluxo (A fazer → Fazendo → Revisão → Pronto), **limitar o trabalho em andamento (WIP)** e medir **tempo de ciclo** (do início ao fim de um item) e **vazão** (itens concluídos por período). Em vez de prazos fixos, melhora-se o fluxo continuamente.
- **XP e práticas de engenharia:** TDD, refatoração, integração contínua, propriedade coletiva do código, **programação em par**, releases pequenas. É o que você fez neste módulo.
- **Métodos servem ao time, não o contrário.** Muitas equipes misturam (Scrumban). A pergunta útil é *"isto nos ajuda a entregar valor com qualidade, e estamos aprendendo?"*.

### Da necessidade ao código
- **História de usuário:** *"Como [quem], quero [o quê], para [por quê]"*. Boas histórias são **INVEST**: Independentes, Negociáveis, de Valor, Estimáveis, Pequenas e Testáveis.
- **Critérios de aceitação:** a lista de condições que, se verdadeiras, tornam a história aceita. No formato **Dado / Quando / Então** (*Given/When/Then*, ou Gherkin), são **testáveis**, e o ideal é que virem **testes automatizados**: a história passa a ter uma prova executável.
- **Definição de Pronto (DoD):** o acordo do time do que significa "terminado" (testes, revisão, documentação, segurança…). A parte **mecânica** deve ser **automatizada** (um script/CI); a parte **humana** vai no checklist do PR.
- **Estimativa:** é um palpite sobre incerteza. Estimar **tamanho relativo** (pequeno/médio/grande, pontos) e **quebrar** até caber em poucos dias costuma funcionar melhor que prometer horas. Estimativa não é compromisso; **fatiar** é a melhor técnica.

### Trabalhando em time
- **Peça ajuda cedo, mas com contexto:** *"o que eu quero obter, o que eu já tentei, o que apareceu (erro completo), minha hipótese"*. Evite o "oi, posso fazer uma pergunta?" sem pergunta (*don't ask to ask*) e o **problema XY** (perguntar sobre a *tentativa de solução* em vez do *problema real*). Regra prática: se passou ~30 a 60 minutos sem progresso, pergunte.
- **Comunicação assíncrona:** escreva como se o outro estivesse em outro fuso: descrição de PR, mensagens completas, decisões registradas (ADRs). Reunião é para o que exige conversa.
- **Feedback:** receba com curiosidade; dê sobre o **trabalho**, específico, com exemplo e sugestão; elogie o que está bom (aula 06).
- **Programação em par:** duas pessoas, um teclado: uma *dirige*, outra *navega*; alternem. Ótima para onboarding, bugs difíceis e decisões de design.
- **Retrospectiva:** olhar para trás sem culpados: *o que foi bem, o que não foi, o que mudamos na próxima*. O resultado são **ações pequenas e donas** (alguém responsável).
- **Crescimento de um(a) júnior:** entregas pequenas e frequentes, perguntas boas, ler código dos outros, aceitar revisão, documentar o que aprendeu, e dividir o que descobriu.

### IA assistida: usar bem
- **O que a IA faz bem:** rascunhos (boilerplate, testes, scripts), explicar código ou erros, sugerir alternativas, traduzir entre linguagens, lembrar de sintaxe, propor refatorações **que você valida com testes**.
- **Onde ela falha de modo previsível:**
  1. **Erro plausível:** código que compila, roda no caminho feliz e está errado (bordas, dinheiro em `float`, erro engolido).
  2. **Alucinação:** funções, parâmetros ou **pacotes que não existem** (e atacantes podem registrar, no repositório público, nomes que assistentes costumam inventar).
  3. **Insegurança:** padrões vulneráveis comuns (SQL por texto, `except` nu, segredos no código, validação só no cliente).
  4. **Desatualização:** API antiga ou descontinuada; versão errada.
  5. **Contexto ausente:** ela não conhece as suas regras de negócio, arquitetura ou ADRs.
- **Regras de ouro:**
  - **Você é a pessoa responsável** pelo que commita: a revisão do código gerado é a mesma de qualquer PR (aula 06), talvez mais atenta.
  - **Especifique antes** (critérios de aceitação e **testes**) e use os testes como **contrato**; peça pedaços pequenos.
  - **Verifique** com as ferramentas (`ruff`, `mypy`, testes, `pip-audit`) **e** com leitura humana: elas não pegam erro de regra de negócio.
  - **Confira dependências e APIs** na fonte oficial antes de instalar ou usar.
  - **Não cole segredos, dados pessoais nem código/dados confidenciais** em serviços externos sem autorização (LGPD, política da empresa, contrato com o cliente). Pense: *"posso mostrar isto a uma pessoa de fora da empresa?"*.
  - **Entenda o que aceita.** Se você não consegue explicar a solução, não a commite; peça à IA que explique e depois teste a explicação.
  - **Mantenha a prática:** use a IA para aprender (peça explicações, contra-exemplos, perguntas) e não só para entregar, ou você não desenvolve o julgamento que a supervisão exige.
  - **Respeite licenças e a política da empresa** sobre uso de IA e sobre trechos gerados.
  - **Transparência:** diga quando um trecho relevante foi gerado/assistido, se o time ou a empresa pedir.

## 🛠️ Exemplo prático
### Parte A: da história ao teste
**1. A história** (`docs/historias/cupom.md`), com critérios no formato Dado/Quando/Então:
```markdown
# História: aplicar cupom ao pedido

**Como** cliente, **quero** informar um cupom ao finalizar a compra, **para** pagar menos.

## Critérios de aceitação (Dado / Quando / Então)
1. **Cupom percentual.** *Dado* o cupom `PROMO10` (10%), *quando* o subtotal é R$ 200,00, *então* o desconto é R$ 20,00.
2. **Desconto limitado.** *Dado* um cupom fixo de R$ 500,00, *quando* o subtotal é R$ 120,00, *então* o desconto é R$ 120,00 (nunca passa do subtotal).
3. **Cupom vencido.** *Dado* um cupom válido até 07/11/2026, *quando* hoje é 08/11/2026, *então* o pedido é recusado com "O cupom venceu em 07/11/2026.".
4. **Pedido mínimo.** *Dado* um cupom com mínimo de R$ 100,00, *quando* o subtotal é R$ 99,99, *então* o pedido é recusado informando o mínimo.
5. **Centavos.** *Dado* um desconto de 0,025, *quando* calculado, *então* vale R$ 0,03 (meio centavo para cima).

## Fora do escopo (nesta história)
Cupom por cliente, uso máximo e cumulativo (histórias futuras).

## Definição de pronto
Ver `scripts/definicao_de_pronto.sh`.
```
**2. Cada critério virou um teste** (`tests/test_aceitacao_cupom.py`); os comentários repetem a frase do critério, de modo que quem lê o teste lê a história:
```python
def test_criterio_1_cupom_percentual():
    cupom = Cupom(tipo="percentual", valor=D("10"))  # Dado o cupom PROMO10 (10%)
    desconto = calcular_desconto(cupom, D("200.00"))  # Quando o subtotal é R$ 200,00
    assert desconto == D("20.00")  # Então o desconto é R$ 20,00
```
```text
5 passed
```
Quando a pessoa que pediu a funcionalidade pergunta "como sei que o requisito 3 está implementado?", a resposta é um teste com o nome dele.

**3. A definição de pronto, automatizada** (`scripts/definicao_de_pronto.sh`). Cada item mecânico é um comando; o que é humano fica como lembrete:
```bash
#!/usr/bin/env bash
# Definição de pronto (DoD) AUTOMATIZADA: o que a máquina consegue afirmar sobre uma mudança. O resto é revisão humana.
cd "$(dirname "$0")/.."
export DEBUG=${DEBUG:-1}
falhas=0
passo() {  # passo "descrição" comando...
  local descricao=$1; shift
  if "$@" >/tmp/dod_saida.txt 2>&1; then printf "  [x] %s\n" "$descricao"; else printf "  [ ] %s   <-- FALHOU\n" "$descricao"; sed 's/^/        /' /tmp/dod_saida.txt | tail -5; falhas=$((falhas+1)); fi
}
echo "Definição de pronto (parte automática)"
passo "testes passam (todos os níveis, ordem aleatória)"               uv run pytest -q
passo "cobertura das camadas de negócio >= 80%"                         bash scripts/cobertura_negocio.sh
passo "formatação (ruff format)"                                        uv run ruff format --check
passo "lint (ruff check)"                                               uv run ruff check
passo "tipos (mypy)"                                                    uv run mypy
passo "arquitetura (import-linter)"                                     uv run lint-imports
passo "sem migração pendente"                                           uv run python manage.py makemigrations --check --dry-run
passo "contrato OpenAPI válido e sem avisos"                            uv run python manage.py spectacular --validate --fail-on-warn --file /tmp/dod_schema.yml
passo "dependências sem vulnerabilidade conhecida (pip-audit)"          bash -c 'uv export --no-hashes --no-emit-project -o /tmp/dod_req.txt >/dev/null && uv run pip-audit -r /tmp/dod_req.txt --no-deps --disable-pip'
echo "Parte humana (marque no PR): revisão aprovada · critérios de aceitação demonstrados · documentação/ADR atualizados · sem dado pessoal em log"
exit $falhas
```
```text
Definição de pronto (parte automática)
  [x] testes passam (todos os níveis, ordem aleatória)
  [x] cobertura das camadas de negócio >= 80%
  [x] formatação (ruff format)
  [x] lint (ruff check)
  [x] tipos (mypy)
  [x] arquitetura (import-linter)
  [x] sem migração pendente
  [x] contrato OpenAPI válido e sem avisos
  [x] dependências sem vulnerabilidade conhecida (pip-audit)
Parte humana (marque no PR): revisão aprovada · critérios de aceitação demonstrados · documentação/ADR atualizados · sem dado pessoal em log
```
E, como confio mais num portão que já vi **barrar**, deixei um `import os` sobrando em `cupons.py` e rodei de novo:
```text
  [ ] formatação (ruff format)   <-- FALHOU
  [ ] lint (ruff check)   <-- FALHOU
```
(Depois desfiz a alteração.) Os mesmos comandos viram um *job* do CI no módulo 12.

### Parte B: revisar uma sugestão de IA
**4. A sugestão** (`sugestao_ia.py`): ela compila, tem anotação de tipos, devolve o resultado certo para o caso feliz:
```python
"""Sugestão TÍPICA de um assistente de IA para 'aplicar cupom' (escrita por mim, para a aula, imitando padrões comuns): parece razoável, compila e roda."""
import sqlite3


def aplicar_cupom(total: float, cupom: str, caminho_do_banco: str = "db.sqlite3") -> float:
    try:
        conexao = sqlite3.connect(caminho_do_banco)
        linha = conexao.execute(f"SELECT percentual FROM cupons WHERE codigo = '{cupom}'").fetchone()
        desconto = total * linha[0] / 100
        return round(total - desconto, 2)
    except:
        return total
```
**5. O que as ferramentas dizem:**
```text
sugestao_ia.py:1:89: E501 Line too long (155 > 88)
sugestao_ia.py:5:89: E501 Line too long (91 > 88)
sugestao_ia.py:8:33: S608 Possible SQL injection vector through string-based query construction
sugestao_ia.py:8:89: E501 Line too long (101 > 88)
sugestao_ia.py:11:5: E722 Do not use bare `except`
Found 5 errors.
```
```text
mypy --strict:
sugestao_ia.py:10: error: Returning Any from function declared to return "float"  [no-any-return]
Found 1 error in 1 file (checked 1 source file)
```
O `ruff` achou **SQL montado por texto** (`S608`, injeção, aula 9.02) e **`except` nu** (`E722`); as linhas longas são ruído do padrão de 88 colunas. O `mypy` só reclamou do `Any` que sai do banco. **Ele não viu o erro de regra de negócio.**

**6. O que só os testes (escritos do requisito, não da sugestão) e a leitura humana pegam** (`teste_da_sugestao_ia.py`):
```text
E       Failed: DID NOT RAISE Exception
E       Failed: DID NOT RAISE Exception
E       Failed: DID NOT RAISE Exception
FAILED ../m10/teste_da_sugestao_ia.py::test_cupom_inexistente_deve_ser_recusado
FAILED ../m10/teste_da_sugestao_ia.py::test_erro_de_infraestrutura_nao_pode_virar_desconto_zero
FAILED ../m10/teste_da_sugestao_ia.py::test_aspas_no_codigo_do_cupom_nao_quebra_a_consulta
3 failed, 2 passed in 0.02s
```
- ✅ O caminho feliz passa (200 com 10% → 180).
- ❌ **Cupom inexistente não é recusado:** o `linha[0]` quebra com `TypeError`, o `except:` engole e a função **devolve o valor cheio, sem avisar ninguém**. O cliente acha que aplicou o cupom.
- ❌ **Erro de infraestrutura vira "sem desconto":** banco sem a tabela também cai no `except` e passa como se nada tivesse acontecido (um incidente mascarado).
- ❌ **Apóstrofo no código do cupom** (`O'BRIEN`) quebra a consulta e é engolido do mesmo jeito.
Além disso, há problemas que nenhum teste acima exercita mas a leitura mostra: a conexão nunca é fechada, o caminho do banco é padrão `"db.sqlite3"`, e o dinheiro está em `float`. Esse último eu **não presumi**; medi: comparei `float` + `round()` com `Decimal` + `ROUND_HALF_UP`, mesma política, em 80 000 casos (totais de R$ 0,01 a R$ 200,00 com 5%, 10%, 15% e 25%):
```text
casos: 80,000 (totais de R$ 0,01 a R$ 200,00 × 4 percentuais), mesma política de arredondamento
divergências float+round() × Decimal+ROUND_HALF_UP: 4,500 (5.62%)
  exemplo: total 0.02 com 25% → float+round dá 0.01, Decimal dá 0.02
  exemplo: total 0.06 com 25% → float+round dá 0.04, Decimal dá 0.05
  exemplo: total 0.3 com 5% → float+round dá 0.28, Decimal dá 0.29
das 4,500 divergências, 4,500 (100%) são EMPATES de meio centavo (o valor exato termina em ...5): o float não representa 0,015 exatamente
```
**5,6% dos casos divergem, e todos são empates de meio centavo** (ex.: 0,02 com 25% é 0,015 → deve valer 0,02; o `float` devolve 0,01), porque `0,015` não existe exatamente em binário. *(O caso "10,05 com 50%" que eu esperava que falhasse **passou**; vale registrar que nem todo risco teórico aparece no primeiro exemplo.)*

**7. Dependências sugeridas: existem?** (`checa_pacote.py`, consulta somente leitura ao PyPI):
```text
httpx                              ✅ existe · 77 versões · primeira publicação 2019-07-19 · última 2026-08-31 · página do projeto: https://github.com/encode/httpx
django-cupom-pro-max-ia-utils      ❌ NÃO EXISTE no PyPI (HTTP 404): provavelmente nome inventado; NÃO instale
python-cupons-brasil-oficial       ❌ NÃO EXISTE no PyPI (HTTP 404): provavelmente nome inventado; NÃO instale
```
Um pacote real tem **histórico** (77 versões desde 2019, projeto no GitHub); os outros dois são **nomes inventados** (404). Se alguém registrar um desses nomes amanhã com código malicioso, o `uv add` de uma sugestão cega instalaria. **Existir não é o mesmo que ser confiável:** olhe mantenedores, histórico, downloads, repositório e rode o `pip-audit`.

**8. O que fazer com a sugestão.** Aproveitar a *ideia*, refazer com o que a base já tem: `calcular_desconto` (aula 04) com `Decimal`, `ROUND_HALF_UP`, exceção `CupomInvalido` para cupom desconhecido, consulta pelo ORM/parâmetros e erro de infraestrutura **propagado**. A IA ajuda no rascunho; **os testes e os critérios de aceitação decidem se serve**.

### Parte C: modelos prontos para o time
**9. Pedido de ajuda (copie e use):**
```text
Objetivo: o que eu quero obter (e para quê).
Contexto: ambiente/versões, o que já funciona.
O que tentei: 1) ... 2) ...
O que aconteceu: erro COMPLETO (texto, não imagem) / comportamento observado vs esperado.
Hipótese: acho que é X porque Y.
Como reproduzir: comandos ou teste mínimo.
```
**10. Daily em 3 linhas:** *ontem* (entreguei/avancei), *hoje* (vou fazer), *bloqueios* (preciso de quem/de quê).
**11. Retrospectiva:** *o que foi bem · o que atrapalhou · uma ação pequena, com dona/dono e data*.
**12. Prompt com método** (para qualquer assistente): objetivo e **critérios de aceitação** · contexto relevante (sem segredos) · restrições (versões, estilo, `Decimal`, sem dependências novas) · **os testes que devem passar** · pedir **riscos e alternativas** · pedir explicação do que não for óbvio. Depois: ler o diff, rodar os portões, escrever o teste que falta.

### Parte D: estado do laboratório
```text
302 passed, 1 skipped, 1 xfailed        (inclui os 5 testes de aceitação do cupom)
ruff · mypy · lint-imports: limpos      definição de pronto: 9/9 itens automáticos [x]
```

## 🧠 Pausa para lógica
**Problema.** Um colega cola no assistente de IA o conteúdo do seu `.env` ("para ele entender a configuração") e um trecho do banco de produção com e-mails de clientes ("para ele depurar"). (a) Quais riscos existem? (b) O que deveria ter sido feito? (c) E se o assistente sugerir `pip install django-cupom-pro-max-ia-utils`?

<details><summary>Dica</summary>Pense em segredos, LGPD e em verificar o que a ferramenta devolve.</details>

<details><summary>Solução comentada</summary>

(a) O `.env` tem segredos (chaves, senhas): foram para um serviço externo, e precisam ser **rotacionados** como se tivessem vazado (aula 9.06). Os e-mails de clientes são **dados pessoais** enviados a terceiro sem finalidade nem base legal definidas: possível problema de LGPD (aula 9.07) e quebra de política da empresa. (b) Descrever a configuração **sem valores** (nomes das variáveis), usar dados **sintéticos ou anonimizados** para reproduzir o bug, e conferir a política da empresa sobre ferramentas de IA. Comunicar o incidente ao time/encarregado. (c) Verificar se o pacote **existe** e é confiável (PyPI, mantenedor, histórico, repositório); um nome que o PyPI desconhece é provavelmente inventado, e instalar sem checar abre a cadeia de suprimentos (OWASP A03).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| "Somos ágeis" mas há só reuniões | Cerimônia sem propósito | Perguntar o que cada prática melhora; ajustar |
| Histórias gigantes e vagas | Sem fatiar | INVEST; critérios Dado/Quando/Então |
| Critério que ninguém consegue testar | Palavras como "rápido", "amigável" | Torne mensurável ("responde em < 500 ms") |
| "Pronto" que depende de memória | DoD só mental | Script/CI para o mecânico, checklist para o humano |
| Estimativa vira promessa | Pressão | Fatiar, usar faixas, comunicar incerteza |
| Passar horas travado sem pedir ajuda | Receio de incomodar | Regra do tempo (30–60 min) + pedido de ajuda bem escrito |
| Pergunta sem contexto ("não funciona") | Pressa | Objetivo, tentativa, erro completo, hipótese |
| Aceitar código de IA sem ler | Confiança na fluência | Revisão como qualquer PR; testes do requisito |
| Instalar o pacote que a IA citou | Não verificar | Checar existência, histórico e mantenedores; `pip-audit` |
| Colar `.env`, chaves ou dados de clientes no assistente | Falta de política | Descrever sem valores; dados sintéticos; política da empresa; rotacionar se vazou |
| Só pedir para a IA fazer | Atalho | Pedir explicações, tentar antes, comparar soluções |
| Esconder que usou IA | Receio de julgamento | Seguir a política do time; ser transparente quando relevante |
| Levar feedback para o lado pessoal | Identificação com o código | Separar pessoa de código; pedir exemplos |

- **Fatie, meça, melhore** é o resumo dos métodos ágeis.
- **A IA acelera o rascunho; julgamento e responsabilidade continuam com você.**
- **Aprenda em voz alta:** documentar e explicar para outras pessoas consolida o que você sabe.

## 🧩 Exercícios
**1. Fixação.** (a) Quais as quatro prioridades do Manifesto Ágil? (b) Cite os cinco eventos do Scrum. (c) O que é WIP e por que limitá-lo? (d) Por que "existe no PyPI" não basta para confiar num pacote?

<details><summary>Solução</summary>

(a) Indivíduos e interações; software em funcionamento; colaboração com o cliente; responder a mudanças (mais que processos/ferramentas, documentação abrangente, negociação de contratos e seguir um plano). (b) Sprint, Sprint Planning, Daily Scrum, Sprint Review e Sprint Retrospective. (c) *Work in progress*: itens começados e não concluídos; limitar reduz trocas de contexto, expõe gargalos e acelera a conclusão (menor tempo de ciclo). (d) Qualquer pessoa pode registrar um nome; é preciso olhar histórico, mantenedores, repositório, uso e auditar vulnerabilidades.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] Uma **história de usuário** real do MiniShop em `docs/historias/`, com 4–6 critérios Dado/Quando/Então
- [ ] **Um teste de aceitação por critério**, com a frase do critério nos comentários
- [ ] `scripts/definicao_de_pronto.sh` (ou um workflow do CI) rodando **todos os portões** e a saída anexada, mais uma execução em que ele **falha**
- [ ] Um **quadro Kanban** do módulo (A fazer / Fazendo / Revisão / Pronto) com limite de WIP e as histórias reais
- [ ] **Revisão de uma sugestão de IA** (qualquer assistente) sobre um problema do MiniShop: guarde a sugestão, a saída do `ruff`/`mypy`/testes e a lista do que só a revisão humana achou
- [ ] Uma checagem de **dependência** sugerida (existe? histórico? `pip-audit`)
- [ ] `docs/uso-de-ia.md` com as **regras do projeto** (o que pode e o que não pode ser compartilhado; como verificar; como declarar o uso)
- [ ] Commit `docs: história do cupom e uso responsável de IA`

**3. Desafio (opcional).** Faça uma **programação em par** (com uma pessoa ou com um assistente de IA como "navegador") de uma história pequena usando TDD. Registre três decisões que o par mudou e uma que você não teria pensado sozinho(a).

## 🎤 Na entrevista
- **O que é metodologia ágil?** Uma abordagem de entregar valor em ciclos curtos com feedback frequente, priorizando pessoas, software funcionando, colaboração e adaptação; o Scrum e o Kanban são formas de aplicá-la.
- **Diferença entre Scrum e Kanban?** Scrum usa Sprints (ciclos fixos de até um mês), papéis e eventos definidos; Kanban visualiza o fluxo e limita o trabalho em andamento, sem iterações obrigatórias.
- **O que é Definição de Pronto?** O acordo do time sobre o que "terminado" significa (testes, revisão, documentação, segurança…), parte dela automatizada.
- **Como você pede ajuda?** Depois de tentar por um tempo, com objetivo, o que tentei, o erro completo e minha hipótese, para a pessoa responder sem precisar perguntar de volta.
- **Conte uma situação em que recebeu feedback duro.** (Use um exemplo real: o que foi dito, como reagiu, o que mudou depois.)
- **Como você usa IA no trabalho?** Para rascunhos, testes, explicações e alternativas; sempre com critérios e testes definidos antes, revisando o resultado como qualquer PR, verificando APIs e dependências, sem compartilhar segredos nem dados pessoais, e assumindo a responsabilidade pelo que commito.
- **Quais os riscos do código gerado por IA?** Erros plausíveis, alucinação (inclusive de pacotes), padrões inseguros, desatualização, falta de contexto de negócio, vazamento de dados no prompt e dependência excessiva.

## 📚 Para ir além
- 📄 Manifesto: [Manifesto para o Desenvolvimento Ágil de Software](https://agilemanifesto.org/iso/ptbr/manifesto.html) e os [12 princípios](https://agilemanifesto.org/iso/ptbr/principles.html).
- 📄 Guia oficial: [O Guia do Scrum](https://scrumguides.org/scrum-guide.html) (edição de 2020; há versão em português na página) e o [Guia do Kanban](https://kanbanguides.org/).
- 📄 Glossário: [Agile Alliance: Definition of Done](https://www.agilealliance.org/glossary/definition-of-done/) (em inglês).
- 📄 Tutorial: [Atlassian: introdução ao Agile](https://www.atlassian.com/br/agile) e [histórias de usuário](https://www.atlassian.com/br/agile/project-management/user-stories).
- 📄 Referência: [Gherkin](https://cucumber.io/docs/gherkin/reference) e [Given-When-Then (Fowler)](https://martinfowler.com/bliki/GivenWhenThen.html) (em inglês).
- 📄 Comunicação: [Don't ask to ask](https://dontasktoask.com/) e [O problema XY](https://xyproblem.info/) (em inglês).
- 📄 Referência: [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/). Riscos de segurança de sistemas com IA (em inglês).
- 📚 Livros: *Scrum: A Arte de Fazer o Dobro do Trabalho na Metade do Tempo*, de Jeff Sutherland; *Extreme Programming Explained*, de Kent Beck (em inglês).

## ✅ Checklist da aula
- [ ] Sei explicar Manifesto, Scrum, Kanban e XP com minhas palavras
- [ ] Transformei uma necessidade em história com critérios que viraram testes
- [ ] Tenho uma definição de pronto automatizada que já vi falhar
- [ ] Sei pedir ajuda e dar/receber feedback
- [ ] Reviso código de IA como qualquer PR e verifico APIs e dependências
- [ ] Nunca compartilho segredos nem dados pessoais com ferramentas externas sem autorização
