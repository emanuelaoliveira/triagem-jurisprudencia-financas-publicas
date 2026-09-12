# -*- coding: utf-8 -*-
"""
Banco de dados local (SQLite) com as decisões já triadas como finanças públicas.

Um único arquivo, sem precisar instalar servidor de banco de dados —
mesmo espírito do restante do projeto: simples de rodar no computador da Emanuela.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

CAMINHO_DB = Path(__file__).resolve().parent.parent / "dados" / "db" / "jurisprudencia.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS decisoes (
    id_unico        TEXT PRIMARY KEY,   -- chave única: "{orgao}:{key_da_fonte}"
    orgao           TEXT NOT NULL,      -- TCU, STF...
    tipo            TEXT,               -- Acórdão, ADI, RE, Súmula...
    titulo          TEXT,
    numero          TEXT,
    ano             TEXT,
    colegiado       TEXT,
    relator         TEXT,
    data_sessao     TEXT,
    assunto         TEXT,
    ementa          TEXT,               -- ementa/sumário usado na classificação
    url             TEXT,
    temas_json      TEXT NOT NULL,      -- lista de temas casados, em JSON
    data_coleta     TEXT NOT NULL       -- quando este registro foi coletado/atualizado
);
CREATE INDEX IF NOT EXISTS idx_decisoes_orgao ON decisoes(orgao);
CREATE INDEX IF NOT EXISTS idx_decisoes_data_sessao ON decisoes(data_sessao);
"""


@contextmanager
def conexao():
    CAMINHO_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CAMINHO_DB)
    try:
        con.executescript(SCHEMA)
        yield con
        con.commit()
    finally:
        con.close()


@dataclass
class Decisao:
    orgao: str
    key_fonte: str
    tipo: str | None
    titulo: str | None
    numero: str | None
    ano: str | None
    colegiado: str | None
    relator: str | None
    data_sessao: str | None
    assunto: str | None
    ementa: str | None
    url: str | None
    temas: list[str]
    data_coleta: str

    @property
    def id_unico(self) -> str:
        return f"{self.orgao}:{self.key_fonte}"


def salvar(con: sqlite3.Connection, d: Decisao) -> None:
    con.execute(
        """
        INSERT INTO decisoes (
            id_unico, orgao, tipo, titulo, numero, ano, colegiado, relator,
            data_sessao, assunto, ementa, url, temas_json, data_coleta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id_unico) DO UPDATE SET
            tipo=excluded.tipo, titulo=excluded.titulo, numero=excluded.numero,
            ano=excluded.ano, colegiado=excluded.colegiado, relator=excluded.relator,
            data_sessao=excluded.data_sessao, assunto=excluded.assunto,
            ementa=excluded.ementa, url=excluded.url, temas_json=excluded.temas_json,
            data_coleta=excluded.data_coleta
        """,
        (
            d.id_unico, d.orgao, d.tipo, d.titulo, d.numero, d.ano, d.colegiado,
            d.relator, d.data_sessao, d.assunto, d.ementa, d.url,
            json.dumps(d.temas, ensure_ascii=False), d.data_coleta,
        ),
    )


def contar(con: sqlite3.Connection, orgao: str | None = None) -> int:
    if orgao:
        cur = con.execute("SELECT COUNT(*) FROM decisoes WHERE orgao = ?", (orgao,))
    else:
        cur = con.execute("SELECT COUNT(*) FROM decisoes")
    return cur.fetchone()[0]
