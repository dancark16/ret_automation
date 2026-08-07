# Mapeo de nombre real → nombre corto para Excel y PDF
# Agregar aquí cada cliente que tenga nombre diferente al que usa SRI
CLIENT_ALIASES: dict[str, str] = {
    "GUAMBUGUETE SOLORZANO JOSE LUIS": "MAXCOLOR",
}


def resolve_client(name: str) -> str:
    """Retorna el alias del cliente si existe, o el nombre original."""
    return CLIENT_ALIASES.get(name.strip().upper(), name)
