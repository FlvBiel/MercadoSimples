"""Funções puras de validação e formatação de dados do domínio."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from src.excecoes import ErroValidacao

CATEGORIAS_PERMITIDAS = (
    "Eletrônicos",
    "Livros",
    "Roupas",
    "Casa",
    "Esportes",
    "Outros",
)

PERFIS_PERMITIDOS = ("cliente", "anunciante")

EXTENSOES_IMAGEM_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

_PADRAO_EMAIL = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validar_nome(nome: str) -> str:
    """Valida e normaliza o nome de exibição do usuário."""
    if not isinstance(nome, str):
        raise ErroValidacao("O nome deve ser um texto válido.")
    limpo = nome.strip()
    if len(limpo) < 2:
        raise ErroValidacao("O nome deve ter pelo menos 2 caracteres.")
    if len(limpo) > 100:
        raise ErroValidacao("O nome deve ter no máximo 100 caracteres.")
    return limpo


def validar_email(email: str) -> str:
    """Valida e normaliza o endereço de e-mail."""
    if not isinstance(email, str):
        raise ErroValidacao("O e-mail deve ser um texto válido.")
    limpo = email.strip().lower()
    if not limpo or len(limpo) > 150 or not _PADRAO_EMAIL.match(limpo):
        raise ErroValidacao("Informe um endereço de e-mail válido.")
    return limpo


def validar_senha(senha: str) -> str:
    """Valida os requisitos mínimos da senha."""
    if not isinstance(senha, str) or len(senha) < 6:
        raise ErroValidacao("A senha deve ter pelo menos 6 caracteres.")
    if len(senha) > 128:
        raise ErroValidacao("A senha deve ter no máximo 128 caracteres.")
    return senha


def validar_perfil(perfil: str) -> str:
    """Valida o tipo de conta do usuário (cliente ou anunciante)."""
    if not isinstance(perfil, str):
        raise ErroValidacao("Perfil de usuário inválido.")
    limpo = perfil.strip().lower()
    if limpo not in PERFIS_PERMITIDOS:
        raise ErroValidacao("O perfil deve ser 'cliente' ou 'anunciante'.")
    return limpo