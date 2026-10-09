# Preparação para o mapeamento histórico do STF (fazer na segunda)

Isso só precisa ser feito **uma vez**. Depois disso, rodar o mapeamento é um único
comando.

## O que você vai precisar criar

Uma conta no **Google Cloud** — é gratuita para o que vamos usar (consultar esta
base específica fica bem abaixo da cota grátis do BigQuery, que é de 1 TB de
consulta por mês; a base inteira tem 1,44 GB). **Atenção**: o Google pode pedir um
cartão de crédito para ativar a conta, mesmo no nível gratuito — é a política deles
para evitar contas falsas, não vamos usar nada pago. Se isso te incomodar, me avise
antes de continuar que buscamos outra alternativa.

**Eu não posso criar essa conta por você** — é uma conta/autorização sua. Mas te
guio passo a passo quando for fazer.

## Passo a passo

1. **Criar/entrar na conta Google Cloud**: acesse console.cloud.google.com e
   entre com uma conta Google (pode ser a `senadoconorf@gmail.com` que você já
   usa, ou outra).
2. **Criar um projeto novo**: no topo da página, "Select a project" → "New
   Project" → dê um nome (ex: `triagem-stf`) → Create.
3. **Instalar o Google Cloud CLI** no seu Mac (ferramenta de linha de comando):
   baixe em cloud.google.com/sdk/docs/install e siga o instalador.
4. **Autenticar**: abra o Terminal e rode:
   ```bash
   gcloud auth application-default login
   ```
   Isso abre o navegador pra você fazer login com a mesma conta Google do passo 1.
5. **Apontar pro projeto criado**: substitua `SEU_PROJETO_ID` pelo nome que você
   deu no passo 2:
   ```bash
   gcloud config set project SEU_PROJETO_ID
   ```

## Rodando o mapeamento

Com os passos acima feitos, dentro da pasta do projeto:

```bash
.venv/bin/pip install -r requirements-stf.txt
.venv/bin/python3 -m scripts.mapeamento_stf_corte_aberta --project SEU_PROJETO_ID
```

Isso vai:
- Ler todos os processos do STF desde 2000 (só os metadados: classe, número,
  relator, assunto, link — não o texto da decisão)
- Classificar pelos mesmos 20 temas de finanças públicas do TCU
- Salvar os que casarem no banco local, com `orgao = "STF"`

**O resultado não tem o texto da ementa** (ver a limitação do bloqueio do site do
STF) — é uma lista de processos candidatos, pra depois decidirmos como buscar o
texto de cada um (manual, pontual, ou outra solução).
