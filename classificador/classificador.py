# -*- coding: utf-8 -*-
"""
Classificador por palavra-chave: decide se um texto de jurisprudência
trata de finanças públicas, e aponta quais temas da lista foram encontrados.

É a "primeira camada" do critério pedido pelo Flávio (ver config/temas_financas_publicas.py).
Uma segunda camada por IA (para confirmar casos duvidosos) pode ser plugada depois,
sem mudar a interface desta função — ver `classifica()`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from config.temas_financas_publicas import TEMAS


@lru_cache(maxsize=None)
def _padroes_compilados() -> dict[str, list[re.Pattern]]:
    return {
        tema: [re.compile(p, re.IGNORECASE) for p in padroes]
        for tema, padroes in TEMAS.items()
    }


@dataclass
class ResultadoClassificacao:
    eh_financas_publicas: bool
    temas_encontrados: list[str] = field(default_factory=list)


def classifica(*textos: str | None) -> ResultadoClassificacao:
    """Recebe um ou mais textos (ementa, assunto, sumário, relatório, voto...)
    e devolve quais temas de finanças públicas foram encontrados.

    Usa apenas os textos passados; texto None ou vazio é ignorado.
    """
    texto_completo = "\n".join(t for t in textos if t)
    if not texto_completo.strip():
        return ResultadoClassificacao(eh_financas_publicas=False)

    temas_encontrados = [
        tema
        for tema, padroes in _padroes_compilados().items()
        if any(p.search(texto_completo) for p in padroes)
    ]
    return ResultadoClassificacao(
        eh_financas_publicas=bool(temas_encontrados),
        temas_encontrados=temas_encontrados,
    )
