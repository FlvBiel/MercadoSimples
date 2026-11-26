"""Serviço para manipulação do carrinho de compras do cliente."""

from src.excecoes import ErroNaoEncontrado
from src.modelos import Carrinho, ItemCarrinho
from src.repositorios.repositorio_produto import RepositorioProduto
from src.validadores import validar_quantidade_compra


class ServicoCarrinho:
    """Reconstrói e atualiza o estado do carrinho validando estoque atual."""

    def __init__(self, repositorio_produto: RepositorioProduto) -> None:
        self.repositorio_produto = repositorio_produto

    def reconstruir_carrinho(self, dados_carrinho: dict[str, int] | None) -> Carrinho:
        """Monta um objeto Carrinho a partir dos pares produto_id -> quantidade."""
        itens: list[ItemCarrinho] = []
        for chave_id, qtd in (dados_carrinho or {}).items():
            try:
                produto_id = int(chave_id)
                quantidade = int(qtd)
            except (TypeError, ValueError):
                continue

            if quantidade < 1:
                continue

            produto = self.repositorio_produto.buscar_por_id(produto_id)
            if produto is None or not produto.ativo or produto.estoque <= 0:
                continue

            qtd_ajustada = min(quantidade, produto.estoque)
            itens.append(ItemCarrinho(produto=produto, quantidade=qtd_ajustada))

        return Carrinho(itens=itens)

    def adicionar_item(
        self,
        dados_carrinho: dict[str, int] | None,
        produto_id: int,
        quantidade: int | str = 1,
    ) -> dict[str, int]:
        """Adiciona unidades de um produto ao carrinho serializado."""
        qtd = validar_quantidade_compra(quantidade)
        produto = self.repositorio_produto.buscar_por_id(produto_id)
        if produto is None or not produto.ativo:
            raise ErroNaoEncontrado("Produto não encontrado ou indisponível.")

        carrinho = self.reconstruir_carrinho(dados_carrinho)
        carrinho.adicionar(produto, qtd)
        return carrinho.para_dicionario()

    def atualizar_item(
        self,
        dados_carrinho: dict[str, int] | None,
        produto_id: int,
        quantidade: int | str,
    ) -> dict[str, int]:
        """Atualiza a quantidade de um produto já presente no carrinho."""
        qtd = validar_quantidade_compra(quantidade)
        carrinho = self.reconstruir_carrinho(dados_carrinho)
        carrinho.atualizar_quantidade(produto_id, qtd)
        return carrinho.para_dicionario()

    def remover_item(
        self,
        dados_carrinho: dict[str, int] | None,
        produto_id: int,
    ) -> dict[str, int]:
        """Remove um item do carrinho."""
        carrinho = self.reconstruir_carrinho(dados_carrinho)
        carrinho.remover(produto_id)
        return carrinho.para_dicionario()

    @staticmethod
    def limpar_carrinho() -> dict[str, int]:
        """Retorna a representação vazia de um carrinho limpo."""
        return {}