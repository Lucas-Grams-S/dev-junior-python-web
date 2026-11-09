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
