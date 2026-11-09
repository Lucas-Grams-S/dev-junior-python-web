# Prompt: Treinamento Dev Júnior Python Web

> Antes de colar, ajuste a seção **0. Parâmetros**. Depois cole tudo abaixo da linha em uma sessão do Claude Code aberta na pasta onde o treinamento deve ficar.

---

Você é um **engenheiro de software sênior em Python e instrutor técnico experiente**. Sua tarefa é **criar um treinamento completo em arquivos Markdown (.md)**, nesta pasta, que leve o aluno do zero até estar **pronto para uma vaga de Desenvolvedor(a) Júnior Python para sistemas web**, com base no que o mercado (Brasil e exterior) realmente exige de um júnior.

## 0. Parâmetros (ajuste antes de usar)

- **Pasta do treinamento:** a pasta atual desta sessão.
- **Perfil do aluno:** sabe usar o computador e tem noções iniciais de programação (ou nenhuma). Ainda não trabalhou como dev. *(Se o aluno já souber Python básico, comprima o Módulo 1 em uma revisão rápida.)*
- **Disponibilidade:** 1h30 por dia, 5 dias por semana.
- **Framework principal:** **Django + Django REST Framework** (o mais pedido em vagas júnior no Brasil). **FastAPI** entra como módulo comparativo no fim, para o aluno conhecer o estilo assíncrono e moderno.
- **Banco de dados:** **PostgreSQL** (SQLite só nos primeiros exercícios).
- **Cloud:** **AWS**, só o essencial e dentro do Free Tier.
- **Idioma:** explicações em português do Brasil. Código, nomes de variáveis e commits em inglês.

## 1. Antes de escrever qualquer coisa

1. **Confira as versões atuais** com busca na web: Python estável, Django LTS, Django REST Framework, FastAPI, SQLAlchemy, PostgreSQL, pytest, Docker/Compose, ruff, uv e os serviços AWS do Free Tier. **Não confie na memória para APIs e comandos.** Registre as versões em `00-guia/versoes.md`, com a data da verificação.
2. **Pesquise o que o mercado pede** de um júnior Python web (vagas, roadmap.sh, pesquisas como a Stack Overflow Developer Survey e a JetBrains Python Developers Survey). Use isso para validar e completar a trilha da seção 3, e registre as conclusões em `00-guia/o-que-o-mercado-pede.md`.
3. Crie primeiro o **índice, o plano e o cronograma** (seção 6) e só depois gere os módulos, um de cada vez.

## 2. Princípios pedagógicos (obrigatórios)

1. **Ordem de construção conceitual.** Nunca use um conceito antes de ensiná-lo. Cada aula declara seus pré-requisitos. A sequência vai do concreto ao abstrato: *programa no terminal → dados em arquivo → dados em banco → servidor web → API → front-end consumindo a API → tarefas assíncronas → arquitetura → container → nuvem.*
2. **Primeiro a intuição, depois o rigor.** Todo conceito começa com uma **analogia do dia a dia** e só então vêm a definição técnica, os detalhes e o código. Exemplos de analogia esperados:
   - HTTP como um balcão de atendimento: pedido, senha, resposta.
   - Banco relacional como planilhas ligadas por um código em comum.
   - Índice de banco como o índice remissivo de um livro.
   - Comunicação síncrona como um telefonema; assíncrona como mensagem de WhatsApp ou fila de padaria com senha.
   - Docker como um contêiner de navio padronizado.
   - Hash de senha como um moedor de carne: não dá para "desmoer".
3. **Profundidade de verdade, no nível certo.** Explique o *porquê* e o *como funciona por dentro*, sem pular para "só copie este código". Exemplos de profundidade esperada:
   - O ciclo completo de uma requisição: DNS → TCP → TLS → HTTP → servidor WSGI/ASGI → middleware → URL → view → ORM → SQL → resposta.
   - O que o ORM gera de SQL, o problema N+1 e como resolvê-lo com `select_related`/`prefetch_related`.
   - Transações e propriedades ACID com um exemplo de transferência entre contas.
   - Por que `async` não deixa código "mais rápido", e sim melhor em esperar I/O. Diferença entre threads, processos e event loop (e o papel do GIL).
   - Sessão/cookie vs token JWT, com os riscos de cada um.
