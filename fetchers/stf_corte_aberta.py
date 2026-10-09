# -*- coding: utf-8 -*-
"""
Mapeamento histórico do STF via "Corte Aberta" (dados abertos oficiais do STF,
Resolução 774/2022), espelhado gratuitamente na plataforma Base dos Dados.

Isso NÃO traz o texto da ementa/decisão (o site de busca do STF bloqueia acesso
automático — ver limitacoes jurisprudencia STF.docx). O que esta base tem é
metadado processual (classe, número, relator, assunto, ramo do direito, link)
desde 2000 — o suficiente pra descobrir QUAIS processos históricos são de
finanças públicas, usando o mesmo classificador por palavra-chave do TCU.

Pré-requisito: uma conta Google Cloud com um projeto criado (gratuito — consultar
esta base fica muito abaixo da cota grátis do BigQuery). Ver SETUP_STF_CORTE_ABERTA.md
na raiz do projeto para o passo a passo.

Tabela: basedosdados.br_stf_corte_aberta.decisoes
Documentação: https://basedosdados.org/dataset/b46bb892-3273-434d-9335-f502b8656ef1
"""
from __future__ import annotations

from typing import Iterator

ORGAO = "STF"

TABELA = "basedosdados.br_stf_corte_aberta.decisoes"

# Colunas que realmente precisamos (evita baixar colunas pesadas/irrelevantes
# como observacao_andamento_decisao, meio_tramitacao etc.)
COLUNAS = [
    "ano", "classe", "numero", "relator", "link",
    "assunto_processo", "ramo_direito", "data_decisao",
]


def consultar_decisoes(project_id: str) -> Iterator[dict]:
    """Consulta todas as linhas da tabela Corte Aberta (só as colunas que
    usamos) e devolve um dict por linha. Requer `google-cloud-bigquery`
    instalado e credenciais configuradas (gcloud auth application-default
    login) — ver requirements-stf.txt e SETUP_STF_CORTE_ABERTA.md.
    """
    from google.cloud import bigquery  # import local: dependência opcional

    cliente = bigquery.Client(project=project_id)
    colunas_sql = ", ".join(COLUNAS)
    consulta = f"SELECT {colunas_sql} FROM `{TABELA}`"
    resultado = cliente.query(consulta).result()
    for linha in resultado:
        yield dict(linha.items())


def texto_para_classificar(linha: dict) -> tuple[str, ...]:
    """Campos usados pra decidir o tema: assunto do processo + ramo do direito.
    (Não há ementa nesta base — ver módulo docstring.)
    """
    return (
        linha.get("assunto_processo") or "",
        linha.get("ramo_direito") or "",
    )
