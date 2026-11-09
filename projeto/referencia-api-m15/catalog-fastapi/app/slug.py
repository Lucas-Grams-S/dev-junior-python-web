import re
import unicodedata


def slugify(text: str) -> str:
    """'Fone de ouvido Pro' -> 'fone-de-ouvido-pro' (mesma ideia do django.utils.text.slugify)."""
    ascii_ = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", ascii_).strip().lower())
