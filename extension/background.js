// background.js — Hint Media LinkedIn Extension Service Worker

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function setState(patch) {
  return chrome.storage.local.set(patch);
}

// Send bubble by executing inline script in the tab — no content script needed
async function sendBubbleInTab(tabId, text) {
  const results = await chrome.scripting.executeScript({
    target: { tabId },
    func: async (bubbleText) => {
      const _sleep = ms => new Promise(r => setTimeout(r, ms));

      const INPUT_SELS = [
        '.msg-form__contenteditable[contenteditable="true"]',
        '.msg-compose-form div[contenteditable="true"]',
        '.msg-overlay-conversation-bubble div[contenteditable="true"]',
        'div[contenteditable="true"][role="textbox"]',
        'div.msg-form__contenteditable',
        'div[contenteditable="true"]',
        '[contenteditable="true"]',
        'textarea',
      ];
      const BTN_SELS = [
        'button[aria-label="Enviar"]',
        'button[aria-label="Send"]',
        'button.msg-form__send-button',
        '.msg-form__form button[type="submit"]',
        'button[data-control-name="send-message"]',
      ];

      // Search in a document (main or iframe contentDocument)
      const findElIn = (doc, sels) => {
        for (const s of sels) {
          try { const e = doc.querySelector(s); if (e) return e; } catch(_) {}
        }
        return null;
      };

      await _sleep(500);

      // First try main document
      let input = findElIn(document, INPUT_SELS);
      let inputDoc = document;

      // If not found, search inside all same-origin iframes
      if (!input) {
        const iframes = [...document.querySelectorAll('iframe')];
        for (const frame of iframes) {
          try {
            const doc = frame.contentDocument || frame.contentWindow?.document;
            if (!doc) continue;
            const el = findElIn(doc, INPUT_SELS);
            if (el) { input = el; inputDoc = doc; break; }
          } catch (_) {} // cross-origin, skip
        }
      }

      if (!input) {
        const iframeUrls = [...document.querySelectorAll('iframe')].map(f => f.src || f.getAttribute('src') || 'no-src').join(', ');
        return { error: 'Input no encontrado en ningún frame. Iframes: ' + iframeUrls };
      }

      input.focus();
      await _sleep(300);
      document.execCommand('selectAll', false, null);
      document.execCommand('delete', false, null);
      await _sleep(150);

      const inserted = document.execCommand('insertText', false, bubbleText);
      await _sleep(300);

      if (!inserted || !input.innerText?.trim()) {
        input.innerHTML = '';
        input.appendChild(document.createTextNode(bubbleText));
        const range = document.createRange();
        range.selectNodeContents(input);
        range.collapse(false);
        window.getSelection()?.removeAllRanges();
        window.getSelection()?.addRange(range);
        input.dispatchEvent(new InputEvent('input', { bubbles: true, data: bubbleText, inputType: 'insertText' }));
        await _sleep(400);
      }

      let sendBtn = null;
      for (let i = 0; i < 15; i++) {
        const btn = findElIn(inputDoc, BTN_SELS);
        if (btn && !btn.disabled) { sendBtn = btn; break; }
        await _sleep(200);
      }

      if (sendBtn) {
        sendBtn.click();
      } else {
        input.dispatchEvent(new KeyboardEvent('keydown', {
          key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
        }));
      }

      await _sleep(600);
      return { ok: true };
    },
    args: [text],
  });

  // Find first frame that succeeded or get the first error
  const ok = results?.find(r => r.result?.ok);
  if (ok) return ok.result;
  const err = results?.find(r => r.result?.error);
  throw new Error(err?.result?.error || 'No se pudo enviar la burbuja en ningún frame');
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.action === 'start-send') {
    doSend(msg.tabId, msg.bubbles, msg.entry);
    sendResponse({ ok: true });
    return false;
  }
});

async function doSend(tabId, bubbles, entry) {
  for (let i = 0; i < bubbles.length; i++) {
    await setState({ phase: 'sending', sendCurrent: i, sendTotal: bubbles.length });

    try {
      await sendBubbleInTab(tabId, bubbles[i]);
    } catch (e) {
      await setState({
        phase: 'error',
        sendError: 'Error en burbuja ' + (i + 1) + ': ' + e.message,
      });
      return;
    }

    if (i < bubbles.length - 1) {
      const delay = 4000 + Math.floor(Math.random() * 2000);
      await sleep(delay);
    }
  }

  try {
    await fetch('http://localhost:3000/api/historial', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry),
    });
  } catch (_) {}

  await setState({ phase: 'done' });
}
