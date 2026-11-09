# ADR 0003: Configuração e segredos no ambiente (twelve-factor)

Status: aceito · Data: 2026-11-08

## Contexto
`SECRET_KEY`, `DEBUG` e o banco estavam fixos no código, e a suíte só rodava em SQLite.

## Decisão
Ler `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` e `DATABASE_URL` do ambiente (`config/envconf.py`, sem dependência extra). `DEBUG` padrão `False`; sem `SECRET_KEY` e com `DEBUG=False` o processo **não sobe**. Logs em stdout. A suíte roda em SQLite e PostgreSQL.

## Alternativas
`django-environ`/`dj-database-url`: aceitáveis, mas o parser é pequeno e testado aqui. Arquivo `.env` lido em produção: rejeitado (segredos no disco).

## Consequências
+ `check --deploy` caiu de 7 para 2 avisos. + Achados de paridade corrigidos (sequências, limites do OpenAPI).
− Dois avisos conscientes (HSTS de subdomínios e *preload*) dependem do domínio.

## Quando rever
Ao adotar um cofre de segredos ou um orquestrador com injeção própria.
