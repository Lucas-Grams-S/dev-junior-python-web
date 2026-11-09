"""Cabeçalhos de segurança que o Django 5.2 não envia sozinho: Content-Security-Policy e Permissions-Policy."""
API = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
DOCS = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://cdn.jsdelivr.net; worker-src blob:; frame-ancestors 'none'; base-uri 'self'")
ADMIN = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
PERMISSOES = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resp = self.get_response(request)
        caminho = request.path
        if caminho.startswith(("/api/docs", "/api/redoc")):
            csp = DOCS
        elif caminho.startswith("/admin") or caminho.lstrip("/").startswith(self._admin()):
            csp = ADMIN
        else:
            csp = API
        resp.headers.setdefault("Content-Security-Policy", csp)
        resp.headers.setdefault("Permissions-Policy", PERMISSOES)
        return resp

    @staticmethod
    def _admin():
        from django.conf import settings
        return settings.ADMIN_URL
