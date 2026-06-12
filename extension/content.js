// content.js — Hint Media LinkedIn Extension

(function() {
'use strict';

// Guard: only register listener once per page context
if (window.__hintMediaListening) return;
window.__hintMediaListening = true;

const CHAT_INPUT_SELECTORS = [
  '.msg-form__contenteditable[contenteditable="true"]',
  'div[contenteditable="true"][role="textbox"].msg-form__contenteditable',
  '.msg-overlay-conversation-bubble div[contenteditable="true"]',
  '.msg-compose-form div[contenteditable="true"]',
  'div[contenteditable="true"][role="textbox"]',
  'div.msg-form__contenteditable',
  'div[contenteditable="true"]',
];

const SEND_BTN_SELECTORS = [
  'button[aria-label="Enviar"]',
  'button[aria-label="Send"]',
  'button.msg-form__send-button',
  '.msg-form__form button[type="submit"]',
  'button[data-control-name="send-message"]',
];

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function findEl(selectors) {
  for (const sel of selectors) {
    try {
      const el = document.querySelector(sel);
      if (el) return el;
    } catch (_) {}
  }
  return null;
}

function findMessageButton() {
  const all = [...document.querySelectorAll('button, a')];
  const exact = all.find(el => {
    const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().toLowerCase();
    return text.includes('enviar mensaje') || text.includes('send message');
  });
  if (exact) return exact;
  return all.find(el => {
    const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().toLowerCase();
    const label = (el.getAttribute('aria-label') || '').toLowerCase();
    if (label.includes('notificacion') || label.includes('notification')) return false;
    return text === 'mensaje' || text === 'message' ||
           label.includes('enviar mensaje') || label.includes('send message');
  }) || null;
}

async function setInputText(el, text) {
  el.focus();
  await sleep(300);
  document.execCommand('selectAll', false, null);
  document.execCommand('delete', false, null);
  await sleep(150);
  const inserted = document.execCommand('insertText', false, text);
  await sleep(300);
  if (!inserted || !el.innerText?.trim()) {
    el.innerHTML = '';
    el.appendChild(document.createTextNode(text));
    const range = document.createRange();
    range.selectNodeContents(el);
    range.collapse(false);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(range);
    el.dispatchEvent(new InputEvent('input', { bubbles: true, data: text, inputType: 'insertText' }));
    await sleep(400);
  }
}

async function sendBubble(text) {
  const input = findEl(CHAT_INPUT_SELECTORS);
  if (!input) throw new Error('Input del chat no encontrado. Abrí el chat primero.');

  await setInputText(input, text);

  let sendBtn = null;
  for (let i = 0; i < 15; i++) {
    const btn = findEl(SEND_BTN_SELECTORS);
    if (btn && !btn.disabled) { sendBtn = btn; break; }
    await sleep(200);
  }

  if (sendBtn) {
    sendBtn.click();
  } else {
    input.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
    }));
  }

  await sleep(600);
  return true;
}

function scrapeProfile() {
  const getText = sel => {
    try { return document.querySelector(sel)?.innerText?.trim() || ''; }
    catch (_) { return ''; }
  };

  const name =
    getText('h1') ||
    getText('h1.text-heading-xlarge') ||
    getText('.pv-text-details__left-panel h1') ||
    getText('.top-card__title') ||
    (() => {
      const t = document.title || '';
      const m = t.match(/^(.+?)\s*[-–|]/);
      return m ? m[1].trim() : '';
    })();

  const headline =
    getText('.text-body-medium.break-words') ||
    getText('.pv-text-details__left-panel .text-body-medium') ||
    getText('.top-card__subline-item') ||
    getText('.text-body-small.break-words') ||
    (() => {
      const t = document.title || '';
      const m = t.match(/^.+?\s*-\s*(.+?)\s*[|]/);
      return m ? m[1].trim() : '';
    })();

  if (!name && !headline) return null;

  const allSections = [...document.querySelectorAll('section')];
  const findSectionText = (...keywords) => {
    for (const section of allSections) {
      const heading = section.querySelector(
        'h2, h3, .pvs-header__title span[aria-hidden="true"], .pv-shared-text-with-see-more'
      );
      const headText = (heading?.innerText || '').toLowerCase();
      if (keywords.some(k => headText.includes(k))) {
        return (section.innerText || '').trim().substring(0, 1200);
      }
    }
    for (const kw of keywords) {
      try {
        const el = document.getElementById(kw);
        if (el) return (el.closest('section')?.innerText || '').trim().substring(0, 1200);
      } catch (_) {}
    }
    return '';
  };

  const about      = findSectionText('about', 'acerca');
  const experience = findSectionText('experience', 'experiencia');
  const activity   = findSectionText('activity', 'actividad', 'recent');

  let result = '';
  if (name)       result += `Nombre: ${name}\n`;
  if (headline)   result += `Cargo: ${headline}\n`;
  if (about)      result += `\nAcerca de:\n${about}\n`;
  if (experience) result += `\nExperiencia:\n${experience}\n`;
  if (activity)   result += `\nActividad reciente:\n${activity}\n`;

  return { text: result.trim(), name };
}

// ── Message handler ──────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {

  if (msg.action === 'scrape') {
    (async () => {
      let result = null;
      for (let i = 0; i < 20; i++) {
        result = scrapeProfile();
        if (result) break;
        await sleep(500);
      }
      sendResponse(result || { error: 'No se pudo leer el perfil.\n\nEsperá que la página cargue completamente y volvé a intentar.' });
    })();
    return true;
  }

  if (msg.action === 'open-chat') {
    (async () => {
      if (findEl(CHAT_INPUT_SELECTORS)) { sendResponse({ ok: true }); return; }
      const btn = findMessageButton();
      if (!btn) { sendResponse({ error: 'No se encontró el botón Mensaje. Abrí el chat manualmente.' }); return; }
      btn.click();
      for (let i = 0; i < 40; i++) {
        await sleep(200);
        if (findEl(CHAT_INPUT_SELECTORS)) { sendResponse({ ok: true }); return; }
      }
      sendResponse({ error: 'El chat no se abrió. Abrilo manualmente y hacé click en Enviar.' });
    })();
    return true;
  }

  if (msg.action === 'send-bubble') {
    (async () => {
      try {
        await sendBubble(msg.text);
        sendResponse({ ok: true });
      } catch (e) {
        sendResponse({ error: e.message });
      }
    })();
    return true;
  }

  if (msg.action === 'chat-ready') {
    sendResponse({ ok: !!findEl(CHAT_INPUT_SELECTORS) });
    return false;
  }
});

})(); // end IIFE
