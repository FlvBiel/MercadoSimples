"""Serviço de finalização de pedidos e consulta de saldo dos anunciantes."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.banco import BancoDados
from src.excecoes import (
    ErroEstoqueInsuficiente,
    ErroNaoEncontrado,
    ErroPermissao,
    ErroValidacao,
)
from src.modelos import Carrinho, ItemPedido, Pedido, RegistroVenda
from src.repositorios.repositorio_pedido import RepositorioPedido
from src.repositorios.repositorio_produto import RepositorioProduto
from src.repositorios.repositorio_usuario import RepositorioUsuario
from src.servicos.servico_pagamento import SimuladorPagamento


@dataclass
class ResumoFinanceiroAnunciante:
    """Agrupa o saldo acumulado e o histórico de vendas de um anunciante."""

    saldo_disponivel: Decimal
    total_vendas: int
    itens_vendidos: int
    vendas: list[RegistroVenda]


class ServicoPedido:
    """Orquestra o pagamento único do carrinho, baixa de estoque e repasse de saldo."""

    def __init__(
        self,
        banco: BancoDados,
        repositorio_usuario: RepositorioUsuario,
        repositorio_produto: RepositorioProduto,
        repositorio_pedido: RepositorioPedido,
        simulador_pagamento: SimuladorPagamento | None = None,
    ) -> None:
        self.banco = banco
        self.repositorio_usuario = repositorio_usuario
        self.repositorio_produto = repositorio_produto
        self.repositorio_pedido = repositorio_pedido
        self.simulador_pagamento = simulador_pagamento or SimuladorPagamento()

    def finalizar_compra(self, cliente_id: int, carrinho: Carrinho) -> Pedido:
        """Valida itens, aprova o pagamento simulado, abate estoque e credita vendedores."""
        cliente = self.repositorio_usuario.buscar_por_id(cliente_id)
        if cliente is None:
            raise ErroNaoEncontrado("Cliente não encontrado.")
        if not cliente.eh_cliente():
            raise ErroPermissao("Apenas contas de cliente podem finalizar compras.")
        if carrinho.esta_vazio():
            raise ErroValidacao("Não é possível finalizar a compra com o carrinho vazio.")

        itens_pedido: list[ItemPedido] = []
        total = Decimal("0.00")

        for item_carrinho in carrinho.itens:
            assert item_carrinho.produto.id is not None
            produto_atual = self.repositorio_produto.buscar_por_id(item_carrinho.produto.id)
            if produto_atual is None or not produto_atual.esta_disponivel(item_carrinho.quantidade):
                raise ErroEstoqueInsuficiente(
                    f"Estoque insuficiente para o produto '{item_carrinho.produto.titulo}'."
                )

            item = ItemPedido(
                produto_id=produto_atual.id,  # type: ignore[arg-type]
                anunciante_id=produto_atual.anunciante_id,
                titulo_produto=produto_atual.titulo,
                preco_unitario=produto_atual.preco,
                quantidade=item_carrinho.quantidade,
            )
            itens_pedido.append(item)
            total = (total + item.subtotal).quantize(Decimal("0.01"))

        resultado_pagamento = self.simulador_pagamento.aprovar_pagamento(cliente_id, total)
        if not resultado_pagamento.aprovado:
            raise ErroValidacao(resultado_pagamento.mensagem)

        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
        novo_pedido = Pedido(
            cliente_id=cliente_id,
            itens=itens_pedido,
            total=total,
            status="pago",
            codigo_transacao=resultado_pagamento.codigo_transacao,
            criado_em=data_hora,
        )

        with self.banco.transacao() as conexao:
            for item in itens_pedido:
                self.repositorio_produto.reduzir_estoque(
                    item.produto_id,
                    item.quantidade,
                    conexao=conexao,
                )
                self.repositorio_usuario.adicionar_saldo(
                    item.anunciante_id,
                    item.subtotal,
                    conexao=conexao,
                )
            pedido_salvo = self.repositorio_pedido.criar(novo_pedido, conexao=conexao)

        carrinho.limpar()
        return pedido_salvo

    def listar_pedidos_cliente(self, cliente_id: int) -> list[Pedido]:
        """Retorna o histórico de compras de um cliente."""
        cliente = self.repositorio_usuario.buscar_por_id(cliente_id)
        if cliente is None:
            raise ErroNaoEncontrado("Cliente não encontrado.")
        if not cliente.eh_cliente():
            raise ErroPermissao("Apenas contas de cliente possuem histórico de compras.")
        return self.repositorio_pedido.listar_por_cliente(cliente_id)

    def obter_resumo_financeiro_anunciante(
        self,
        anunciante_id: int,
    ) -> ResumoFinanceiroAnunciante:
        """Retorna o saldo a receber e a lista detalhada de itens vendidos."""
        anunciante = self.repositorio_usuario.buscar_por_id(anunciante_id)
        if anunciante is None:
            raise ErroNaoEncontrado("Anunciante não encontrado.")
        if not anunciante.eh_anunciante():
            raise ErroPermissao("Apenas contas de anunciante possuem extrato de vendas.")

        vendas = self.repositorio_pedido.listar_vendas_por_anunciante(anunciante_id)
        itens_vendidos = sum(v.quantidade for v in vendas)
        return ResumoFinanceiroAnunciante(
            saldo_disponivel=anunciante.saldo,
            total_vendas=len(vendas),
            itens_vendidos=itens_vendidos,
            vendas=vendas,
        )