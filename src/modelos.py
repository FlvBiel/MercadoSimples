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

@dataclass
class Produto:
    """Representa um item anunciado para venda por um anunciante."""

    anunciante_id: int
    titulo: str
    descricao: str
    preco: Decimal
    estoque: int
    categoria: str = "Outros"
    imagem_url: str = ""
    ativo: bool = True
    nome_anunciante: str = ""
    id: Optional[int] = None

    def esta_disponivel(self, quantidade: int = 1) -> bool:
        """Verifica se o produto está ativo e possui estoque suficiente."""
        return self.ativo and quantidade >= 1 and self.estoque >= quantidade

    def alterar_preco(self, novo_preco: Decimal | float | str) -> None:
        """Atualiza o preço do produto após validação."""
        self.preco = validar_preco(novo_preco)

    def reduzir_estoque(self, quantidade: int) -> None:
        """Deduz unidades vendidas do estoque do produto."""
        qtd = validar_quantidade_compra(quantidade)
        if not self.ativo:
            raise ErroEstoqueInsuficiente(f"O produto '{self.titulo}' não está mais ativo.")
        if qtd > self.estoque:
            raise ErroEstoqueInsuficiente(
                f"Estoque insuficiente para '{self.titulo}' (disponível: {self.estoque})."
            )
        self.estoque -= qtd

    def desativar(self) -> None:
        """Marca o anúncio como inativo (removido do catálogo público)."""
        self.ativo = False

    def caminho_imagem_exibicao(self) -> str:
        """Retorna a imagem cadastrada ou a ilustração padrão do sistema."""
        return self.imagem_url if self.imagem_url else IMAGEM_PADRAO_PRODUTO