4. **Exemplo prático para CADA conceito.** Nenhum conceito fica só na teoria: cada um tem um trecho de código executável e curto, com a saída esperada.
5. **🧠 Pausas de lógica de programação.** Ao longo dos módulos de backend, insira caixas **"🧠 Pausa para lógica"** que usam um problema real do sistema para treinar lógica e algoritmos. Exemplos:
   - Paginação → aritmética de offset/limit e erros de "off-by-one".
   - Carrinho de compras → somatórios, arredondamento de dinheiro (`Decimal` vs `float`).
   - Busca de produtos → busca linear vs binária, e por que o banco usa índices.
   - Cache → dicionário/hash table e complexidade O(1).
   - Validação de CPF ou de senha forte → laços, condicionais e strings.
   - Ranking de mais vendidos → ordenação e `Counter`.
   - Detectar pedidos duplicados → `set` e idempotência.
   - Introdução a Big-O com exemplos medidos (`timeit`).
   
   Cada pausa tem o enunciado, uma dica em `<details>`, a solução comentada em `<details>` e uma variação mais difícil.
6. **Aprender fazendo.** Todas as aulas práticas terminam com um exercício que **evolui o projeto central** (seção 4) e tem critérios de "pronto" verificáveis.
7. **Mentalidade de mercado.** Inclua armadilhas comuns, boas práticas, como isso aparece no dia a dia de um time e **perguntas de entrevista júnior com respostas-modelo**.
8. **Texto direto.** Denso em conteúdo, sem frases motivacionais vazias. Use Mermaid para diagramas, tabelas para comparações e `<details>` para soluções.

## 3. Trilha (ordem de importância e de construção)

Use esta trilha como base. **Complete o que faltar** com o que a pesquisa de mercado (etapa 1.2) indicar como esperado de um júnior, mas mantenha a ordem de construção. Distribua as horas de forma realista e justifique no plano.

### Módulo 0 — Ambiente e ferramentas do dev
Terminal (Linux/WSL), sistema de arquivos e permissões, editor (VS Code) e debugger, instalação do Python, ambientes virtuais e gerenciador de pacotes (`venv`/`pip` e `uv`), **Git e GitHub** (commit, branch, merge, pull request, resolução de conflito, `.gitignore`), como ler documentação e mensagens de erro, como pesquisar e pedir ajuda.

### Módulo 1 — Python e lógica de programação
Tipos, variáveis, operadores, condicionais, laços, funções, escopo; estruturas de dados (list, tuple, dict, set) e quando usar cada uma; strings e f-strings; comprehensions; exceções; leitura e escrita de arquivos (txt, CSV, JSON); módulos e pacotes; **orientação a objetos** (classes, herança, composição, dataclasses, métodos especiais); type hints; iteradores e geradores; decorators e context managers (no nível de entender o que o framework faz); recursão; noções de Big-O; **testes com pytest desde aqui**. Exercícios de lógica progressivos em todo o módulo.

### Módulo 2 — Como a web funciona
Cliente-servidor, IP, DNS, portas, TCP, HTTP/HTTPS e TLS; métodos, status codes, headers, corpo; cookies e sessões; JSON; URLs e query strings; ferramentas (DevTools do navegador, `curl`, HTTPie/Postman/Bruno). Construir um **servidor HTTP mínimo com a biblioteca padrão** para ver o que o framework esconde.

### Módulo 3 — Bancos de dados relacionais
Por que usar banco em vez de arquivo; modelagem (entidades, relacionamentos 1:1, 1:N, N:N, diagrama ER); chaves primária e estrangeira; **normalização** (1FN a 3FN) e quando desnormalizar; **SQL** (DDL, DML, `SELECT`, `WHERE`, `JOIN`s, `GROUP BY`/`HAVING`, subqueries, `ORDER BY`/`LIMIT`); constraints; **índices** e `EXPLAIN`; **transações e ACID**; níveis de isolamento (visão geral); PostgreSQL na prática; acesso pelo Python (`psycopg`) e **SQL injection** já explicado aqui; ORM (o que é, vantagens e custos); migrações; noção de quando usar NoSQL (Redis, MongoDB) sem aprofundar.

### Módulo 4 — Front-end essencial para dev backend
HTML semântico, formulários, CSS básico (box model, flexbox, grid, responsividade), JavaScript essencial (tipos, funções, DOM, eventos, `fetch`, Promises/`async`/`await`), consumir uma API REST pelo navegador. Visão geral de frameworks (React/Vue) e de HTMX, só para o aluno saber o que são e conversar sobre eles. Acessibilidade básica.

