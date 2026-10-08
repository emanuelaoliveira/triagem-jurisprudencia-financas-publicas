# -*- coding: utf-8 -*-
"""
Atualização semanal do TCU: baixa de novo o CSV do ano corrente (os acórdãos
mudam/são oficializados com o tempo), reclassifica e atualiza o banco local
(upsert — não duplica), depois regenera a planilha Excel e o portal web.

Este script é 100% independente (não depende do Claude nem de e-mail) — pode
rodar sozinho, por isso é a parte da rotina semanal que dá pra agendar de
verdade (cron, Agendador de Tarefas, ou só rodar manualmente 1x por semana).

Uso:
    python -m scripts.atualizacao_semanal_tcu
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from armazenamento.db import conexao, contar
from exporta.exportar_excel import exportar
from portal.gerar_portal import gerar as gerar_portal
from scripts.carga_historica_tcu import processa_ano


def main() -> None:
    ano_atual = dt.date.today().year
    print(f"=== Atualização semanal TCU — {dt.datetime.now():%d/%m/%Y %H:%M} ===")

    # Reforça o ano corrente (acórdãos recentes são oficializados aos poucos).
    # Em janeiro, reforça também o ano anterior, por segurança (virada de ano).
    anos = [ano_atual] if dt.date.today().month > 1 else [ano_atual - 1, ano_atual]

    total_geral = encontrados_geral = 0
    for ano in anos:
        t, e = processa_ano(ano, forcar=True)
        total_geral += t
        encontrados_geral += e

    with conexao() as con:
        no_banco = contar(con, "TCU")

    n_excel = exportar()
    n_portal = gerar_portal()

    print(f"\nResumo: {total_geral} acórdãos lidos, {encontrados_geral} classificados "
          f"nesta execução. Total acumulado no banco (TCU): {no_banco}.")
    print(f"Planilha atualizada: {n_excel} decisões. Portal atualizado: {n_portal} decisões.")


if __name__ == "__main__":
    main()
