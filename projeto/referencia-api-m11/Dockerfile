# syntax=docker/dockerfile:1

# ---------- base: o que as duas etapas compartilham ----------
FROM python:3.13-slim AS base
# Sem .pyc soltos e sem buffer de saída: os logs aparecem na hora em `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---------- builder: instala dependências (esta etapa NÃO vai para a imagem final) ----------
FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app

# 1) Dependências primeiro: só dependem de pyproject.toml e uv.lock, que mudam raramente.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# 2) Código depois: muda a cada commit, então vem por último.
COPY manage.py ./
COPY config config
COPY apps apps
COPY legado legado

# 3) Arquivos estáticos (admin, DRF) são coletados na construção.
RUN SECRET_KEY=so-para-o-build /app/.venv/bin/python manage.py collectstatic --noinput

# ---------- runtime: a imagem que roda ----------
FROM base AS runtime
# Usuário sem privilégios, com UID fixo (previsível para volumes e para o Kubernetes).
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
 && mkdir /data && chown app:app /data
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8000
# Forma "exec" (lista JSON): o gunicorn vira o PID 1 e recebe o SIGTERM do `docker stop`.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
