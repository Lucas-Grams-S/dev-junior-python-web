# 02. Currículo e LinkedIn para júnior

> ⏱️ ~1h30 · Módulo 16 · Pré-requisitos: aula 01

## 🎯 Objetivos
Ao final desta aula você consegue:
- Montar um currículo de 1 página para vaga júnior, com projeto no topo
- Escrever bullets com **ação + tecnologia + resultado verificável**
- Ajustar o currículo a uma vaga sem mentir
- Configurar título, "Sobre" e destaques do LinkedIn
- Abordar uma pessoa da empresa com uma mensagem curta

## 🤔 Por que isso importa
Filtros (humanos e automáticos) leem o currículo em segundos. Sem emprego anterior na área, o **projeto** é a experiência. E tudo que está escrito pode virar pergunta na entrevista: exagero custa caro.

## 💡 Intuição (explicação simples)
O currículo é um **resumo executivo**, não uma biografia. Cada linha responde: "por que vale 30 minutos de conversa?". O LinkedIn é o mesmo texto, em formato que a busca de recrutadores encontra.

## 🔬 Como funciona por dentro
Estrutura (1 página, PDF, texto selecionável — sem tabelas complexas nem colunas que quebram leitores automáticos):

1. Cabeçalho: nome, cargo-alvo, cidade/modalidade, e-mail, GitHub, LinkedIn.
2. Resumo (2–3 linhas).
3. **Projeto em destaque** (acima de formação, se você não tem experiência).
4. Habilidades — só o que você consegue **demonstrar** no repositório.
5. Experiência (qualquer trabalho relevante, estágio, voluntariado) e Formação.

Fórmula do bullet: **verbo + o que + tecnologia + prova**.

| Fraco | Forte |
|---|---|
| "Responsável pelo backend" | "Implementei a baixa de estoque transacional (Django, PostgreSQL) e testei a concorrência com 2 pedidos simultâneos" |
| "Conhecimento avançado em Docker" | "Containerizei a API com Docker Compose (Nginx, worker, PostgreSQL, Redis); imagem final de 452 MB" |
| "Usei testes" | "341 testes (pytest) e CI no GitHub Actions rodando em SQLite e PostgreSQL" |

> Esses números vêm dos marcos dos módulos 11, 12 e 14 **deste curso**; use os do seu repositório.

Habilidades: três níveis honestos — *uso no dia a dia*, *já usei em projeto*, *noções*. FastAPI e AWS entram como "noções/projeto" (o curso usou só uma fatia de FastAPI e simulador da AWS: **diga isso**).

IA assistida: se usou, assuma ("usei IA para revisar e gerar rascunhos; entendo e testo o que entrego"). A entrevista vai medir isso.

## 🛠️ Exemplo prático
Modelos em [`portfolio/curriculo-modelo.md`](../projeto/referencia-m16/portfolio/curriculo-modelo.md) e [`portfolio/linkedin-modelo.md`](../projeto/referencia-m16/portfolio/linkedin-modelo.md).

Ajustar a uma vaga: leia os requisitos das vagas que **você** escolheu. O curso traz uma análise de 40 vagas em `recursos/ferramentas/saida/` e o script que a gerou (`recursos/ferramentas/buscar_vagas.py`; ele usa endpoints públicos não oficiais do LinkedIn, cujos termos restringem coleta automatizada: só para pesquisa pessoal, em volume baixo, e pare se vier HTTP 429; **não o reexecutei nesta aula**). Depois, para cada vaga: (a) reordene as habilidades para a ordem pedida; (b) escolha 2 bullets do projeto que provem os requisitos; (c) **não** adicione tecnologia que você não usou.

LinkedIn, pontos que mais pesam: foto simples, **título com tecnologias** (não "Em busca de oportunidades"), "Sobre" em 3 parágrafos curtos, projeto em "Destaques" com link do GitHub, habilidades (≤ 15) alinhadas às vagas, perfil em português e a seção de inglês honesta. Mensagem a recrutador(a): ≤ 300 caracteres, vaga específica, link do projeto, pedido claro.

## 🧠 Pausa para lógica
Uma vaga pede "Django, PostgreSQL, Docker, AWS e Kafka". Você tem os quatro primeiros (AWS só em simulador) e nunca viu Kafka. Em que ordem e com que palavras você os lista?
<details><summary>Solução</summary>

Primeiro o que você domina (Django, PostgreSQL, Docker). AWS: "noções (EC2/RDS/S3/IAM, praticado em simulador local)". Kafka: não liste; na carta/mensagem diga "conheço filas com Celery/Redis e aprendo Kafka". Honestidade selecionada, não mentira.
</details>

## ⚠️ Erros comuns e boas práticas
- Barras de proficiência ("Python 90%"): não significam nada e viram pergunta.
- Currículo de 3 páginas, foto grande, CPF/endereço completo (dados desnecessários).
- Links quebrados ou repositório privado listado como "projeto público". **Abra seus links numa janela anônima.**
- Mentir tecnologia: "Kubernetes" porque estava na vaga. Na primeira pergunta o currículo desmorona.
- Mesmo currículo para todas as vagas, sem ajuste.

## 🧩 Exercícios
1. **(Fixação)** Reescreva 3 bullets fracos seus com a fórmula da aula.
2. **(Aplicação no MiniShop)** Currículo de 1 página + LinkedIn.
   - [ ] PDF de 1 página, texto selecionável
   - [ ] Projeto no topo, com link que abre em janela anônima
   - [ ] Cada habilidade citada tem prova no repositório
   - [ ] Título do LinkedIn com tecnologias
   - [ ] Pedi a uma pessoa para ler em 30 s e dizer o que entendeu
3. **(Desafio)** Faça 3 versões (back-end Django, API FastAPI, geral) e justifique as diferenças em 5 linhas.

## 🎤 Na entrevista
**"Seu currículo diz X; me mostre."** Tenha o trecho de código aberto. **"Qual foi sua contribuição?"** (projeto de curso é solo; diga com clareza o que foi guiado e o que foi decisão sua.) **"Por que mudou de área?"** História curta, sem pedir desculpas.

## 📚 Para ir além
- 📄 [GitHub — Fixar itens no perfil](https://docs.github.com/pt/account-and-profile/setting-up-and-managing-your-github-profile/customizing-your-profile/pinning-items-to-your-profile) (HTTP 200 em 2026-11-09)
- 📄 [backend-br/vagas](https://github.com/backend-br/vagas): vagas reais de back-end para ler requisitos e ver como as descrições são escritas (HTTP 200 em 2026-11-09)
- 🏋️ Prática extra: peça revisão do currículo a duas pessoas da área e compare os comentários.

## ✅ Checklist da aula
- [ ] Currículo em PDF (1 página) e versão ajustada a uma vaga real
- [ ] LinkedIn com título, "Sobre" e projeto em destaque
- [ ] Todos os links testados em janela anônima