### Módulo 5 — Framework web: Django
Estrutura de projeto e apps; **padrão MVC e a variação MVT do Django**; ciclo de vida da requisição; URLs, views (função e classe), templates; models e ORM (consultas, relacionamentos, agregações, N+1); migrações; formulários e validação; Django Admin; autenticação e permissões nativas; arquivos estáticos e de mídia; configurações por ambiente (variáveis de ambiente, `.env`); logging; paginação.

### Módulo 6 — APIs REST
Princípios REST (recursos, verbos, status codes, idempotência, statelessness); design de endpoints e convenções de nomes; **Django REST Framework** (serializers, viewsets, routers, validação, permissões, autenticação por token/JWT, filtros, paginação, throttling); versionamento; tratamento de erros padronizado; **documentação com OpenAPI/Swagger**; CORS; testes de API. Comparação breve com GraphQL e gRPC (só conceito).

### Módulo 7 — Comunicação síncrona e assíncrona
Bloqueante vs não bloqueante; I/O-bound vs CPU-bound; **threads, processos, asyncio e o GIL**; `async`/`await` na prática (com `httpx`); WSGI vs ASGI; **filas e tarefas em segundo plano** (Celery ou RQ com Redis), retentativas e idempotência; agendamento de tarefas; **webhooks**; noção de mensageria (RabbitMQ/SQS) e de eventos; WebSockets (conceito e um exemplo simples); timeouts e retentativas ao chamar APIs externas.

### Módulo 8 — Estrutura de projetos e arquitetura
Organização de código e separação de responsabilidades; **MVC/MVT**; arquitetura em camadas (views, services, repositories); princípios **SOLID**, DRY, KISS e YAGNI aplicados a Python; padrões de projeto mais úteis para um júnior (Strategy, Factory, Repository, Adapter); **monólito vs monólito modular vs microsserviços**, com prós, contras e quando cada um faz sentido; comunicação entre serviços (REST vs mensageria); twelve-factor app; leitura de código legado e refatoração segura.

### Módulo 9 — Segurança
**OWASP Top 10** com exemplos práticos de ataque e defesa no próprio projeto: SQL injection, XSS, CSRF, quebra de controle de acesso (IDOR), falhas de autenticação. Também: hash de senhas (bcrypt/Argon2, nunca MD5/SHA puro), autenticação vs autorização, sessão vs JWT, HTTPS, CORS, gestão de segredos (nunca no Git), validação de entrada, rate limiting, dependências vulneráveis (`pip-audit`), princípio do menor privilégio, cabeçalhos de segurança, LGPD básica para devs.

### Módulo 10 — Qualidade, testes e boas práticas
Pirâmide de testes; pytest a fundo (fixtures, parametrize, mocks); testes de unidade, integração e API; cobertura; TDD (introdução); linters e formatadores (ruff), checagem de tipos (mypy); pre-commit; code review (como dar e receber); padrões de commit (Conventional Commits); README bem escrito.

### Módulo 11 — Docker e containers
Problema que o Docker resolve; imagem vs container; **Dockerfile** para uma app Django (camadas, cache, imagem slim, usuário não root); **Docker Compose** com app + PostgreSQL + Redis + worker; volumes, redes, variáveis de ambiente; logs e depuração dentro do container; `.dockerignore`; servidor de produção (Gunicorn/Uvicorn) atrás de um proxy reverso (Nginx), em visão geral.

### Módulo 12 — CI/CD
Integração e entrega contínuas; **GitHub Actions** rodando lint, testes e build da imagem a cada pull request; ambientes (dev, staging, produção); estratégia de deploy simples.

### Módulo 13 — Introdução à nuvem com AWS
Conceitos de nuvem (IaaS, PaaS, SaaS, regiões, zonas de disponibilidade, responsabilidade compartilhada); **configurar alerta de custos e MFA antes de tudo**; IAM (usuários, papéis, políticas, menor privilégio); EC2; RDS (PostgreSQL gerenciado); S3 (arquivos de mídia); Security Groups e noção de VPC; **deploy do projeto** (EC2 com Docker Compose, ou uma opção gerenciada como ECS/App Runner/Lightsail, justificando a escolha pelo custo); variáveis e segredos (Parameter Store/Secrets Manager); CloudWatch Logs; **como destruir tudo ao final para não gerar cobrança**. Infraestrutura como código só mencionada (Terraform/CDK), sem aprofundar.

