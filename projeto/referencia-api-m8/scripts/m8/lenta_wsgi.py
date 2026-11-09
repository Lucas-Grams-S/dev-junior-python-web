"""WSGI de demonstração: /lenta demora 3 s (simula uma requisição em andamento); o resto é o MiniShop."""
import time
from config.wsgi import application as django_app


def application(environ, start_response):
    if environ["PATH_INFO"] == "/lenta":
        time.sleep(3)
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"terminei o trabalho\n"]
    return django_app(environ, start_response)
