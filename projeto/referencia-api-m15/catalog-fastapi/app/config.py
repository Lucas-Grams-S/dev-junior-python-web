from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração tipada lida do ambiente (prefixo CATALOG_) ou de .env. Compare com config/envconf.py do Django."""

    model_config = SettingsConfigDict(env_prefix="CATALOG_", env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./catalog.db"
    api_token: str = ""  # vazio = escrita DESLIGADA (fecha por padrão); defina CATALOG_API_TOKEN para ligar
    page_size: int = 20
    max_page_size: int = 100


settings = Settings()
