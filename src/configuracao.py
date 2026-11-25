"""Configurações de ambiente da aplicação MercadoSimples."""

import os
from pathlib import Path
from typing import Any

DIRETORIO_RAIZ = Path(__file__).resolve().parent.parent


def obter_configuracao(sobrescritas: dict[str, Any] | None = None) -> dict[str, Any]:
    """Monta o dicionário de configuração lendo variáveis de ambiente com padrões seguros."""
    pasta_instancia = DIRETORIO_RAIZ / "instance"
    caminho_banco_padrao = str(pasta_instancia / "mercado.db")
    pasta_uploads_padrao = str(pasta_instancia / "uploads")

    config: dict[str, Any] = {
        "SECRET_KEY": os.environ.get("SECRET_KEY", "chave-desenvolvimento-mercado-simples"),
        "CAMINHO_BANCO": os.environ.get("CAMINHO_BANCO", caminho_banco_padrao),
        "PASTA_UPLOADS": os.environ.get("PASTA_UPLOADS", pasta_uploads_padrao),
        "MAX_CONTENT_LENGTH": int(os.environ.get("MAX_CONTENT_LENGTH", str(4 * 1024 * 1024))),
        "PORT": int(os.environ.get("PORT", "5000")),
        "TESTING": False,
    }

    if sobrescritas:
        config.update(sobrescritas)

    return config