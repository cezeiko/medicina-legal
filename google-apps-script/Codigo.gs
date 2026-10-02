/**
 * Recebe os pedidos de amostra gratuita da landing page,
 * grava cada lead na planilha e envia a amostra por e-mail.
 *
 * Instalação: veja google-apps-script/LEIA-ME.md
 */

const CONFIG = {
  // Nome da aba onde os leads são gravados (é criada automaticamente)
  ABA: 'Leads',
  // ID do PDF da amostra no Google Drive
  // (o trecho entre /d/ e /view no link do arquivo)
  ID_ARQUIVO_AMOSTRA: '',
  NOME_REMETENTE: 'Prof. Dr. Paulo Romero Calou',
  RESPONDER_PARA: '', // opcional: e-mail que recebe as respostas
  ASSUNTO: 'Sua amostra gratuita — Medicina Legal para Concursos',
  // Não reenvia para o mesmo e-mail dentro deste intervalo (evita abuso / clique duplo)
  HORAS_ENTRE_ENVIOS: 24,
};

const CABECALHO = ['Data', 'Nome', 'E-mail', 'Status', 'Origem', 'Navegador'];

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const p = (e && e.parameter) || {};
    const nome = String(p.nome || '').trim().slice(0, 100);
    const email = String(p.email || '').trim().toLowerCase().slice(0, 200);
    if (!nome || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return resposta({ ok: false, erro: 'dados inválidos' });
    }

    const aba = obterAba();
    let status;
    if (enviadoRecentemente(aba, email)) {
      status = 'ignorado (já enviado nas últimas ' + CONFIG.HORAS_ENTRE_ENVIOS + 'h)';
    } else {
      try {
        enviarAmostra(nome, email);
        status = 'enviado';
      } catch (err) {
        status = 'erro: ' + err.message;
      }
    }

    aba.appendRow([new Date(), nome, email, status, p.origem || '', p.userAgent || '']);
    return resposta({ ok: true, status: status });
  } finally {
    lock.releaseLock();
  }
}

// Permite conferir no navegador se o app da web está no ar
function doGet() {
  return resposta({ ok: true, mensagem: 'Endpoint da amostra gratuita ativo.' });
}

function enviarAmostra(nome, email) {
  const primeiroNome = nome.split(/\s+/)[0];
  const opcoes = {
    name: CONFIG.NOME_REMETENTE,
    htmlBody:
      '<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.6;color:#1B2534">' +
      '<p>Olá, ' + escaparHtml(primeiroNome) + '!</p>' +
      '<p>Obrigado pelo interesse no <strong>Medicina Legal para Concursos — Guia Completo de Estudos</strong>.</p>' +
      '<p>Sua amostra gratuita está em anexo. Nela você conhece a estrutura, a organização e a identidade visual do material.</p>' +
      '<p>Bons estudos!<br>' + escaparHtml(CONFIG.NOME_REMETENTE) + '</p>' +
      '</div>',
  };
  if (CONFIG.RESPONDER_PARA) opcoes.replyTo = CONFIG.RESPONDER_PARA;
  if (CONFIG.ID_ARQUIVO_AMOSTRA) {
    opcoes.attachments = [DriveApp.getFileById(CONFIG.ID_ARQUIVO_AMOSTRA).getAs(MimeType.PDF)];
  } else {
    throw new Error('ID_ARQUIVO_AMOSTRA não configurado');
  }
  MailApp.sendEmail(email, CONFIG.ASSUNTO, '', opcoes);
}

function obterAba() {
  const planilha = SpreadsheetApp.getActiveSpreadsheet();
  let aba = planilha.getSheetByName(CONFIG.ABA);
  if (!aba) {
    aba = planilha.insertSheet(CONFIG.ABA);
    aba.appendRow(CABECALHO);
    aba.setFrozenRows(1);
    aba.getRange(1, 1, 1, CABECALHO.length).setFontWeight('bold');
  }
  return aba;
}

function enviadoRecentemente(aba, email) {
  const ultima = aba.getLastRow();
  if (ultima < 2) return false;
  const limite = Date.now() - CONFIG.HORAS_ENTRE_ENVIOS * 3600 * 1000;
  const linhas = aba.getRange(2, 1, ultima - 1, 4).getValues();
  return linhas.some(function (l) {
    return String(l[2]).toLowerCase() === email && l[3] === 'enviado' && new Date(l[0]).getTime() > limite;
  });
}

function resposta(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function escaparHtml(t) {
  return String(t).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}

/**
 * Rode esta função uma vez pelo editor (botão "Executar") para autorizar
 * o script e receber um e-mail de teste no seu próprio endereço.
 */
function testarEnvio() {
  enviarAmostra('Teste', Session.getActiveUser().getEmail());
  Logger.log('E-mail de teste enviado para ' + Session.getActiveUser().getEmail());
}
