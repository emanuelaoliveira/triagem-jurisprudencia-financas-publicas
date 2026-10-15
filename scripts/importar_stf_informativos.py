# -*- coding: utf-8 -*-
"""
Importa o arquivo "Dados_InformativosSTF.xlsx" (planilha oficial do STF com o
resumo estruturado de todas as decisões já publicadas no Informativo STF,
baixada manualmente pela Emanuela em sessão ao vivo, via
https://portal.stf.jus.br/textos/verTexto.asp?servico=informativoSTF) para o
banco local, classificando pelos 20 temas de finanças públicas.

Cada linha da aba "dados" é uma decisão mencionada num Informativo, já com
Tese Julgado + Resumo (texto curado pelo próprio STF) — por isso não precisa
do método de busca por tema no site (que é mais trabalhoso e sofre bloqueio
anti-robô). Este arquivo é estático e também passa pela mesma proteção, então
precisa ser baixado manualmente de novo quando quisermos atualizar.

Uso:
    .venv/bin/python3 -m scripts.importar_stf_informativos <caminho.xlsx> [anos]

`anos` (opcional, padrão 10): só importa decisões com Data Julgamento dentro
dos últimos N anos a partir de hoje.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from armazenamento.db import Decisao, conexao, contar, salvar
from classificador.classificador import classifica


def importar(caminho_xlsx: str, anos: int = 10, corte: dt.date | None = None) -> tuple[int, int, int]:
    if corte is None:
        hoje = dt.date.today()
        corte = hoje.replace(year=hoje.year - anos)
    agora = dt.datetime.now().isoformat(timespec="seconds")

    wb = openpyxl.load_workbook(caminho_xlsx, read_only=True, data_only=True)
    ws = wb["dados"]
    linhas = ws.iter_rows(min_row=2, values_only=True)

    total = 0
    dentro_do_periodo = 0
    salvos = 0

    with conexao() as con:
        for r in linhas:
            total += 1
            informativo, classe, numero = r[0], r[1], r[2]
            incidente = r[3]
            data_julgamento = r[6]
            relator = r[7]
            orgao_julgador = r[9]
            titulo_curto = r[12]
            tese = r[13]
            resumo = r[14]
            materia = r[17]

            if not data_julgamento:
                continue
            data_sessao = data_julgamento.date() if hasattr(data_julgamento, "date") else data_julgamento
            if data_sessao < corte:
                continue
            dentro_do_periodo += 1

            resultado = classifica(titulo_curto, tese, resumo, materia)
            if not resultado.eh_financas_publicas:
                continue

            titulo = f"{classe} {numero}" + (f" {incidente}" if incidente else "")
            ementa = "\n\n".join(t for t in (tese, resumo) if t)

            d = Decisao(
                orgao="STF",
                key_fonte=f"info-{informativo}-{classe}-{numero}-{incidente or 'NA'}",
                tipo=classe,
                titulo=titulo,
                numero=str(numero) if numero is not None else None,
                ano=str(data_sessao.year),
                colegiado=orgao_julgador,
                relator=relator,
                data_sessao=data_sessao.isoformat(),
                assunto=titulo_curto,
                ementa=ementa,
                url=None,
                temas=resultado.temas_encontrados,
                data_coleta=agora,
            )
            salvar(con, d)
            salvos += 1

    with conexao() as con:
        no_banco = contar(con, "STF")

    print(
        f"Total de linhas na planilha: {total}\n"
        f"Dentro do período (desde {corte.isoformat()}): {dentro_do_periodo}\n"
        f"Classificadas como finanças públicas e salvas: {salvos}\n"
        f"Total acumulado no banco (STF): {no_banco}."
    )
    return total, dentro_do_periodo, salvos


if __name__ == "__main__":
    caminho = sys.argv[1]
    if len(sys.argv) > 2 and "-" in sys.argv[2]:
        importar(caminho, corte=dt.date.fromisoformat(sys.argv[2]))
    else:
        anos = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        importar(caminho, anos)
