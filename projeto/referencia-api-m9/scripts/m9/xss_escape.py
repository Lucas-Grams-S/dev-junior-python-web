"""Escape de saída no Django: o mesmo texto, em três situações. O valor é só um comentário com marcação HTML."""
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.environ["LAB"])
import django
django.setup()
from django.template import engines
from django.utils.html import format_html
from django.utils.safestring import mark_safe

django_t = engines["django"]
comentario = 'Ótimo! <b>negrito</b> & "aspas" <script>alert(1)</script>'

def render(src, **ctx):
    return django_t.from_string(src).render(ctx)

print("1) autoescape (padrão):            ", render("<p>{{ c }}</p>", c=comentario))
print("2) com |safe (DESLIGA a proteção):  ", render("<p>{{ c|safe }}</p>", c=comentario))
print("3) em atributo, entre aspas:        ", render('<input value="{{ c }}">', c='" onfocus="x'))
print("4) format_html escapa os argumentos:", format_html("<a href='/u/{}'>{}</a>", "a&b", "<i>x</i>"))
print("5) mark_safe confia no que você passa:", mark_safe(comentario)[:34] + "...")
print("6) json_script (dados para o JS):   ", render("{% load static %}{{ d|json_script:'dados' }}", d={"texto": "</script><b>"}))
