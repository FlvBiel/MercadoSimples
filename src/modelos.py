"""Modelos de domínio da plataforma de e-commerce MercadoSimples."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from src.excecoes import ErroEstoqueInsuficiente, ErroValidacao
from src.validadores import validar_preco, validar_quantidade_compra

IMAGEM_PADRAO_PRODUTO = "/static/img/produto_padrao.svg"


class PerfilUsuario(str, Enum):
    """Perfis disponíveis para contas de usuário."""

    CLIENTE = "cliente"
    ANUNCIANTE = "anunciante"


@dataclass
class Usuario:
    """Representa um usuário cadastrado na plataforma (cliente ou anunciante)."""

    nome: str
    email: str
    senha_hash: str
    perfil: str
    saldo: Decimal = Decimal("0.00")
    id: Optional[int] = None

    def eh_anunciante(self) -> bool:
        """Indica se o usuário possui conta de anunciante."""
        return self.perfil == PerfilUsuario.ANUNCIANTE.value

    def eh_cliente(self) -> bool:
        """Indica se o usuário possui conta de cliente comprador."""
        return self.perfil == PerfilUsuario.CLIENTE.value

    def creditar_saldo(self, valor: Decimal) -> None:
        """Adiciona um valor positivo ao saldo a receber do anunciante."""
        quantia = validar_preco(valor)
        if not self.eh_anunciante():
            raise ErroValidacao("Apenas contas de anunciante possuem saldo de vendas.")
        self.saldo = (self.saldo + quantia).quantize(Decimal("0.01"))