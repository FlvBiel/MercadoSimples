"""Serviço responsável pelo cadastro, autenticação e consulta de usuários."""

from decimal import Decimal
from werkzeug.security import check_password_hash, generate_password_hash

from src.excecoes import ErroAutenticacao, ErroNaoEncontrado
from src.modelos import Usuario
from src.repositorios.repositorio_usuario import RepositorioUsuario
from src.validadores import (
    validar_email,
    validar_nome,
    validar_perfil,
    validar_senha,
)


class ServicoAutenticacao:
    """Coordena regras de registro e login de clientes e anunciantes."""

    def __init__(self, repositorio_usuario: RepositorioUsuario) -> None:
        self.repositorio_usuario = repositorio_usuario

    def cadastrar_usuario(
        self,
        nome: str,
        email: str,
        senha: str,
        perfil: str,
    ) -> Usuario:
        """Valida os dados cadastrais, gera hash da senha e cria a conta."""
        nome_limpo = validar_nome(nome)
        email_limpo = validar_email(email)
        senha_valida = validar_senha(senha)
        perfil_valido = validar_perfil(perfil)

        existente = self.repositorio_usuario.buscar_por_email(email_limpo)
        if existente is not None:
            raise ErroAutenticacao("Este endereço de e-mail já está cadastrado.")

        novo_usuario = Usuario(
            nome=nome_limpo,
            email=email_limpo,
            senha_hash=generate_password_hash(senha_valida),
            perfil=perfil_valido,
            saldo=Decimal("0.00"),
        )
        return self.repositorio_usuario.criar(novo_usuario)

    def autenticar(self, email: str, senha: str) -> Usuario:
        """Verifica credenciais de acesso e retorna o usuário autenticado."""
        email_limpo = validar_email(email)
        if not isinstance(senha, str) or not senha:
            raise ErroAutenticacao("E-mail ou senha incorretos.")

        usuario = self.repositorio_usuario.buscar_por_email(email_limpo)
        if usuario is None or not check_password_hash(usuario.senha_hash, senha):
            raise ErroAutenticacao("E-mail ou senha incorretos.")
        return usuario

    def obter_usuario(self, usuario_id: int) -> Usuario:
        """Retorna um usuário pelo ID ou lança erro caso não exista."""
        usuario = self.repositorio_usuario.buscar_por_id(usuario_id)
        if usuario is None:
            raise ErroNaoEncontrado("Usuário não encontrado.")
        return usuario