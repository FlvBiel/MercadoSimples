"""Serviço de gerenciamento de anúncios e consulta ao catálogo de produtos."""

from decimal import Decimal
from typing import Optional

from src.excecoes import ErroNaoEncontrado, ErroPermissao
from src.modelos import Produto
from src.repositorios.repositorio_produto import RepositorioProduto
from src.repositorios.repositorio_usuario import RepositorioUsuario
from src.validadores import (
    validar_categoria,
    validar_descricao_produto,
    validar_estoque,
    validar_preco,
    validar_titulo_produto,
    validar_url_imagem,
)


class ServicoCatalogo:
    """Regras de negócio para publicação, edição, remoção e busca de produtos."""

    def __init__(
        self,
        repositorio_produto: RepositorioProduto,
        repositorio_usuario: RepositorioUsuario,
    ) -> None:
        self.repositorio_produto = repositorio_produto
        self.repositorio_usuario = repositorio_usuario

    def _exigir_anunciante(self, usuario_id: int) -> None:
        usuario = self.repositorio_usuario.buscar_por_id(usuario_id)
        if usuario is None:
            raise ErroNaoEncontrado("Usuário não encontrado.")
        if not usuario.eh_anunciante():
            raise ErroPermissao("Apenas contas de anunciante podem gerenciar produtos.")

    def _obter_produto_do_anunciante(self, anunciante_id: int, produto_id: int) -> Produto:
        self._exigir_anunciante(anunciante_id)
        produto = self.repositorio_produto.buscar_por_id(produto_id)
        if produto is None or not produto.ativo:
            raise ErroNaoEncontrado("Produto não encontrado.")
        if produto.anunciante_id != anunciante_id:
            raise ErroPermissao("Você só pode gerenciar os seus próprios produtos anunciados.")
        return produto

    def anunciar_produto(
        self,
        anunciante_id: int,
        titulo: str,
        descricao: str,
        preco: Decimal | float | int | str,
        estoque: int | str,
        categoria: str = "Outros",
        imagem_url: str = "",
    ) -> Produto:
        """Publica um novo produto em nome de um anunciante."""
        self._exigir_anunciante(anunciante_id)

        novo_produto = Produto(
            anunciante_id=anunciante_id,
            titulo=validar_titulo_produto(titulo),
            descricao=validar_descricao_produto(descricao),
            preco=validar_preco(preco),
            estoque=validar_estoque(estoque),
            categoria=validar_categoria(categoria),
            imagem_url=validar_url_imagem(imagem_url),
            ativo=True,
        )
        return self.repositorio_produto.criar(novo_produto)

    def editar_produto(
        self,
        anunciante_id: int,
        produto_id: int,
        titulo: str,
        descricao: str,
        preco: Decimal | float | int | str,
        estoque: int | str,
        categoria: str = "Outros",
        imagem_url: Optional[str] = None,
    ) -> Produto:
        """Atualiza os campos de um anúncio pertencente ao anunciante."""
        produto = self._obter_produto_do_anunciante(anunciante_id, produto_id)

        produto.titulo = validar_titulo_produto(titulo)
        produto.descricao = validar_descricao_produto(descricao)
        produto.preco = validar_preco(preco)
        produto.estoque = validar_estoque(estoque)
        produto.categoria = validar_categoria(categoria)
        if imagem_url is not None:
            produto.imagem_url = validar_url_imagem(imagem_url)

        return self.repositorio_produto.atualizar(produto)

    def alterar_preco_produto(
        self,
        anunciante_id: int,
        produto_id: int,
        novo_preco: Decimal | float | int | str,
    ) -> Produto:
        """Altera apenas o preço de venda de um produto anunciado."""
        produto = self._obter_produto_do_anunciante(anunciante_id, produto_id)
        produto.alterar_preco(novo_preco)
        return self.repositorio_produto.atualizar(produto)

    def remover_produto(self, anunciante_id: int, produto_id: int) -> None:
        """Remove (desativa) um produto anunciado pelo próprio vendedor."""
        produto = self._obter_produto_do_anunciante(anunciante_id, produto_id)
        assert produto.id is not None
        self.repositorio_produto.desativar(produto.id)

    def obter_produto_ativo(self, produto_id: int) -> Produto:
        """Retorna um produto ativo para exibição pública."""
        produto = self.repositorio_produto.buscar_por_id(produto_id)
        if produto is None or not produto.ativo:
            raise ErroNaoEncontrado("Produto não encontrado ou removido.")
        return produto

    def pesquisar_produtos(
        self,
        busca: str = "",
        categoria: str = "",
        ordenacao: str = "recentes",
        apenas_em_estoque: bool = False,
    ) -> list[Produto]:
        """Pesquisa produtos disponíveis no catálogo público."""
        return self.repositorio_produto.listar_disponiveis(
            busca=busca,
            categoria=categoria,
            ordenacao=ordenacao,
            apenas_em_estoque=apenas_em_estoque,
        )

    def listar_meus_anuncios(self, anunciante_id: int) -> list[Produto]:
        """Lista todos os anúncios ativos pertencentes ao anunciante."""
        self._exigir_anunciante(anunciante_id)
        return self.repositorio_produto.listar_por_anunciante(anunciante_id)