# -*- coding: utf-8 -*-
"""Utilidades compartilhadas pelos importadores de STF."""
from __future__ import annotations

from urllib.parse import quote


def url_busca_stf(titulo: str) -> str:
    """Monta um link para a Pesquisa de Jurisprudência do STF já buscando
    pelo número do processo (ex: "ARE 1465015 AgR"), para servir de link
    "ver decisão" quando não temos a URL exata do processo."""
    return (
        "https://jurisprudencia.stf.jus.br/pages/search"
        "?base=acordaos&sinonimo=true&plural=true&radicais=false&buscaExata=true"
        f"&page=1&pageSize=10&queryString={quote(titulo)}&sort=date&sortBy=desc"
    )