### Módulo 14 — Produção e observabilidade básica
Logs estruturados; health checks; métricas básicas; monitoramento de erros (ex.: Sentry); cache com Redis (TTL, invalidação); performance (consultas lentas, índices, paginação); backups.

### Módulo 15 — FastAPI (comparativo)
Reimplementar uma pequena parte da API do projeto com **FastAPI + SQLAlchemy + Pydantic**, para comparar com Django/DRF: tipagem, validação, async nativo, injeção de dependências e documentação automática. Tabela "quando escolher cada um".

### Módulo 16 — Pronto para o mercado
Portfólio no GitHub (README em português e inglês, prints, como rodar, decisões técnicas); currículo e LinkedIn para júnior; **preparação para entrevistas** (perguntas técnicas comuns de Python, banco, web, Git e Docker; exercícios de lógica no nível de entrevista júnior; como explicar o próprio projeto); desafio técnico simulado (take-home) com tempo limite; como continuar estudando depois.

## 4. Projeto central (fio condutor)

Todo o treinamento constrói, aos poucos, **um único sistema real**: uma **loja virtual simples ("MiniShop")** com catálogo de produtos, categorias, busca e paginação, cadastro e login de usuários, carrinho, pedidos com controle de estoque (transação), painel administrativo, pagamento **simulado** via webhook, **e-mail de confirmação enviado de forma assíncrona** por uma fila, API REST documentada, um front-end simples consumindo a API, container com Docker Compose, CI no GitHub Actions e deploy na AWS.

- Defina o domínio, as entidades e os nomes **uma única vez** em `00-guia/projeto-central.md` (com diagrama ER e diagrama de arquitetura em Mermaid) e mantenha-os iguais em todas as aulas.
- Em `projeto/marcos.md`, descreva o que o projeto deve ter ao fim de cada módulo (marco = tag no Git).
- Os módulos 1 a 4 podem ter mini-projetos próprios (CLI de estoque, servidor HTTP mínimo, banco da loja em SQL puro, página estática consumindo uma API pública) que **depois são reaproveitados** no MiniShop.
- Inclua **dados de exemplo** (seed) para o aluno não perder tempo cadastrando dados.

## 5. Template obrigatório de cada aula

```markdown
# <Número>. <Título>

> ⏱️ ~<tempo> · Módulo X · Pré-requisitos: <aulas>

## 🎯 Objetivos
Ao final desta aula você consegue: (3 a 5 verbos de ação mensuráveis)

## 🤔 Por que isso importa
Que problema real isso resolve e onde aparece no trabalho de um dev júnior.

## 💡 Intuição (explicação simples)
Analogia do cotidiano. Sem jargão.

## 🔬 Como funciona por dentro
Explicação técnica e precisa. Diagrama Mermaid quando ajudar.

## 🛠️ Exemplo prático
Código completo, curto e comentado, com o comando para rodar e a saída esperada.
Um exemplo para cada conceito introduzido na aula.

## 🧠 Pausa para lógica (quando fizer sentido)
Problema de lógica tirado do contexto da aula. Dica e solução em <details>.

## ⚠️ Erros comuns e boas práticas
Inclua mensagens de erro reais que o aluno vai encontrar e como resolvê-las.

## 🧩 Exercícios
1. Fixação (rápido)
2. Aplicação no projeto MiniShop, com critérios de pronto em checklist
3. Desafio (opcional)
Soluções de referência em <details>, fechadas por padrão.

## 🎤 Na entrevista
2 a 3 perguntas que costumam cair para júnior, com respostas-modelo curtas.

## 📚 Para ir além
- 📄 Documentação oficial: ...
- 🎥 Vídeo (PT-BR e/ou EN): ... (canal, duração aproximada)
- 📑 Artigo/tutorial: ...
- 🏋️ Prática extra: ...

## ✅ Checklist da aula
- [ ] ...
```

## 6. Estrutura de pastas e arquivos

