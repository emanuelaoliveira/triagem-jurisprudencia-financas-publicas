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
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --senado-blue: #1a5276; --senado-blue-light: #2980b9; --senado-green: #1a7a4a;
    --bg: #f4f6f8; --surface: #ffffff; --surface2: #eef1f4;
    --border: rgba(0,0,0,0.10); --border2: rgba(0,0,0,0.20);
    --text: #1a1a1a; --text2: #4a5568; --text3: #718096;
    --radius-md: 6px; --radius-lg: 10px; --font: 'Segoe UI', system-ui, sans-serif;
  }
  body { font-family: var(--font); background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.6; min-height: 100vh; padding: 0 0 4rem; }
  .inst-header { background: #fff; border-bottom: 3px solid var(--senado-blue); padding: 10px 2rem; display: flex; align-items: center; gap: 1rem; }
  .conof-bar { width: 4px; height: 44px; background: linear-gradient(180deg, var(--senado-blue) 50%, var(--senado-green) 50%); border-radius: 2px; flex-shrink: 0; }
  .conof-name { font-size: 13px; color: var(--senado-blue); font-weight: 600; line-height: 1.3; }
  .inst-divider { width: 1px; height: 40px; background: var(--border2); flex-shrink: 0; margin: 0 4px; }
  .senado-text span { display: block; font-size: 13px; font-weight: 700; color: var(--senado-blue); letter-spacing: 0.04em; line-height: 1.15; }
  .page-title-bar { background: var(--senado-blue); padding: 14px 2rem; display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
  .page-title-bar h1 { font-size: 18px; font-weight: 600; color: #fff; }
  .page-title-bar p { font-size: 12px; color: rgba(255,255,255,0.72); }
  .container { max-width: 1000px; margin: 0 auto; padding: 1.5rem 1rem; }
  .section { background: var(--surface); border: 0.5px solid var(--border); border-radius: var(--radius-lg); padding: 1.25rem 1.5rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
  .section-title { font-size: 10px; font-weight: 700; color: var(--senado-blue); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 1rem; display: flex; align-items: center; gap: 8px; }
  .section-title::after { content: ''; flex: 1; height: 1px; background: var(--border); }

  .barra { display: flex; gap: 10px; flex-wrap: wrap; position: sticky; top: 0; background: var(--surface); z-index: 5; }
  .barra input, .barra select { padding: 8px 10px; border: 1.5px solid var(--border2); border-radius: var(--radius-md); font-size: 13px; font-family: var(--font); color: var(--text); background: #fff; }
  .barra input[type=search] { flex: 1; min-width: 220px; }
  .barra input:focus, .barra select:focus { outline: none; border-color: var(--senado-blue-light); }

  .contagem { color: var(--text3); font-size: 11px; margin: 0 0 10px; }
  .card { border: 0.5px solid var(--border); border-radius: var(--radius-md); padding: 14px 16px; margin-bottom: 10px; }
  .card h2 { font-size: 14px; font-weight: 600; margin: 0 0 4px; }
  .card h2 a { color: var(--senado-blue); text-decoration: none; }
  .card h2 a:hover { text-decoration: underline; }
  .meta { font-size: 11px; color: var(--text3); margin-bottom: 8px; }
  .temas { margin-bottom: 8px; }
  .tema-tag { display: inline-block; background: #e8f0fe; color: var(--senado-blue); border-radius: 12px; padding: 2px 10px; font-size: 11px; font-weight: 600; margin: 0 4px 4px 0; }
  .ementa { font-size: 13px; line-height: 1.5; color: var(--text2); white-space: pre-line; max-height: 6.5em; overflow: hidden; }
  .card.aberto .ementa { max-height: none; }
  .ver-mais { font-size: 12px; color: var(--senado-blue-light); cursor: pointer; background: none; border: none; padding: 4px 0; font-family: var(--font); font-weight: 500; }
  .vazio { text-align: center; color: var(--text3); padding: 40px 0; font-size: 13px; }

  footer { margin-top: 1rem; font-size: 11px; color: var(--text3); text-align: center; border-top: 1px solid var(--border); padding-top: 1rem; }
  footer strong { color: var(--senado-blue); }
</style>
</head>
<body>
<script id="dados-portal" type="application/json">__DADOS_JSON__</script>

<div class="inst-header">
  <div class="conof-bar"></div>
  <div class="conof-name">Consultoria de Orçamentos,<br>Fiscalização e Controle</div>
  <div class="inst-divider"></div>
  <div class="senado-text"><span>SENADO</span><span>FEDERAL</span></div>
</div>
<div class="page-title-bar">
  <h1>Jurisprudência sobre Finanças Públicas</h1>
  <p id="subtitulo">carregando…</p>
</div>

<div class="container">

  <div class="section">
    <p class="section-title">Filtrar</p>
    <div class="barra">
      <input type="search" id="busca" placeholder="Buscar por palavra, relator, número...">
      <select id="filtroOrgao"><option value="">Todos os órgãos</option></select>
      <select id="filtroTema"><option value="">Todos os temas</option></select>
    </div>
  </div>

  <div class="section">
    <p class="section-title">Decisões</p>
    <div class="contagem" id="contagem"></div>
    <div id="lista"></div>
  </div>

  <footer>
    Ferramenta para uso interno da <strong>CONORF — Consultoria de Orçamentos, Fiscalização e Controle / Senado Federal</strong>.<br>
    Dados públicos do TCU e do STF, triados automaticamente por tema de finanças públicas.
  </footer>
</div>
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
