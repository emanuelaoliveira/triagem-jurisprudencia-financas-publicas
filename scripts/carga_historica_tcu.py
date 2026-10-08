# -*- coding: utf-8 -*-
"""
Carga histórica de acórdãos do TCU: baixa os CSVs anuais oficiais,
classifica por tema de finanças públicas e guarda no banco local
só o que casou com algum tema.

Uso:
    python -m scripts.carga_historica_tcu 2024 2025 2026
    python -m scripts.carga_historica_tcu --desde 2017 --ate 2026
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from armazenamento.db import Decisao, conexao, salvar, contar
from classificador.classificador import classifica
from fetchers.tcu import ORGAO, baixar_csv_ano, iterar_acordaos_csv, texto_para_classificar


def processa_ano(ano: int, forcar: bool = False) -> tuple[int, int]:
    print(f"\n== TCU {ano} ==")
    caminho = baixar_csv_ano(ano, forcar=forcar)
    total = 0
    encontrados = 0
    agora = dt.datetime.now().isoformat(timespec="seconds")
    with conexao() as con:
        for linha in iterar_acordaos_csv(caminho):
            total += 1
            resultado = classifica(*texto_para_classificar(linha))
            if not resultado.eh_financas_publicas:
                continue
            encontrados += 1
            d = Decisao(
                orgao=ORGAO,
                key_fonte=linha.get("KEY", ""),
                tipo=linha.get("TIPO"),
                titulo=linha.get("TITULO"),
                numero=linha.get("NUMACORDAO"),
                ano=linha.get("ANOACORDAO"),
                colegiado=linha.get("COLEGIADO"),
                relator=linha.get("RELATOR"),
                data_sessao=linha.get("DATASESSAO"),
                assunto=linha.get("ASSUNTO"),
                ementa=linha.get("SUMARIO") or linha.get("DECISAO"),
                url=f"https://pesquisa.apps.tcu.gov.br/redireciona/acordao-completo/{linha.get('KEY','')}",
                temas=resultado.temas_encontrados,
                data_coleta=agora,
            )
            salvar(con, d)
            if encontrados % 200 == 0:
                print(f"\r  {total} lidos, {encontrados} sobre finanças públicas...", end="")
    print(f"\r  {total} lidos, {encontrados} sobre finanças públicas.        ")
    return total, encontrados


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("anos", nargs="*", type=int, help="anos específicos, ex: 2024 2025")
    ap.add_argument("--desde", type=int, help="ano inicial de um intervalo")
    ap.add_argument("--ate", type=int, help="ano final de um intervalo (padrão: ano atual)")
    args = ap.parse_args()

    if args.desde:
        ate = args.ate or dt.date.today().year
        anos = list(range(args.desde, ate + 1))
    elif args.anos:
        anos = args.anos
    else:
        anos = [dt.date.today().year]

    total_geral = encontrados_geral = 0
    for ano in anos:
        t, e = processa_ano(ano)
        total_geral += t
        encontrados_geral += e

    with conexao() as con:
        no_banco = contar(con, ORGAO)

    print(f"\nResumo: {total_geral} acórdãos lidos, {encontrados_geral} classificados como "
          f"finanças públicas nesta execução. Total acumulado no banco (TCU): {no_banco}.")


if __name__ == "__main__":
    main()
