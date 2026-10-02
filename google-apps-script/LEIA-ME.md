# Landing page da amostra gratuita: GitHub Pages + Google Sheets

Fluxo: a pessoa preenche nome e e-mail na página → o formulário envia para um
Google Apps Script → o script grava o lead na planilha e envia o PDF da amostra
por e-mail.

Endereço da página depois de publicada:
**https://cezeiko.github.io/medicina-legal/**

## 1. Ativar o GitHub Pages (uma vez só)

1. No GitHub, abra o repositório → **Settings** → **Pages**.
2. Em **Build and deployment → Source**, escolha **GitHub Actions**.
3. Coloque estes arquivos na branch `main` (faça o merge do pull request).
   O workflow `.github/workflows/pages.yml` publica a pasta `landing-page/`
   automaticamente a cada alteração nela.

## 2. Criar a planilha e o script

1. Suba o **PDF da amostra** no Google Drive. Abra o arquivo e copie o ID do
   link: `https://drive.google.com/file/d/`**`ESTE_TRECHO`**`/view`.
2. Crie uma planilha nova no Google Sheets (ex.: "Leads — Amostra gratuita").
3. Na planilha: **Extensões → Apps Script**.
4. Apague o conteúdo do editor e cole o arquivo `Codigo.gs` desta pasta.
5. No topo do código, preencha `ID_ARQUIVO_AMOSTRA` com o ID do passo 1
   (e, se quiser, `RESPONDER_PARA`). Salve (Ctrl+S).
6. Selecione a função **testarEnvio** e clique em **Executar**. Autorize o
   acesso quando o Google pedir. Você deve receber o e-mail de teste com o PDF.

## 3. Publicar o script como app da web

1. No Apps Script: **Implantar → Nova implantação**.
2. Tipo: **App da Web**.
   - Executar como: **Eu**
   - Quem pode acessar: **Qualquer pessoa**
3. Clique em **Implantar** e copie a **URL do app da web**
   (termina em `/exec`).

> Se depois alterar o código, use **Implantar → Gerenciar implantações →
> Editar → Nova versão**, assim a URL continua a mesma.

## 4. Ligar a página ao script

No arquivo `landing-page/index.html`, logo no começo:

```html
window.LP_CONFIG = { formEndpoint: 'COLE_AQUI_A_URL_/exec' };
```

Salve e faça commit na `main`. O GitHub Pages republica sozinho em ~1 minuto.

## Teste final

Abra a página publicada, envie o formulário com seu e-mail e confira:
- uma linha nova na aba **Leads** com status `enviado`;
- o e-mail com o PDF na sua caixa de entrada (veja também spam/promoções).

## Observações

- Enquanto `formEndpoint` estiver vazio, o formulário mostra erro em vez de
  fingir que enviou, para nenhum lead se perder.
- Limite do Gmail: contas gratuitas enviam até **100 e-mails por dia** pelo
  Apps Script (Google Workspace: 1.500). Se passar disso, o status na planilha
  fica como `erro: ...` e o lead continua gravado para envio manual.
- O mesmo e-mail não recebe a amostra de novo dentro de 24h
  (`HORAS_ENTRE_ENVIOS`), evitando cliques duplicados e abuso.
- Se exportar a página de novo pelo Claude Design, esta integração precisa ser
  reaplicada no novo arquivo.
