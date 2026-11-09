# O que o mercado pede de um(a) dev júnior Python web

> Pesquisa em 2026-11-07. Fontes: [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/2025/technology), [JetBrains Python Developers Survey 2024](https://lp.jetbrains.com/python-developers-survey-2024/), [roadmap.sh/python](https://roadmap.sh/python). ⚠️ Amostra de vagas reais muito pequena (ver seção final); pesquisa JetBrains 2025 não analisada.

## Dados
| Tema | Dado | Fonte | Decisão no curso |
|---|---|---|---|
| Python | 57,9% dos respondentes; 71,8% entre quem está aprendendo | SO 2025 | Linguagem certa para começar. |
| Frameworks (Python) | JetBrains 2024: FastAPI 38%, Django 35%, Flask 34%. SO 2025: FastAPI 14,8%, Flask 14,4%, Django 12,6% | JB/SO | Django+DRF segue como principal (pedido nas vagas BR, a confirmar na amostragem); FastAPI sobe para módulo próprio e Flask ganha menção no comparativo. |
| Banco | PostgreSQL 55,6% (SO) / 49% (JB), líder nos dois | SO/JB | PostgreSQL confirmado. |
| Redis | 28% (SO), +8 pontos | SO | Redis aparece cedo: cache, fila e Celery. |
| Docker | 71,1%, maior salto do ano (+17 pts) | SO | Docker é praticamente obrigatório; Módulo 11 é central. |
| Cloud | AWS 43,3% | SO | AWS confirmada. |
| Testes | pytest 53%; 36% não usam framework de testes | JB | pytest desde o Módulo 1; testar é diferencial de júnior. |
| Uso principal | Web dev é o uso nº 1 de Python (23%) | JB | |
| Roadmap | Git, SQL, REST, autenticação, estruturas de dados, deploy/cloud, projetos de portfólio; roadmap.sh não cita testes | roadmap.sh | Confirma a trilha. |

## O que acrescentei à trilha original
1. **Metodologias ágeis, trabalho em time e uso responsável de IA assistida** (Módulo 10, aula 07) e “IA como ferramenta de estudo” no Módulo 0: júnior hoje usa IA no dia a dia; entrevistas testam se você entende o código gerado.
2. **Pydantic e validação por tipos** no Módulo 1 (type hints) e reforçado no 15, pois FastAPI lidera as pesquisas.
3. **Flask** como menção conceitual no comparativo (Módulo 15), sem implementar.
4. **Inglês técnico**: glossário bilíngue e leitura de documentação em inglês desde o Módulo 0.
5. **Nota de migração Django 5.2 → 6.2 LTS** (lançamento em abril/2027).
6. **Pandas/NumPy ficam de fora** de propósito: pertencem à trilha de dados, não à de web júnior.

## Competências esperadas (resumo)
Python sólido + OO · Git/GitHub · SQL e modelagem · Django/DRF · REST · testes · Docker · noções de CI e nuvem · segurança básica · comunicação e leitura de código.

---

## Amostra de vagas reais (2026-11-07)

> ⚠️ **Amostra inicial muito pequena (2 anúncios), superada pela amostra LinkedIn de 40 vagas ao final deste arquivo.** O LinkedIn bloqueia acesso automatizado (HTTP 429), e Indeed (403) e ProgramaThor (404) também falharam. Os dois anúncios vieram do [backend-br/vagas](https://github.com/backend-br/vagas) e do BairesDev. Trate como ilustração, não como estatística. Para uma amostra válida, cole aqui 10–20 descrições de vagas do LinkedIn.

| Vaga | Pilha pedida | Observações |
|---|---|---|
| [Back-end Júnior Python / AI Coding, MKdigital](https://github.com/backend-br/vagas/issues/12493) (remoto) | Python, **FastAPI**, PostgreSQL/SQL, Linux, Docker, Git, CI/CD, **testes automatizados**; TypeScript/JS/React como extra | Superior concluído ou em fase final; inglês técnico desejável; usa ferramentas de IA para codar. Sem Django/AWS. |
| [Backend Júnior Python, BairesDev](https://talent.bairesdev.com/pt/vagas/desenvolvedor-backend-junior-python-remote) (remoto) | Python, **Django**, bancos relacionais (Oracle/MS SQL/MySQL), XML | **1+ ano** de Python/Django, POO, algoritmos e estruturas de dados, **inglês avançado**. |

Trechos de outras buscas (sem acesso ao anúncio completo): POO, APIs REST, Git e bancos relacionais aparecem com frequência; diferenciais citados são portfólio no GitHub, testes unitários e Scrum.

## Perfil-alvo (o que o curso mira ao final)
Quem terminar deve conseguir dizer “sim” a:
- [ ] Python + POO + estruturas de dados e algoritmos básicos
- [ ] Django **e** FastAPI (o curso cobre os dois)
- [ ] SQL e PostgreSQL (modelagem, JOINs, índices)
- [ ] API REST com autenticação, documentação e testes automatizados
- [ ] Git/GitHub, Linux, Docker, CI/CD básico
- [ ] Inglês técnico (leitura de docs) e, idealmente, conversação
- [ ] Portfólio no GitHub com o MiniShop no ar

## Impacto no plano
1. **Testes automatizados** aparecem como requisito explícito: já começam no Módulo 1 e a meta de cobertura fica em ≥ 80% (Módulo 10).
2. **FastAPI pede-se junto com Django** em vagas reais: o Módulo 15 passa a ser tratado como parte do alvo, não como extra. Recomendo manter as 5 sessões.
3. **Inglês**: vamos reservar 10 min por aula de leitura de docs em inglês e incluir perguntas de entrevista em inglês no Módulo 16.
4. **Vagas “júnior” pedem 1+ ano**: o portfólio e o projeto substituem a experiência; o Módulo 16 foca em como apresentá-lo.

---

## Amostra LinkedIn (coletada em 2026-11-07, 40 vagas)

Script: `recursos/ferramentas/buscar_vagas.py`. Dados brutos em `recursos/ferramentas/saida/`. Percentual = vagas que citam o termo (busca por palavra-chave, sujeita a falsos positivos). Isto **substitui** a amostra de 2 vagas acima.

| Tecnologia | A: “python junior” (20) | B: “desenvolvedor backend python” (20) |
|---|---|---|
| Python | 100% | 100% |
| REST/API | 40% | **80%** |
| SQL / PostgreSQL | 75% / 20% | 25% / 45% |
| Git | 60% | 45% |
| Docker | 10% | **50%** |
| FastAPI | 10% | **50%** |
| Django | 5% | 45% |
| Flask | 5% | 25% |
| AWS | 35% | 45% |
| Azure / GCP | 30% / 15% | 35% / 20% |
| Testes | 40% | 40% |
| CI/CD | 15% | 35% |
| Redis / Celery | 10% / 0% | 25% / 15% |
| Microsserviços | 10% | 50% |
| Kubernetes | 5% | 40% |
| SOLID/Patterns | 10% | 40% |
| Inglês | 40% | 45% |
| IA/LLM | 80% | 45% |

### Limitações (importante)
- **A** (“python junior”): ~metade das vagas é de **dados/analytics** (cientista, engenheiro, analista de dados). Só ~8–9 são de desenvolvimento. Por isso SQL e IA aparecem tanto.
- **B** (“backend python”): quase todas são **pleno/sênior**; o filtro de júnior do LinkedIn não se manteve. Docker, Kubernetes e microsserviços estão **superestimados** para o nível júnior.
- Leitura honesta: A mostra o piso (Python, SQL, Git, testes, APIs); B mostra o teto do que se espera ao crescer.

### Conclusões para o curso
1. **FastAPI e Django aparecem juntos** (50% e 45% nas vagas de backend). Confirma manter os dois; FastAPI deixa de ser “extra”. **Proposta:** ampliar o Módulo 15 de 5 para 7 sessões (pelo menos uma aula de FastAPI com async e dependências a mais).
2. **REST/API é quase universal** (80% em backend): Módulo 6 está bem dimensionado.
3. **Docker (50%) e AWS (45%)** confirmam os Módulos 11 e 13. Docker em vaga júnior ficou em 10% na amostra A, então é diferencial, não filtro.
4. **Kubernetes (40% no sênior):** só mencionar em “para ir além” (Módulo 11), sem aula.
5. **Azure e GCP** aparecem tanto quanto AWS em algumas vagas: incluir no Módulo 13 uma aula curta de “equivalências AWS ↔ Azure ↔ GCP” (nomes dos serviços), sem prática.
6. **Testes em 40%** nas duas amostras: já alinhado.
7. **IA/LLM aparece muito (80% em A, mas inflado pelas vagas de dados)**: manter a aula de IA assistida; **não** adicionar módulo de IA.
8. **SQL** é central nas vagas de entrada (75%): reforçar com mais exercícios de SQL no Módulo 3.
9. **Inglês em ~40–45%**: confirma o plano de leitura de docs em inglês e perguntas de entrevista em inglês.
10. **Fora do escopo, mas citados:** Kafka/RabbitMQ (15%), Go, Databricks. Só menção conceitual, já prevista no Módulo 7.
