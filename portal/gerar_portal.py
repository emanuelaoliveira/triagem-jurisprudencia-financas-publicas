# -*- coding: utf-8 -*-
"""
Gera a página web local de consulta (estática — sem precisar manter servidor rodando).

Lê o banco de dados e escreve portal/site/index.html + portal/site/dados.json.
Para abrir: dois cliques em portal/site/index.html.

Uso:
    python -m portal.gerar_portal
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from armazenamento.db import conexao
from config.temas_financas_publicas import TEMAS

PASTA_SITE = Path(__file__).resolve().parent / "site"


def carregar_decisoes() -> list[dict]:
    with conexao() as con:
        cur = con.execute(
            "SELECT orgao, tipo, titulo, numero, ano, colegiado, relator, "
            "data_sessao, temas_json, assunto, ementa, url FROM decisoes "
            "ORDER BY data_sessao DESC"
        )
        campos = ["orgao", "tipo", "titulo", "numero", "ano", "colegiado", "relator",
                  "data_sessao", "temas_json", "assunto", "ementa", "url"]
        decisoes = []
        for row in cur:
            d = dict(zip(campos, row))
            d["temas"] = json.loads(d.pop("temas_json") or "[]")
            decisoes.append(d)
        return decisoes


TEMPLATE_HTML = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jurisprudência — Finanças Públicas</title>
<style>
  :root {
    --azul: #1b3a63; --azul-claro: #2c5a94; --cinza: #f4f5f7; --borda: #dde1e6;
    --texto: #1f2430; --texto-suave: #565f6e;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, "Segoe UI", Arial, sans-serif; color: var(--texto); background: #fff; }
  header { background: var(--azul); color: #fff; padding: 18px 24px; }
  header h1 { margin: 0; font-size: 1.25rem; }
  header p { margin: 4px 0 0; font-size: 0.85rem; color: #cfd9e8; }
  .barra { display: flex; gap: 10px; flex-wrap: wrap; padding: 14px 24px; background: var(--cinza); border-bottom: 1px solid var(--borda); position: sticky; top: 0; }
  .barra input, .barra select { padding: 8px 10px; border: 1px solid var(--borda); border-radius: 6px; font-size: 0.9rem; }
  .barra input[type=search] { flex: 1; min-width: 220px; }
  main { padding: 10px 24px 40px; max-width: 1000px; margin: 0 auto; }
  .contagem { color: var(--texto-suave); font-size: 0.85rem; margin: 10px 0; }
  .card { border: 1px solid var(--borda); border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; }
  .card h2 { margin: 0 0 4px; font-size: 1rem; }
  .card h2 a { color: var(--azul-claro); text-decoration: none; }
  .card h2 a:hover { text-decoration: underline; }
  .meta { font-size: 0.8rem; color: var(--texto-suave); margin-bottom: 8px; }
  .temas { margin-bottom: 8px; }
  .tema-tag { display: inline-block; background: #e8edf5; color: var(--azul); border-radius: 12px; padding: 2px 10px; font-size: 0.72rem; margin: 0 4px 4px 0; }
  .ementa { font-size: 0.88rem; line-height: 1.45; white-space: pre-line; max-height: 6.5em; overflow: hidden; }
  .card.aberto .ementa { max-height: none; }
  .ver-mais { font-size: 0.8rem; color: var(--azul-claro); cursor: pointer; background: none; border: none; padding: 4px 0; }
  .vazio { text-align: center; color: var(--texto-suave); padding: 40px 0; }
</style>
</head>
<body>
<script id="dados-portal" type="application/json">__DADOS_JSON__</script>
<header>
  <h1>Jurisprudência sobre Finanças Públicas</h1>
  <p id="subtitulo">carregando…</p>
</header>
<div class="barra">
  <input type="search" id="busca" placeholder="Buscar por palavra, relator, número...">
  <select id="filtroOrgao"><option value="">Todos os órgãos</option></select>
  <select id="filtroTema"><option value="">Todos os temas</option></select>
</div>
<main>
  <div class="contagem" id="contagem"></div>
  <div id="lista"></div>
</main>
<script>
function main() {
  // Os dados vêm embutidos na própria página (não via fetch), para funcionar
  // ao abrir o arquivo direto com duplo clique — navegadores bloqueiam fetch()
  // de arquivos locais (file://) por política de segurança (CORS).
  const info = JSON.parse(document.getElementById('dados-portal').textContent);
  const decisoes = info.decisoes;

  document.getElementById('subtitulo').textContent =
    `${decisoes.length} decisões · atualizado em ${info.gerado_em}`;

  const orgaos = [...new Set(decisoes.map(d => d.orgao))].sort();
  const selOrgao = document.getElementById('filtroOrgao');
  orgaos.forEach(o => selOrgao.add(new Option(o, o)));

  const selTema = document.getElementById('filtroTema');
  info.temas.forEach(t => selTema.add(new Option(t, t)));

  const lista = document.getElementById('lista');
  const contagem = document.getElementById('contagem');
  const busca = document.getElementById('busca');

  function renderiza() {
    const termo = busca.value.trim().toLowerCase();
    const orgao = selOrgao.value;
    const tema = selTema.value;

    const filtradas = decisoes.filter(d => {
      if (orgao && d.orgao !== orgao) return false;
      if (tema && !d.temas.includes(tema)) return false;
      if (termo) {
        const alvo = `${d.titulo} ${d.relator} ${d.ementa} ${d.assunto}`.toLowerCase();
        if (!alvo.includes(termo)) return false;
      }
      return true;
    });

    contagem.textContent = `${filtradas.length} decisão(ões) encontrada(s)`;
    lista.innerHTML = '';

    if (filtradas.length === 0) {
      lista.innerHTML = '<div class="vazio">Nenhuma decisão encontrada com esse filtro.</div>';
      return;
    }

    for (const d of filtradas.slice(0, 300)) {
      const card = document.createElement('div');
      card.className = 'card';
      const link = d.url ? `<a href="${d.url}" target="_blank" rel="noopener">${d.titulo || d.numero}</a>` : (d.titulo || d.numero);
      card.innerHTML = `
        <h2>${link}</h2>
        <div class="meta">${d.orgao} · ${d.colegiado || ''} · ${d.relator || ''} · sessão em ${d.data_sessao || '—'}</div>
        <div class="temas">${d.temas.map(t => `<span class="tema-tag">${t}</span>`).join('')}</div>
        <div class="ementa">${(d.ementa || d.assunto || '(sem ementa/sumário)').replace(/</g,'&lt;')}</div>
        <button class="ver-mais">ver mais ▾</button>
      `;
      card.querySelector('.ver-mais').addEventListener('click', () => {
        card.classList.toggle('aberto');
        const btn = card.querySelector('.ver-mais');
        btn.textContent = card.classList.contains('aberto') ? 'ver menos ▴' : 'ver mais ▾';
      });
      lista.appendChild(card);
    }
  }

  busca.addEventListener('input', renderiza);
  selOrgao.addEventListener('change', renderiza);
  selTema.addEventListener('change', renderiza);
  renderiza();
}
main();
</script>
</body>
</html>
"""


def gerar() -> int:
    PASTA_SITE.mkdir(parents=True, exist_ok=True)
    decisoes = carregar_decisoes()

    dados = {
        "gerado_em": dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "temas": list(TEMAS.keys()),
        "decisoes": decisoes,
    }
    # escapa "</" para o JSON embutido não poder fechar a tag <script> mais cedo
    dados_json = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE_HTML.replace("__DADOS_JSON__", dados_json)
    (PASTA_SITE / "index.html").write_text(html, encoding="utf-8")
    return len(decisoes)


if __name__ == "__main__":
    n = gerar()
    print(f"Portal gerado em {PASTA_SITE / 'index.html'} com {n} decisões.")
