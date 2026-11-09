# Competência exigida de um(a) júnior → onde o curso cobre

> Revisão final (2026-11-09). Fonte das competências: [`o-que-o-mercado-pede.md`](o-que-o-mercado-pede.md). Links para o módulo; a coluna "Aulas-chave" aponta onde praticar.

| Competência | Módulo | Aulas-chave | Prova (checkpoint) |
|---|---|---|---|
| Python sólido, lógica e Big-O | [1](../01-python-logica/README.md) | [Dicts/sets](../01-python-logica/06-dicts-sets.md), [Geradores](../01-python-logica/15-iteradores-geradores.md), [Recursão e Big-O](../01-python-logica/17-recursao-big-o.md) | [M1](../01-python-logica/checkpoint.md) |
| POO e type hints | [1](../01-python-logica/README.md) | [Classes](../01-python-logica/12-poo-classes.md), [Hints](../01-python-logica/14-metodos-especiais-type-hints.md) | [M1](../01-python-logica/checkpoint.md) |
| Git/GitHub e terminal | [0](../00-ambiente-ferramentas/README.md), [10](../10-qualidade-testes/README.md), [16](../16-pronto-para-o-mercado/README.md) | [Code review e commits](../10-qualidade-testes/06-code-review-commits-readme.md), [Git na entrevista](../16-pronto-para-o-mercado/04-entrevista-banco-web-git-docker.md) | [M0](../00-ambiente-ferramentas/checkpoint.md) |
| HTTP e web | [2](../02-como-a-web-funciona/README.md) | DevTools e `curl` | [M2](../02-como-a-web-funciona/checkpoint.md) |
| SQL e modelagem | [3](../03-banco-de-dados/README.md) | [Joins](../03-banco-de-dados/05-joins.md), [Índices e EXPLAIN](../03-banco-de-dados/08-constraints-indices-explain.md), [Transações](../03-banco-de-dados/09-transacoes-acid.md) | [M3](../03-banco-de-dados/checkpoint.md) |
| Front-end básico | [4](../04-front-end-essencial/README.md) | página consumindo API | [M4](../04-front-end-essencial/checkpoint.md) |
| Django | [5](../05-django/README.md) | [Templates](../05-django/03-templates.md), [Carrinho](../05-django/16-carrinho.md) | [M5](../05-django/checkpoint.md) |
| APIs REST/DRF e OpenAPI | [6](../06-apis-rest/README.md) | [Versionamento e OpenAPI](../06-apis-rest/10-versionamento-openapi.md) | [M6](../06-apis-rest/checkpoint.md) |
| Assíncrono, filas e tempo real | [7](../07-sincrono-assincrono/README.md) | Celery, WebSocket | [M7](../07-sincrono-assincrono/checkpoint.md) |
| Arquitetura e padrões | [8](../08-arquitetura/README.md) | [Services e repositories](../08-arquitetura/02-services-repositories.md) | [M8](../08-arquitetura/checkpoint.md) |
| Segurança web (OWASP, auth, LGPD) | [9](../09-seguranca/README.md) | [Injection/XSS](../09-seguranca/02-injection-xss.md), [IDOR](../09-seguranca/05-controle-acesso-idor.md) | [M9](../09-seguranca/checkpoint.md) |
| Testes e qualidade | [10](../10-qualidade-testes/README.md) | [Pirâmide](../10-qualidade-testes/01-piramide-fixtures.md), [TDD](../10-qualidade-testes/04-tdd.md) | [M10](../10-qualidade-testes/checkpoint.md) |
| Docker | [11](../11-docker/README.md) | Dockerfile multi-stage, Compose | [M11](../11-docker/checkpoint.md) |
| CI/CD | [12](../12-ci-cd/README.md) | GitHub Actions | [M12](../12-ci-cd/checkpoint.md) |
| Nuvem (AWS) | [13](../13-aws/README.md) | IAM, EC2, RDS, S3 (**simulador**, 💸 conta real opcional) | [M13](../13-aws/checkpoint.md) |
| Produção e observabilidade | [14](../14-producao-observabilidade/README.md) | [Logs e health](../14-producao-observabilidade/01-logs-estruturados-health.md) | [M14](../14-producao-observabilidade/checkpoint.md) |
| FastAPI (e escolha de framework) | [15](../15-fastapi-comparativo/README.md) | [Comparativo](../15-fastapi-comparativo/06-comparativo-quando-escolher.md) | [M15](../15-fastapi-comparativo/checkpoint.md) |
| Portfólio, currículo e entrevista | [16](../16-pronto-para-o-mercado/README.md) | [README](../16-pronto-para-o-mercado/01-portfolio-readme.md), [Lógica](../16-pronto-para-o-mercado/05-logica-nivel-entrevista.md), [Take-homes](../16-pronto-para-o-mercado/06-take-home-1.md) | [M16](../16-pronto-para-o-mercado/checkpoint.md) |
| Comunicação, ágil e IA assistida | [10](../10-qualidade-testes/README.md) | [Ágil e IA](../10-qualidade-testes/07-agil-ia-assistida.md) | [M10](../10-qualidade-testes/checkpoint.md) |

## Lacunas conhecidas (honestas)
- **AWS:** praticada só em simulador (`moto`); a conta real é opcional e não foi usada.
- **Sentry/Prometheus/Grafana:** configuração testada com dublês; sem conta/servidor reais.
- **FastAPI:** uma fatia do catálogo; sem JWT, pedidos, Docker/CI próprios.
- **Front-end:** o suficiente para consumir a API; não há trilha de framework JS.
- **Vagas:** a análise de mercado usa uma amostra pequena (40 vagas); trate como indício.
