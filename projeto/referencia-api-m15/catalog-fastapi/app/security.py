import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

# auto_error=False: sem cabeçalho não explode aqui; decidimos nós (leitura pública x escrita protegida)
bearer = HTTPBearer(auto_error=False, description="Token de serviço (CATALOG_API_TOKEN)")
Creds = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


def is_staff(creds: Creds) -> bool:
    """Opcional: True se o token é o do serviço. Comparação em tempo constante (evita ataque de temporização)."""
    if creds is None or not settings.api_token:
        return False
    return hmac.compare_digest(creds.credentials.encode(), settings.api_token.encode())


def require_staff(staff: Annotated[bool, Depends(is_staff)]) -> None:
    if not staff:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais ausentes ou inválidas.", headers={"WWW-Authenticate": "Bearer"})
