# -*- coding: utf-8 -*-
"""
Lista de temas de finanças públicas e os termos usados para reconhecê-los
no texto das decisões (ementa, sumário, assunto, relatório, voto...).

Baseado no escopo definido por Flávio em 2026-09-12 (ver Escopo.docx).

Cada tema tem uma lista de "padrões" (expressões regulares, case-insensitive).
Um documento é considerado "finanças públicas" se casar com pelo menos um
padrão de pelo menos um tema. Os temas casados ficam registrados junto com
a decisão, para facilitar a consulta por assunto no portal/planilha.
"""

TEMAS: dict[str, list[str]] = {
    "LRF": [
        r"\bLRF\b",
        r"lei de responsabilidade fiscal",
        r"lei complementar\s*n?[ºo°]?\s*101/2000",
        r"lei complementar\s*n?[ºo°]?\s*101,?\s*de\s*2000",
    ],
    "Orçamento público": [
        r"orçamento p[uú]blico",
        r"lei orçament[aá]ria anual",
        r"\bLOA\b",
        r"plano plurianual",
        r"\bPPA\b",
        r"lei de diretrizes orçament[aá]rias",
        r"\bLDO\b",
    ],
    "Execução orçamentária e financeira": [
        r"execu[cç][aã]o or[cç]ament[aá]ria",
        r"execu[cç][aã]o financeira",
    ],
    "Créditos adicionais": [
        r"cr[eé]dito[s]? adicion(al|ais)",
        r"cr[eé]dito[s]? suplementar(es)?",
        r"cr[eé]dito[s]? especi(al|ais)",
        r"cr[eé]dito[s]? extraordin[aá]rio[s]?",
        r"abertura de cr[eé]dito",
    ],
    "Emendas parlamentares": [
        r"emenda[s]? parlamentar(es)?",
        r"emenda[s]? de bancada",
        r"emenda[s]? de relator",
        r"emenda[s]? individu(al|ais)",
        r"\bRP[- ]?[6-9]\b",
    ],
    "Despesas com pessoal": [
        r"despesa[s]? (total )?com pessoal",
        r"limite[s]? (m[aá]ximo[s]? )?(de|com) (despesa|gasto)[s]? (de|com) pessoal",
        r"gasto[s]? com pessoal",
    ],
    "Renúncia de receita / benefícios tributários": [
        r"ren[uú]ncia[s]? (fiscal|de receita)",
        r"benef[ií]cio[s]? tribut[aá]rio[s]?",
        r"incentivo[s]? fiscal(is)?",
        r"isen[cç][aã]o (fiscal|tribut[aá]ria)",
    ],
    "Dívida pública e operações de crédito": [
        r"d[ií]vida p[uú]blica",
        r"opera[cç][aã]o(?:ões)? de cr[eé]dito",
        r"endividamento p[uú]blico",
        r"limite[s]? de endividamento",
    ],
    "Precatórios": [
        r"precat[oó]rio[s]?",
        r"requisi[cç][aã]o de pequeno valor",
        r"\bRPV\b",
    ],
    "Transferências intergovernamentais": [
        r"transfer[eê]ncia[s]? (intergovernamental(is)?|volunt[aá]ria[s]?|obrigat[oó]ria[s]?|constitucional(is)?|legal(is)?)",
        r"conv[eê]nio[s]? (de repasse|federativo[s]?)",
        r"\bFPM\b",
        r"\bFPE\b",
    ],
    "Fundos públicos": [
        r"fundo[s]? p[uú]blico[s]?",
        r"fundo[s]? especial(is)?",
        r"fundo[s]? de participa[cç][aã]o",
    ],
    "Vinculações constitucionais": [
        r"vincula[cç][aã]o(?:ões)? constitucional(is)?",
        r"vincula[cç][aã]o(?:ões)? de receita[s]?",
        r"aplica[cç][aã]o m[ií]nima em (sa[uú]de|educa[cç][aã]o)",
        r"\bEC\s*29\b",
        r"\bEC\s*95\b",
    ],
    "Regras fiscais": [
        r"regra[s]? fisc(al|ais)",
        r"teto de gastos",
        r"novo regime fiscal",
        r"arcabou[cç]o fiscal",
    ],
    "Responsabilidade fiscal": [
        r"responsabilidade fiscal",
        r"gest[aã]o fiscal respons[aá]vel",
    ],
    "Controle e fiscalização da execução orçamentária": [
        r"fiscaliza[cç][aã]o (da execu[cç][aã]o )?or[cç]ament[aá]ria",
        r"controle (externo|interno) (da|na) execu[cç][aã]o or[cç]ament[aá]ria",
    ],
    "Impacto orçamentário e financeiro de proposições": [
        r"impacto or[cç]ament[aá]rio(?:\s*e financeiro)?",
        r"impacto financeiro",
        r"estimativa de impacto or[cç]ament[aá]rio",
    ],
    "Subsídios e subvenções": [
        r"subs[ií]dio[s]?",
        r"subven[cç][aã]o(?:ões)?",
    ],
    "Restos a pagar": [
        r"restos a pagar",
        r"\bRPP\b",
        r"\bRPNP\b",
    ],
    "Contingenciamento": [
        r"contingenciamento",
        r"limita[cç][aã]o de empenho",
    ],
    "Receitas públicas e repartição de receitas": [
        r"receita[s]? p[uú]blica[s]?",
        r"receita[s]? corrente[s]? l[ií]quida[s]?",
        r"\bRCL\b",
        r"reparti[cç][aã]o de receita[s]?",
        r"receita[s]? tribut[aá]ria[s]?",
    ],
}

# Exceções: padrões que, quando presentes perto de um "match" do tema, indicam
# falso positivo e cancelam a classificação naquele tema (mas não nos demais).
#
# 2026-09-12: a Emanuela pediu para excluir o caso de "subsídio" como regime de
# remuneração de servidor/agente político (art. 39, §4º da CF) — isso não é
# "subsídio" no sentido de finanças públicas (subvenção/incentivo econômico)
# que o Flávio quis dizer.
EXCLUSOES: dict[str, list[str]] = {
    "Subsídios e subvenções": [
        r"subs[ií]dio[s]?\s+(mensal|[uú]nico|remunerat[oó]rio[s]?)",
        r"remunerad[oa]?[s]?\s+por\s+subs[ií]dio",
        r"regime de subs[ií]dio",
        r"subs[ií]dio.{0,60}(servidor|agente pol[ií]tico|cargo|vencimento|remunera[cç][aã]o|remunerat[oó]ri)",
        r"(servidor|agente pol[ií]tico|cargo|vencimento|remunera[cç][aã]o|remunerat[oó]ri).{0,60}subs[ií]dio",
        r"art\.?\s*39.{0,15}§\s*4",
    ],
}
