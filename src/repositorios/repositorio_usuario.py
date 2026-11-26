"""Repositório de persistência de usuários e controle de saldo."""

from decimal import Decimal
import sqlite3
from typing import Optional

from src.banco import BancoDados
from src.excecoes import ErroAutenticacao, ErroNaoEncontrado
from src.modelos import Usuario
from src.validadores import centavos_para_decimal, decimal_para_centavos


class RepositorioUsuario:
    """Realiza operações de leitura e gravação da entidade Usuario."""

    def __init__(self, banco: BancoDados) -> None:
        self.banco = banco

    @staticmethod
    def _linha_para_usuario(linha: sqlite3.Row) -> Usuario:
        return Usuario(
            id=linha["id"],
            nome=linha["nome"],
            email=linha["email"],
            senha_hash=linha["senha_hash"],
            perfil=linha["perfil"],
            saldo=centavos_para_decimal(linha["saldo_centavos"]),
        )

    def criar(self, usuario: Usuario) -> Usuario:
        """Insere um novo usuário no banco de dados."""
        saldo_centavos = decimal_para_centavos(usuario.saldo)
        try:
            with self.banco.transacao() as conexao:
                cursor = conexao.execute(
                    """
                    INSERT INTO usuarios (nome, email, senha_hash, perfil, saldo_centavos)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        usuario.nome,
                        usuario.email,
                        usuario.senha_hash,
                        usuario.perfil,
                        saldo_centavos,
                    ),
                )
                novo_id = cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ErroAutenticacao("Este endereço de e-mail já está cadastrado.") from exc

        return Usuario(
            id=novo_id,
            nome=usuario.nome,
            email=usuario.email,
            senha_hash=usuario.senha_hash,
            perfil=usuario.perfil,
            saldo=usuario.saldo,
        )

    def buscar_por_id(self, usuario_id: int) -> Optional[Usuario]:
        """Busca um usuário pelo identificador numérico."""
        with self.banco.transacao() as conexao:
            linha = conexao.execute(
                "SELECT * FROM usuarios WHERE id = ?",
                (usuario_id,),
            ).fetchone()
        return self._linha_para_usuario(linha) if linha else None

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        """Busca um usuário pelo e-mail normalizado."""
        with self.banco.transacao() as conexao:
            linha = conexao.execute(
                "SELECT * FROM usuarios WHERE email = ?",
                (email.strip().lower(),),
            ).fetchone()
        return self._linha_para_usuario(linha) if linha else None

    def adicionar_saldo(
        self,
        usuario_id: int,
        valor: Decimal,
        conexao: Optional[sqlite3.Connection] = None,
    ) -> None:
        """Incrementa o saldo a receber de um anunciante de forma atômica."""
        acrescimo = decimal_para_centavos(valor)
        sql = """
            UPDATE usuarios
            SET saldo_centavos = saldo_centavos + ?
            WHERE id = ? AND perfil = 'anunciante'
        """
        if conexao is not None:
            cursor = conexao.execute(sql, (acrescimo, usuario_id))
            if cursor.rowcount == 0:
                raise ErroNaoEncontrado("Anunciante não encontrado para crédito de saldo.")
            return

        with self.banco.transacao() as nova_conexao:
            cursor = nova_conexao.execute(sql, (acrescimo, usuario_id))
            if cursor.rowcount == 0:
                raise ErroNaoEncontrado("Anunciante não encontrado para crédito de saldo.")