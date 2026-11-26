"""Registro de blueprints das rotas HTTP."""

from src.rotas.autenticacao import bp_autenticacao
from src.rotas.catalogo import bp_catalogo

__all__ = ["bp_catalogo", "bp_autenticacao"]