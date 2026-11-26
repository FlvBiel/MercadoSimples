"""Repositório de persistência e consulta de produtos anunciados."""

import sqlite3
from typing import Optional

from src.banco import BancoDados
from src.excecoes import ErroEstoqueInsuficiente, ErroNaoEncontrado
from src.modelos import Produto
from src.validadores import centavos_para_decimal, decimal_para_centavos


class RepositorioProduto:
    """Realiza operações CRUD, filtros de catálogo e atualização de estoque."""

    def __init__(self, banco: BancoDados) -> None:
        self.banco = banco

    @staticmethod
    def _linha_para_produto(linha: sqlite3.Row) -> Produto:
        chaves = linha.keys()
        nome_anunciante = linha["nome_anunciante"] if "nome_anunciante" in chaves else ""
        return Produto(
            id=linha["id"],
            anunciante_id=linha["anunciante_id"],
            titulo=linha["titulo"],
            descricao=linha["descricao"],
            preco=centavos_para_decimal(linha["preco_centavos"]),
            estoque=linha["estoque"],
            categoria=linha["categoria"],
            imagem_url=linha["imagem_url"],
            ativo=bool(linha["ativo"]),
            nome_anunciante=nome_anunciante,
        )

    def criar(self, produto: Produto) -> Produto:
        """Salva um novo anúncio de produto no banco."""
        preco_centavos = decimal_para_centavos(produto.preco)
        with self.banco.transacao() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO produtos (
                    anunciante_id, titulo, descricao, preco_centavos,
                    estoque, categoria, imagem_url, ativo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    produto.anunciante_id,
                    produto.titulo,
                    produto.descricao,
                    preco_centavos,
                    produto.estoque,
                    produto.categoria,
                    produto.imagem_url,
                    1 if produto.ativo else 0,
                ),
            )
            novo_id = cursor.lastrowid
        criado = self.buscar_por_id(int(novo_id))
        assert criado is not None
        return criado

    def buscar_por_id(self, produto_id: int) -> Optional[Produto]:
        """Recupera um produto pelo ID juntamente com o nome do anunciante."""
        with self.banco.transacao() as conexao:
            linha = conexao.execute(
                """
                SELECT p.*, u.nome AS nome_anunciante
                FROM produtos p
                JOIN usuarios u ON u.id = p.anunciante_id
                WHERE p.id = ?
                """,
                (produto_id,),
            ).fetchone()
        return self._linha_para_produto(linha) if linha else None

    def listar_disponiveis(
        self,
        busca: str = "",
        categoria: str = "",
        ordenacao: str = "recentes",
        apenas_em_estoque: bool = False,
    ) -> list[Produto]:
        """Lista produtos ativos aplicando filtros opcionais de busca, categoria e ordem."""
        clausulas = ["p.ativo = 1"]
        parametros: list[object] = []

        if apenas_em_estoque:
            clausulas.append("p.estoque > 0")

        termo = busca.strip()
        if termo:
            clausulas.append("(LOWER(p.titulo) LIKE ? OR LOWER(p.descricao) LIKE ?)")
            padrao = f"%{termo.lower()}%"
            parametros.extend([padrao, padrao])

        cat = categoria.strip()
        if cat:
            clausulas.append("p.categoria = ?")
            parametros.append(cat)

        mapa_ordenacao = {
            "recentes": "p.id DESC",
            "menor_preco": "p.preco_centavos ASC, p.id DESC",
            "maior_preco": "p.preco_centavos DESC, p.id DESC",
        }
        clausula_ordem = mapa_ordenacao.get(ordenacao, "p.id DESC")

        sql = f"""
            SELECT p.*, u.nome AS nome_anunciante
            FROM produtos p
            JOIN usuarios u ON u.id = p.anunciante_id
            WHERE {' AND '.join(clausulas)}
            ORDER BY {clausula_ordem}
        """
        with self.banco.transacao() as conexao:
            linhas = conexao.execute(sql, parametros).fetchall()
        return [self._linha_para_produto(linha) for linha in linhas]

    def listar_por_anunciante(
        self,
        anunciante_id: int,
        incluir_inativos: bool = False,
    ) -> list[Produto]:
        """Lista os produtos cadastrados por um anunciante específico."""
        filtro_ativo = "" if incluir_inativos else "AND p.ativo = 1"
        sql = f"""
            SELECT p.*, u.nome AS nome_anunciante
            FROM produtos p
            JOIN usuarios u ON u.id = p.anunciante_id
            WHERE p.anunciante_id = ? {filtro_ativo}
            ORDER BY p.id DESC
        """
        with self.banco.transacao() as conexao:
            linhas = conexao.execute(sql, (anunciante_id,)).fetchall()
        return [self._linha_para_produto(linha) for linha in linhas]

    def atualizar(self, produto: Produto) -> Produto:
        """Atualiza os dados de um produto existente."""
        if produto.id is None:
            raise ErroNaoEncontrado("Produto sem identificador para atualização.")
        preco_centavos = decimal_para_centavos(produto.preco)
        with self.banco.transacao() as conexao:
            cursor = conexao.execute(
                """
                UPDATE produtos
                SET titulo = ?, descricao = ?, preco_centavos = ?,
                    estoque = ?, categoria = ?, imagem_url = ?, ativo = ?
                WHERE id = ?
                """,
                (
                    produto.titulo,
                    produto.descricao,
                    preco_centavos,
                    produto.estoque,
                    produto.categoria,
                    produto.imagem_url,
                    1 if produto.ativo else 0,
                    produto.id,
                ),
            )
            if cursor.rowcount == 0:
                raise ErroNaoEncontrado("Produto não encontrado.")
        atualizado = self.buscar_por_id(produto.id)
        assert atualizado is not None
        return atualizado

    def desativar(self, produto_id: int) -> None:
        """Remove o produto do catálogo marcando-o como inativo."""
        with self.banco.transacao() as conexao:
            cursor = conexao.execute(
                "UPDATE produtos SET ativo = 0 WHERE id = ?",
                (produto_id,),
            )
            if cursor.rowcount == 0:
                raise ErroNaoEncontrado("Produto não encontrado.")

    def reduzir_estoque(
        self,
        produto_id: int,
        quantidade: int,
        conexao: Optional[sqlite3.Connection] = None,
    ) -> None:
        """Deduz unidades do estoque garantindo disponibilidade de forma atômica."""
        sql = """
            UPDATE produtos
            SET estoque = estoque - ?
            WHERE id = ? AND ativo = 1 AND estoque >= ?
        """
        if conexao is not None:
            cursor = conexao.execute(sql, (quantidade, produto_id, quantidade))
            if cursor.rowcount == 0:
                raise ErroEstoqueInsuficiente(
                    "Estoque insuficiente ou produto indisponível no momento da compra."
                )
            return

        with self.banco.transacao() as nova_conexao:
            cursor = nova_conexao.execute(sql, (quantidade, produto_id, quantidade))
            if cursor.rowcount == 0:
                raise ErroEstoqueInsuficiente(
                    "Estoque insuficiente ou produto indisponível no momento da compra."
                )