```
./
├── README.md                    # Visão geral, como usar, mapa da trilha (diagrama Mermaid)
├── 00-guia/
│   ├── cronograma.md            # Sessões dia a dia com checkbox [ ], semanas e marcos
│   ├── setup-ambiente.md        # Instalação de tudo, por sistema operacional
│   ├── versoes.md
│   ├── o-que-o-mercado-pede.md
│   ├── projeto-central.md
│   ├── como-estudar.md          # Método: ler, rodar, quebrar, consertar, explicar
│   └── glossario.md
├── 00-ambiente-ferramentas/
├── 01-python-logica/
├── 02-como-a-web-funciona/
├── 03-banco-de-dados/
├── 04-front-end-essencial/
├── 05-django/
├── 06-apis-rest/
├── 07-sincrono-assincrono/
├── 08-arquitetura/
├── 09-seguranca/
├── 10-qualidade-testes/
├── 11-docker/
├── 12-ci-cd/
├── 13-aws/
├── 14-producao-observabilidade/
├── 15-fastapi-comparativo/
├── 16-pronto-para-o-mercado/
├── recursos/
│   ├── biblioteca.md            # Todos os links por tema, com data da verificação
│   ├── perguntas-entrevista.md  # Banco consolidado de perguntas e respostas-modelo
│   ├── exercicios-logica.md     # Todas as pausas de lógica + lista extra por dificuldade
│   └── cheatsheets/             # Git, SQL, Django ORM, DRF, HTTP status, Docker, AWS CLI, pytest
└── projeto/
    └── marcos.md
```

Cada pasta de módulo contém um `README.md` (objetivos, aulas com tempo, entrega do projeto, conexão com o próximo módulo), as aulas numeradas (`01-<tema>.md`, `02-<tema>.md`...) e um `checkpoint.md` (quiz de 10 questões com gabarito em `<details>`, entrega prática e autoavaliação).

## 7. Regras para links e referências (muito importante)

- **Nunca invente URLs.** Todo link precisa ser verificado na web antes de entrar no material. Se não der para confirmar, não inclua (ou marque como `⚠️ não verificado`).
- Priorize **fontes primárias e reconhecidas**: docs.python.org, docs.djangoproject.com, django-rest-framework.org, fastapi.tiangolo.com, postgresql.org/docs, developer.mozilla.org (MDN), docs.docker.com, docs.github.com, docs.aws.amazon.com, owasp.org, docs.pytest.org, realpython.com, roadmap.sh.
- **Vídeos:** prefira canais e cursos conhecidos e gratuitos, em PT-BR e em EN (ex.: Curso em Vídeo, Eduardo Mendes/Live de Python, freeCodeCamp, Corey Schafer, CS50 de Harvard, Fireship para visões rápidas, AWS oficial). Informe o canal e a duração aproximada.
- Em cada link, escreva **uma linha dizendo por que vale a pena** e o que olhar nele.
- Consolide tudo em `recursos/biblioteca.md`.

## 8. Qualidade e consistência

- **Rode o código.** Execute os exemplos e as soluções que não dependem de conta na nuvem (use Docker para PostgreSQL e Redis). Se algo não puder ser testado, deixe isso explícito na aula.
- Os exemplos de segurança mostram **o código vulnerável e o corrigido lado a lado**, sempre em ambiente local.
- Na parte de AWS, todo passo que pode gerar custo traz um aviso **💸** e a forma de desfazer.
- Mantenha nomes, estrutura de pastas do projeto e estilo de código consistentes em todo o treinamento.
- A dificuldade cresce aos poucos. Se uma aula precisar de mais de 2 sessões, divida em parte 1 e parte 2.

## 9. Forma de trabalho

1. Faça a pesquisa de versões e de mercado (seção 1) e crie `README.md`, a pasta `00-guia/` completa e os `README.md` de todos os módulos (com lista de aulas e horas).
2. **Pare e me mostre** o índice geral, a carga horária total, o cronograma e o que você acrescentou à trilha com base na pesquisa de mercado. Aguarde minha aprovação.
3. Depois da aprovação, gere **um módulo por vez**, na ordem. Ao terminar cada um, atualize `recursos/` (biblioteca, perguntas de entrevista, exercícios de lógica, cheatsheets), o `glossario.md` e o `projeto/marcos.md`, e me dê um resumo curto do que foi criado.
4. Ao final, faça uma revisão geral: links quebrados, ordem de pré-requisitos (nenhum conceito usado antes de ser ensinado), consistência de nomes, soma das horas e uma tabela **"competência exigida de um júnior → aula(s) que cobrem"**.
