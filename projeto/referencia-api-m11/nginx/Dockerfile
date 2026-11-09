# Nginx com os arquivos estáticos do Django "assados" dentro da imagem.
FROM nginx:1.29-alpine
# `app` é a imagem do Django (passada pelo Compose em additional_contexts): copiamos só o resultado do collectstatic.
COPY --from=app /app/staticfiles /usr/share/nginx/html/static
COPY nginx.conf /etc/nginx/conf.d/default.conf
