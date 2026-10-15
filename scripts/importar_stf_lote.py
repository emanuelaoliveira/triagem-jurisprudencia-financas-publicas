# -*- coding: utf-8 -*-
"""
Importa um lote de decisões do STF (extraídas manualmente via Browser tool,
da busca de Jurisprudência do STF por tema) para o banco local, classificando
pelos 20 temas de finanças públicas.

Cada lote é um arquivo JSON numa lista de objetos:
    {titulo, relator, julgamento (dd/mm/aaaa), publicacao, url?,
     acompanhamento?, ementa}

Uso:
    .venv/bin/python3 -m scripts.importar_stf_lote dados/entrada/stf/<arquivo>.json
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from armazenamento.db import Decisao, conexao, salvar, contar
from classificador.classificador import classifica

NOTA_RE = re.compile(r"\s*NOTA:.*$", re.DOTALL)


def limpar_ementa(texto: str) -> str:
    """Remove eventuais anotações próprias (NOTA: ...) que não fazem parte
    do texto oficial da decisão."""
    return NOTA_RE.sub("", texto).strip()


def para_iso(data_br: str | None) -> str | None:
    if not data_br:
        return None
    try:
        return dt.datetime.strptime(data_br, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def importar(caminho_json: str) -> tuple[int, int]:
    itens = json.loads(Path(caminho_json).read_text(encoding="utf-8"))
    agora = dt.datetime.now().isoformat(timespec="seconds")

    total = 0
    salvos = 0
    with conexao() as con:
        for item in itens:
            total += 1
            ementa = limpar_ementa(item["ementa"])
            resultado = classifica(ementa)
            if not resultado.eh_financas_publicas:
                print(f"  [fora do escopo] {item['titulo']}")
                continue

            titulo = item["titulo"]
            m = re.match(r"^([A-Za-zÀ-ú]+)", titulo)
            classe = m.group(1) if m else None
            numero_m = re.search(r"(\d+)", titulo)
            numero = numero_m.group(1) if numero_m else None
            ano = item["julgamento"].split("/")[-1] if item.get("julgamento") else None

            url = item.get("url") or item.get("acompanhamento")

            d = Decisao(
                orgao="STF",
                key_fonte=titulo.replace(" ", "-"),
                tipo=classe,
                titulo=titulo,
                numero=numero,
                ano=ano,
                colegiado=None,
                relator=item.get("relator"),
                data_sessao=para_iso(item.get("julgamento")),
                assunto=None,
                ementa=ementa,
                url=url,
                temas=resultado.temas_encontrados,
                data_coleta=agora,
            )
            salvar(con, d)
            salvos += 1
            print(f"  [OK] {titulo} -> {resultado.temas_encontrados}")

    with conexao() as con:
        no_banco = contar(con, "STF")

    print(f"\nResumo: {total} itens lidos, {salvos} salvos como finanças públicas. "
          f"Total acumulado no banco (STF): {no_banco}.")
    return total, salvos


if __name__ == "__main__":
    importar(sys.argv[1])
