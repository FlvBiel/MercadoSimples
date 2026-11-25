"""Exceções de domínio da plataforma MercadoSimples."""


class ErroMercado(Exception):
    """Exceção base para erros de negócio do sistema."""


class ErroValidacao(ErroMercado):
    """Erro lançado quando dados informados pelo usuário são inválidos."""


class ErroAutenticacao(ErroMercado):
    """Erro lançado em falhas de cadastro ou autenticação."""


class ErroPermissao(ErroMercado):
    """Erro lançado quando o usuário não possui permissão para a operação."""


class ErroNaoEncontrado(ErroMercado):
    """Erro lançado quando um recurso solicitado não existe."""


class ErroEstoqueInsuficiente(ErroMercado):
    """Erro lançado quando não há estoque disponível para atender ao pedido."""