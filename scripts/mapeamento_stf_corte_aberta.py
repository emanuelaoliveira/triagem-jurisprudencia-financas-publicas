# -*- coding: utf-8 -*-
"""
Mapeia o histórico do STF (2000-presente) usando os dados abertos do Corte
Aberta, classificando por tema de finanças públicas — mesma lista de 20 temas
usada no TCU.

IMPORTANTE — o que isso NÃO faz: não traz o texto da ementa/decisão (o site de
busca do STF bloqueia acesso automático). O resultado é uma LISTA de processos
candidatos (número, classe, relator, link, temas) pra depois buscar o texto de
cada um manualmente/pontualmente — ver "limitacoes jurisprudencia STF.docx".

Pré-requisito: conta Google Cloud configurada. Ver SETUP_STF_CORTE_ABERTA.md.

Uso:
    python -m scripts.mapeamento_stf_corte_aberta --project SEU_PROJETO_GCP
    (ou defina a variável de ambiente GOOGLE_CLOUD_PROJECT e rode sem --project)
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from armazenamento.db import Decisao, conexao, salvar, contar
from classificador.classificador import classifica
from fetchers.stf_corte_aberta import ORGAO, consultar_decisoes, texto_para_classificar

NOTA_SEM_TEXTO = (
    "[Texto completo não disponível pelo Corte Aberta — esta é só a metadado "
    "processual. Consulte o link para o número do processo e busque o texto "
    "manualmente no site do STF.]"
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--project",
        default=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        help="ID do projeto Google Cloud (ou defina GOOGLE_CLOUD_PROJECT)",
    )
    args = ap.parse_args()

    if not args.project:
        ap.error(
            "Falta o projeto do Google Cloud. Passe --project SEU_PROJETO ou "
            "defina a variável de ambiente GOOGLE_CLOUD_PROJECT. "
            "Ver SETUP_STF_CORTE_ABERTA.md para criar um (é gratuito)."
        )

    print(f"=== Mapeamento histórico STF (Corte Aberta) — projeto GCP: {args.project} ===")
    print("Consultando basedosdados.br_stf_corte_aberta.decisoes (pode levar alguns minutos)...")

    total = 0
    encontrados = 0
    agora = dt.datetime.now().isoformat(timespec="seconds")

    with conexao() as con:
        for linha in consultar_decisoes(args.project):
            total += 1
            resultado = classifica(*texto_para_classificar(linha))
            if not resultado.eh_financas_publicas:
                continue
            encontrados += 1

            classe = linha.get("classe") or ""
            numero = linha.get("numero") or ""
            ano = linha.get("ano")
            key_fonte = f"{classe}-{numero}-{ano}".strip("-") or f"linha-{total}"

            d = Decisao(
                orgao=ORGAO,
                key_fonte=key_fonte,
                tipo=classe,
                titulo=f"{classe} {numero}".strip(),
                numero=numero,
                ano=str(ano) if ano is not None else None,
                colegiado=None,
                relator=linha.get("relator"),
                data_sessao=str(linha.get("data_decisao")) if linha.get("data_decisao") else None,
                assunto=linha.get("assunto_processo"),
                ementa=NOTA_SEM_TEXTO,
                url=linha.get("link"),
                temas=resultado.temas_encontrados,
                data_coleta=agora,
            )
            salvar(con, d)
            if encontrados % 200 == 0:
                print(f"\r  {total} processos lidos, {encontrados} sobre finanças públicas...", end="")

    print(f"\r  {total} processos lidos, {encontrados} sobre finanças públicas.        ")

    with conexao() as con:
        no_banco = contar(con, ORGAO)

    print(f"\nResumo: {total} processos do STF lidos (2000-presente), {encontrados} "
          f"classificados como finanças públicas nesta execução. Total acumulado "
          f"no banco (STF): {no_banco}.")
    print("\nLembrete: estes registros NÃO têm o texto da decisão — só o link do "
          "processo. O próximo passo é buscar o texto de cada um, manualmente, no "
          "site do STF (ou decidir, com o Flávio, se vale buscar todos ou só os "
          "mais relevantes).")


if __name__ == "__main__":
    main()
