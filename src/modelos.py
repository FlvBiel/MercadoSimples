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

@dataclass
class ItemCarrinho:
    """Associa um produto a uma quantidade selecionada pelo cliente."""

    produto: Produto
    quantidade: int

    @property
    def subtotal(self) -> Decimal:
        """Calcula o subtotal do item (preço unitário multiplicado pela quantidade)."""
        return (self.produto.preco * self.quantidade).quantize(Decimal("0.01"))


class Carrinho:
    """Gerencia os itens selecionados pelo cliente antes do pagamento."""

    def __init__(self, itens: Optional[list[ItemCarrinho]] = None) -> None:
        self._itens: dict[int, ItemCarrinho] = {}
        for item in itens or []:
            if item.produto.id is None:
                raise ErroValidacao("Produto no carrinho precisa possuir identificador.")
            self._itens[item.produto.id] = item

    @property
    def itens(self) -> list[ItemCarrinho]:
        """Retorna a lista de itens presentes no carrinho."""
        return list(self._itens.values())

    def adicionar(self, produto: Produto, quantidade: int = 1) -> None:
        """Adiciona um produto ao carrinho ou incrementa sua quantidade."""
        if produto.id is None:
            raise ErroValidacao("Não é possível adicionar produto sem identificador.")
        qtd = validar_quantidade_compra(quantidade)
        atual = self._itens[produto.id].quantidade if produto.id in self._itens else 0
        nova_qtd = atual + qtd
        if not produto.esta_disponivel(nova_qtd):
            raise ErroEstoqueInsuficiente(
                f"Quantidade indisponível em estoque para '{produto.titulo}'."
            )
        self._itens[produto.id] = ItemCarrinho(produto=produto, quantidade=nova_qtd)

    def atualizar_quantidade(self, produto_id: int, quantidade: int) -> None:
        """Define uma nova quantidade para um item existente no carrinho."""
        if produto_id not in self._itens:
            raise ErroValidacao("Este item não está no carrinho.")
        qtd = validar_quantidade_compra(quantidade)
        produto = self._itens[produto_id].produto
        if not produto.esta_disponivel(qtd):
            raise ErroEstoqueInsuficiente(
                f"Quantidade indisponível em estoque para '{produto.titulo}'."
            )
        self._itens[produto_id] = ItemCarrinho(produto=produto, quantidade=qtd)

    def remover(self, produto_id: int) -> None:
        """Remove um produto do carrinho caso esteja presente."""
        self._itens.pop(produto_id, None)

    def limpar(self) -> None:
        """Esvazia todos os itens do carrinho."""
        self._itens.clear()

    def esta_vazio(self) -> bool:
        """Indica se não há nenhum item no carrinho."""
        return len(self._itens) == 0

    def quantidade_total_itens(self) -> int:
        """Soma o total de unidades de produtos no carrinho."""
        return sum(item.quantidade for item in self._itens.values())

    def calcular_total(self) -> Decimal:
        """Calcula o valor total a pagar por todos os itens do carrinho."""
        total = sum((item.subtotal for item in self._itens.values()), Decimal("0.00"))
        return total.quantize(Decimal("0.01"))

    def para_dicionario(self) -> dict[str, int]:
        """Serializa o carrinho em formato simples compatível com sessão web."""
        return {str(pid): item.quantidade for pid, item in self._itens.items()}


@dataclass
class ItemPedido:
    """Representa um item adquirido dentro de um pedido pago."""

    produto_id: int
    anunciante_id: int
    titulo_produto: str
    preco_unitario: Decimal
    quantidade: int
    id: Optional[int] = None
    pedido_id: Optional[int] = None

    @property
    def subtotal(self) -> Decimal:
        """Calcula o valor total pago por este item do pedido."""
        return (self.preco_unitario * self.quantidade).quantize(Decimal("0.01"))


@dataclass
class Pedido:
    """Representa uma compra finalizada e paga por um cliente."""

    cliente_id: int
    itens: list[ItemPedido] = field(default_factory=list)
    total: Decimal = Decimal("0.00")
    status: str = "pago"
    codigo_transacao: str = ""
    criado_em: str = ""
    id: Optional[int] = None


@dataclass
class RegistroVenda:
    """Representa uma venda recebida por um anunciante para exibição no extrato."""

    pedido_id: int
    titulo_produto: str
    nome_comprador: str
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal
    criado_em: str