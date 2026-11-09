# Relatório de segurança do MiniShop (módulo 9)

Escopo: o próprio laboratório local do MiniShop (API Django/DRF, admin, Celery, PostgreSQL/SQLite). Nenhum sistema de terceiros foi testado. Data: 2026-11-08. Lista de referência: **OWASP Top 10:2025**.

## Resumo
| Medida | Antes (aula 1) | Depois (aula 7) |
|---|---|---|
| Sondagens da auditoria (`scripts/m9/auditoria.py`) | 14 OK · **3 FALHA** · 6 atenção · 1 não medido | **19 OK · 0 FALHA** · 4 atenção · 1 não medido |
| `manage.py check --deploy` (produção simulada) | 7 avisos | 2 avisos conscientes (HSTS subdomínios e *preload*) |
| `pip-audit` (124 pacotes travados) | não executado | **nenhuma vulnerabilidade conhecida** (ferramenta validada contra pacotes antigos: 75 achados) |
| `ruff` regras `S` / `bandit` | não executado | sem achados (um valor fixo de chave de desenvolvimento foi removido) |
| Suíte de testes | 147 (146 passam em SQLite) | **235 passam em SQLite · 232 em PostgreSQL** |

## Achados, correções e provas
| ID | OWASP | Achado | Evidência | Correção | Teste que impede a volta | Estado |
|---|---|---|---|---|---|---|
| S-01 | A05 | Busca montada por texto em SQL cru (legado, aula 8.07) | `ruff S608`, `bandit B608` | consultas parametrizadas / ORM | `tests/test_sqli_defesa.py`, `tests/test_pontos_perigosos.py` | corrigido |
| S-02 | A05 | Risco de XSS por `mark_safe` / `\|safe` no futuro | guarda por mutação | autoescape do Django; guarda de construções perigosas; CSP restritiva | `tests/test_pontos_perigosos.py` | prevenido |
| S-03 | A07 | Sem validadores de senha (aceitava `123`) | auditoria A07 | `AUTH_PASSWORD_VALIDATORS` (mínimo 12, comuns, numéricas, similaridade) | `tests/test_senhas.py` | corrigido |
| S-04 | A04 | Hash de senha PBKDF2 (padrão) | auditoria A04 | Argon2id primeiro; PBKDF2 só verifica as antigas, regravadas no login | `tests/test_senhas.py` | corrigido |
| S-05 | A02 | Faltavam CSP e Permissions-Policy; `X-Frame-Options` só em produção | auditoria A02 | `config/security_headers.py` + `X_FRAME_OPTIONS` em todos os ambientes | `tests/test_endurecimento.py` | corrigido |
| S-06 | A02 | `/demo/*`, `/api/docs`, `/api/schema` públicos em produção | auditoria A02 (200) | ligados por decisão (`DEBUG`, `EXPOSE_DOCS`); `ADMIN_URL` configurável | `tests/test_endurecimento.py` (processo em modo produção) | corrigido |
| S-07 | A09 | Login falho não registrava quem tentou | auditoria A09 | eventos `login_failed`, `access_denied`, `rate_limited`; sanitização contra *log injection*; sem senhas | `tests/test_endurecimento.py` | corrigido |
| S-08 | A10 | Apagar produto já vendido gerava `ProtectedError` (500) | matriz de autorização | `409 Conflict` com `code: in_use` | `tests/test_matriz_autorizacao.py` | corrigido |
| S-09 | A01 | IDOR em pedidos, pagamento e carrinho | matriz papel × ação × dono | consulta base restrita ao dono; `IsOwner` no cancelamento | `tests/test_matriz_autorizacao.py` (39 casos, 3 mutações detectadas) | sem falha encontrada; protegido por teste |
| S-10 | A02 | `seed` cria usuários com senha conhecida | revisão da varredura de segredos | `ALLOW_SEED` só em desenvolvimento | `tests/test_endurecimento.py` | corrigido |
| S-11 | A02/A07 | Limite de login multiplicado pelos workers (cache local) | medição com 2 workers: 10 tentativas passaram em vez de 5 | `REDIS_CACHE_URL` (cache compartilhado) e `NUM_PROXIES` | `tests/test_endurecimento.py`; medição em `scripts/m9/limite_workers.sh` | corrigido (exige Redis em produção) |
| S-12 | A03 | Dependências nunca auditadas | — | `pip-audit` limpo; validado contra pacotes antigos | execução no CI (módulo 12) | monitorar |
| S-13 | A04 | JWT assinado com a `SECRET_KEY` da aplicação | auditoria A04 | **decisão consciente**: aceitável; melhoria futura = chave de assinatura própria | — | aceito |
| S-14 | A02 | Admin acessível publicamente por padrão | auditoria A02 | caminho configurável; recomendado restringir por rede/VPN e MFA | — | aceito com recomendação |
| S-15 | A05 | `csrf_exempt` no webhook de pagamento | guarda | justificado: sem cookie, autenticado por HMAC + timestamp (aula 7.09) | `tests/test_webhooks.py` | aceito |
| S-16 | A06 | Papéis de catálogo (Gerente, Estoquista) não veem pedidos | matriz | **menor privilégio por desenho**; papel “Atendimento” teria `orders.view_order` | `tests/test_matriz_autorizacao.py` | por desenho |

## Autenticação e sessão
- API: JWT no cabeçalho `Authorization` (access de 15 min, refresh com rotação e lista negra). Não há CSRF na API (sem cookie). Admin: sessão com cookie `HttpOnly`, `Secure`, `SameSite=Lax` e token CSRF.
- O logout invalida o refresh, **não** o access (vale até expirar): por isso é curto.
- Login: resposta idêntica para usuário inexistente e senha errada; diferença de tempo de ~1 ms (dentro do ruído); limite de 5/min.

## HTTPS e rede
- TLS termina no proxy (Nginx/balanceador). O Gunicorn escuta só em rede interna; o proxy sobrescreve `X-Forwarded-Proto`. Verificado no laboratório: certificado e nome conferidos, TLS 1.0/1.1 recusados, 1.2/1.3 aceitos.
- HSTS começa em `max-age=3600` e deve subir aos poucos.

## Banco de dados (menor privilégio)
Três papéis: dono (migrações), aplicação (DML) e leitura. A aplicação não consegue `ALTER`, `DROP`, `TRUNCATE`, `CREATE TABLE` nem criar papéis (relatório em `scripts/m9/saidas/privilegios_out.txt`).

## Privacidade (LGPD)
Inventário e retenção em `docs/privacidade.md`. Direitos implementados: acesso/portabilidade (`exportar_dados_titular`) e anonimização (`anonimizar_titular`), com os pedidos mantidos por obrigação legal. Bases legais e prazos de retenção são **hipóteses a confirmar com o jurídico**.

## Riscos aceitos e pendências
1. HSTS `includeSubDomains` e `preload` dependem do domínio.
2. Admin público: restringir por rede e exigir MFA (não implementado).
3. Chave de assinatura do JWT separada da `SECRET_KEY` (não implementado).
4. Limite de login por **conta** (atraso progressivo) não implementado; o limite por IP não impede ataque distribuído.
5. Migração pendente executada com o papel da aplicação não foi testada.
6. Plano de resposta a incidentes e comunicação à ANPD: documento a escrever com o jurídico.
