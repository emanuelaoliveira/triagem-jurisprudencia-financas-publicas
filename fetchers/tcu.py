# -*- coding: utf-8 -*-
"""
Coleta de jurisprudência do TCU.

O TCU disponibiliza dados abertos oficiais (sem bloqueio de robô):
- CSVs anuais com o texto completo dos acórdãos (para carga histórica);
- um webservice paginado com os acórdãos mais recentes (para atualização semanal).

Documentação: https://sites.tcu.gov.br/dados-abertos/webservices-tcu/
              https://sites.tcu.gov.br/dados-abertos/jurisprudencia/
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Iterator

import requests

ORGAO = "TCU"

URL_CSV_ANO = (
    "https://sites.tcu.gov.br/dados-abertos/jurisprudencia/arquivos/"
    "acordao-completo/acordao-completo-{ano}.csv"
)
URL_API_RECENTES = "https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos"

PASTA_BRUTOS = Path(__file__).resolve().parent.parent / "dados" / "brutos" / "tcu"

# csv com campos de texto muito longos (relatório/voto inteiros) precisa de limite maior
csv.field_size_limit(sys.maxsize)


def caminho_csv_ano(ano: int) -> Path:
    return PASTA_BRUTOS / f"acordao-completo-{ano}.csv"


def baixar_csv_ano(ano: int, forcar: bool = False) -> Path:
    """Baixa (se ainda não tiver) o CSV anual de acórdãos completos do TCU."""
    destino = caminho_csv_ano(ano)
    if destino.exists() and not forcar:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    url = URL_CSV_ANO.format(ano=ano)
    tmp = destino.with_suffix(".tmp")
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        lido = 0
        with open(tmp, "wb") as f:
            for pedaco in resp.iter_content(chunk_size=1024 * 1024):
                f.write(pedaco)
                lido += len(pedaco)
                if total:
                    print(f"\r  baixando {ano}: {lido / 1e6:.0f}/{total / 1e6:.0f} MB", end="")
        print()
    tmp.rename(destino)
    return destino


def iterar_acordaos_csv(caminho: Path) -> Iterator[dict]:
    """Lê um CSV anual de acórdãos e devolve um dict por linha (acórdão)."""
    with open(caminho, encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f, delimiter="|", quotechar='"')
        yield from leitor


def buscar_recentes_api(inicio: int = 0, quantidade: int = 100) -> list[dict]:
    """Consulta o webservice oficial de acórdãos recentes (usado na atualização semanal)."""
    resp = requests.get(
        URL_API_RECENTES,
        params={"inicio": inicio, "quantidade": quantidade},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def texto_para_classificar(linha: dict) -> tuple[str, ...]:
    """Campos do CSV usados para decidir o tema.

    O TCU não tem uma "ementa" separada como o STF; usamos ASSUNTO, SUMARIO e
    DECISAO (o dispositivo). Muitos acórdãos administrativos em lote (ex.:
    aposentadorias) vêm com ASSUNTO/SUMARIO vazios — nesse caso caímos para um
    trecho do RELATORIO, para não perder decisões relevantes só por falta de
    resumo.
    """
    assunto = linha.get("ASSUNTO") or ""
    sumario = linha.get("SUMARIO") or ""
    decisao = linha.get("DECISAO") or ""
    if assunto or sumario:
        return (assunto, sumario, decisao)
    relatorio = linha.get("RELATORIO") or ""
    return (assunto, sumario, decisao, relatorio[:5000])
