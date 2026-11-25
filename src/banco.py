"""Gerenciamento de conexão e esquema SQLite da plataforma."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

ESQUEMA_SQL = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL CHECK (perfil IN ('cliente', 'anunciante')),
    saldo_centavos INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anunciante_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL DEFAULT '',
    preco_centavos INTEGER NOT NULL CHECK (preco_centavos > 0),
    estoque INTEGER NOT NULL CHECK (estoque >= 0),
    categoria TEXT NOT NULL DEFAULT 'Outros',
    imagem_url TEXT NOT NULL DEFAULT '',
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (anunciante_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    total_centavos INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pago',
    codigo_transacao TEXT NOT NULL DEFAULT '',
    criado_em TEXT NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    anunciante_id INTEGER NOT NULL,
    titulo_produto TEXT NOT NULL,
    preco_unitario_centavos INTEGER NOT NULL,
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
    FOREIGN KEY (produto_id) REFERENCES produtos (id),
    FOREIGN KEY (anunciante_id) REFERENCES usuarios (id)
);
"""


class BancoDados:
    """Encapsula o acesso ao banco SQLite e o controle transacional."""

    def __init__(self, caminho_banco: str) -> None:
        self.caminho_banco = caminho_banco
        if caminho_banco != ":memory:":
            Path(caminho_banco).parent.mkdir(parents=True, exist_ok=True)
        self._conexao_memoria: sqlite3.Connection | None = None
        if caminho_banco == ":memory:":
            self._conexao_memoria = self._criar_conexao()

    def _criar_conexao(self) -> sqlite3.Connection:
        conexao = sqlite3.connect(self.caminho_banco, check_same_thread=False)
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON;")
        return conexao

    def conectar(self) -> sqlite3.Connection:
        """Retorna uma conexão configurada com suporte a chaves estrangeiras."""
        if self._conexao_memoria is not None:
            return self._conexao_memoria
        return self._criar_conexao()

    @contextmanager
    def transacao(self) -> Iterator[sqlite3.Connection]:
        """Abre um bloco transacional realizando commit automático ou rollback em erro."""
        conexao = self.conectar()
        try:
            yield conexao
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            if self._conexao_memoria is None:
                conexao.close()

    def inicializar(self) -> None:
        """Cria as tabelas necessárias caso ainda não existam."""
        with self.transacao() as conexao:
            conexao.executescript(ESQUEMA_SQL)

    def fechar(self) -> None:
        """Fecha a conexão persistente em memória, quando utilizada."""
        if self._conexao_memoria is not None:
            self._conexao_memoria.close()
            self._conexao_memoria = None