"""Repositório de persistência de pedidos de compra e histórico de vendas."""

import sqlite3
from typing import Optional

from src.banco import BancoDados
from src.modelos import ItemPedido, Pedido, RegistroVenda
from src.validadores import centavos_para_decimal, decimal_para_centavos


class RepositorioPedido:
    """Realiza gravação e consulta de pedidos de clientes e vendas de anunciantes."""

    def __init__(self, banco: BancoDados) -> None:
        self.banco = banco

    def _inserir_pedido(self, conexao: sqlite3.Connection, pedido: Pedido) -> Pedido:
        total_centavos = decimal_para_centavos(pedido.total)
        cursor = conexao.execute(
            """
            INSERT INTO pedidos (cliente_id, total_centavos, status, codigo_transacao, criado_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                pedido.cliente_id,
                total_centavos,
                pedido.status,
                pedido.codigo_transacao,
                pedido.criado_em,
            ),
        )
        pedido_id = int(cursor.lastrowid)
        itens_salvos: list[ItemPedido] = []

        for item in pedido.itens:
            preco_centavos = decimal_para_centavos(item.preco_unitario)
            cursor_item = conexao.execute(
                """
                INSERT INTO itens_pedido (
                    pedido_id, produto_id, anunciante_id,
                    titulo_produto, preco_unitario_centavos, quantidade
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    pedido_id,
                    item.produto_id,
                    item.anunciante_id,
                    item.titulo_produto,
                    preco_centavos,
                    item.quantidade,
                ),
            )
            itens_salvos.append(
                ItemPedido(
                    id=int(cursor_item.lastrowid),
                    pedido_id=pedido_id,
                    produto_id=item.produto_id,
                    anunciante_id=item.anunciante_id,
                    titulo_produto=item.titulo_produto,
                    preco_unitario=item.preco_unitario,
                    quantidade=item.quantidade,
                )
            )

        return Pedido(
            id=pedido_id,
            cliente_id=pedido.cliente_id,
            itens=itens_salvos,
            total=pedido.total,
            status=pedido.status,
            codigo_transacao=pedido.codigo_transacao,
            criado_em=pedido.criado_em,
        )

    def criar(
        self,
        pedido: Pedido,
        conexao: Optional[sqlite3.Connection] = None,
    ) -> Pedido:
        """Registra um pedido e todos os seus itens no banco."""
        if conexao is not None:
            return self._inserir_pedido(conexao, pedido)
        with self.banco.transacao() as nova_conexao:
            return self._inserir_pedido(nova_conexao, pedido)

    def _carregar_itens(self, conexao: sqlite3.Connection, pedido_id: int) -> list[ItemPedido]:
        linhas = conexao.execute(
            "SELECT * FROM itens_pedido WHERE pedido_id = ? ORDER BY id ASC",
            (pedido_id,),
        ).fetchall()
        return [
            ItemPedido(
                id=linha["id"],
                pedido_id=linha["pedido_id"],
                produto_id=linha["produto_id"],
                anunciante_id=linha["anunciante_id"],
                titulo_produto=linha["titulo_produto"],
                preco_unitario=centavos_para_decimal(linha["preco_unitario_centavos"]),
                quantidade=linha["quantidade"],
            )
            for linha in linhas
        ]

    def buscar_por_id(self, pedido_id: int) -> Optional[Pedido]:
        """Recupera um pedido completo pelo seu identificador."""
        with self.banco.transacao() as conexao:
            linha = conexao.execute(
                "SELECT * FROM pedidos WHERE id = ?",
                (pedido_id,),
            ).fetchone()
            if not linha:
                return None
            itens = self._carregar_itens(conexao, pedido_id)

        return Pedido(
            id=linha["id"],
            cliente_id=linha["cliente_id"],
            itens=itens,
            total=centavos_para_decimal(linha["total_centavos"]),
            status=linha["status"],
            codigo_transacao=linha["codigo_transacao"],
            criado_em=linha["criado_em"],
        )

    def listar_por_cliente(self, cliente_id: int) -> list[Pedido]:
        """Retorna todos os pedidos realizados por um cliente, do mais recente ao mais antigo."""
        with self.banco.transacao() as conexao:
            linhas = conexao.execute(
                "SELECT * FROM pedidos WHERE cliente_id = ? ORDER BY id DESC",
                (cliente_id,),
            ).fetchall()
            pedidos = [
                Pedido(
                    id=linha["id"],
                    cliente_id=linha["cliente_id"],
                    itens=self._carregar_itens(conexao, linha["id"]),
                    total=centavos_para_decimal(linha["total_centavos"]),
                    status=linha["status"],
                    codigo_transacao=linha["codigo_transacao"],
                    criado_em=linha["criado_em"],
                )
                for linha in linhas
            ]
        return pedidos

    def listar_vendas_por_anunciante(self, anunciante_id: int) -> list[RegistroVenda]:
        """Lista cada venda individual de produtos pertencentes ao anunciante."""
        sql = """
            SELECT
                ip.pedido_id,
                ip.titulo_produto,
                ip.preco_unitario_centavos,
                ip.quantidade,
                p.criado_em,
                u.nome AS nome_comprador
            FROM itens_pedido ip
            JOIN pedidos p ON p.id = ip.pedido_id
            JOIN usuarios u ON u.id = p.cliente_id
            WHERE ip.anunciante_id = ?
            ORDER BY ip.id DESC
        """
        with self.banco.transacao() as conexao:
            linhas = conexao.execute(sql, (anunciante_id,)).fetchall()

        vendas: list[RegistroVenda] = []
        for linha in linhas:
            preco = centavos_para_decimal(linha["preco_unitario_centavos"])
            qtd = int(linha["quantidade"])
            vendas.append(
                RegistroVenda(
                    pedido_id=linha["pedido_id"],
                    titulo_produto=linha["titulo_produto"],
                    nome_comprador=linha["nome_comprador"],
                    quantidade=qtd,
                    preco_unitario=preco,
                    subtotal=(preco * qtd).quantize(preco),
                    criado_em=linha["criado_em"],
                )
            )
        return vendas