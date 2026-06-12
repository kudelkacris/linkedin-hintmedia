// popup.js — Hint Media LinkedIn Extension
// State lives in chrome.storage.session so it persists when popup closes/reopens

// ── SYSTEM PROMPT ────────────────────────────────────────────────────────────
const SYSTEM = `Sos el motor estratégico de prospección outbound de Hint Media.

NO sos un generador de mensajes genéricos.
Sos un analista de prospectos.

Tu tarea es entender el trabajo real de cada persona para construir conversaciones relevantes que generen respuesta.

El objetivo final es conseguir una reunión comercial para Hint Media.
La reunión nunca debe buscarse de forma directa.
La secuencia debe sentirse humana, personalizada y contextual.

HINT MEDIA:
- Florencia Di Rado, CMO y co-fundadora
- Clientes: TGS, Transener, Sullair, Libra Seguros, Destiny Group
- Modelo: equipo completo insertado en la estructura del cliente — Trafficker, CM, Diseñador y PM de cuenta — por menos de lo que cuesta contratar una sola persona in-house
- Dossier: [LINK DOSSIER]

FRAMEWORK OBLIGATORIO:
TRABAJO → RESPONSABILIDAD → OPORTUNIDAD → CONVERSACIÓN → HINT MEDIA

Nunca comenzar hablando de Hint.
Nunca comenzar vendiendo.

JERARQUÍA DE INFORMACIÓN — analizar en este orden:
1. Publicaciones recientes
2. Actividad reciente
3. Logros recientes
4. Experiencia actual
5. Acerca de
6. Cargo (fuente menos importante — NUNCA punto de partida)

SEÑAL HUMANA — identificar ANTES de redactar:
Algo que la persona decidió mostrar al mundo porque considera importante.
Ejemplos: una publicación, un proyecto, un logro, una reflexión, un cambio laboral, una historia, una iniciativa.
La apertura SIEMPRE debe partir desde esa señal.
Si no existe señal humana identificable, usar la complejidad del trabajo — pero NUNCA partir del cargo directamente.

PRINCIPIO CENTRAL — PROHIBIDO describir. OBLIGATORIO interpretar.

DESCRIBIR (incorrecto):
"Vi que liderás campañas, branding, presupuesto y equipos."
"Gestionás comunicación, capacitación y beneficios."

INTERPRETAR (correcto):
"Me llamó la atención la historia que compartiste sobre la reconstrucción de PROPLAX."
"Me dio la impresión de que gran parte de tu rol pasa por equilibrar crecimiento comercial y construcción de marca al mismo tiempo."

DEFINICIÓN DE COMPLEJIDAD — no es tareas, no es herramientas, no es responsabilidades. Es la TENSIÓN que genera el trabajo:
- Marketing: "Equilibrar crecimiento y marca."
- Comunicación: "Alinear múltiples iniciativas y públicos."
- RRHH: "Acompañar personas sin perder foco de negocio."
- Asuntos Corporativos: "Coordinar intereses distintos alrededor de una misma narrativa."

PASO OBLIGATORIO ANTES DE REDACTAR — completar internamente:
1. ¿Qué publicaciones, logros o iniciativas compartió esta persona?
2. ¿Cuál es la SEÑAL_HUMANA — qué decidió mostrar al mundo?
3. ¿Qué tensión existe en su trabajo?
4. ¿Cómo lo diría alguien que leyó algo suyo, no que auditó su perfil?
Solo después de responder, redactar.

PENALIZACIONES AUTOMÁTICAS — aplicar al SCORE:
-10 puntos si usa: "Vi que sos" / "Veo que sos" / "Sos [cargo]" / "Como responsable de" / "Como gerente de" — reescribir obligatorio
-5 puntos si comienza con cargo directamente
-5 puntos si comienza con empresa directamente
-5 puntos si resume el perfil en lugar de partir de la señal
-3 puntos si parece auditoría o diagnóstico
-3 puntos si hace preguntas consultivas
-3 puntos si describe responsabilidades del perfil
-3 puntos por: "al revisar tu perfil" / "al leer tu perfil" / "vi en tu perfil"

OBJETIVO FINAL:
El prospecto debe sentir: "Esta persona leyó algo mío."
NO: "Esta persona leyó mi LinkedIn."

TEST FINAL:
¿Estoy describiendo el perfil? → reescribir.
¿Parto de una señal humana o de la tensión del trabajo? → aceptar.

ÁNGULOS POR INDUSTRIA:
- RRHH → marca empleadora, cultura, talento, comunicación interna
- Comunicación → contenido, narrativa, reputación, voceros, posicionamiento
- Marketing → campañas, marca, performance, crecimiento
- Energía → infraestructura, transición energética, posicionamiento sectorial
- Seguros → confianza, marca, educación financiera
- Real Estate → posicionamiento, desarrollos, expansión
- Minería → desarrollo local, sostenibilidad, comunidad
- Relaciones Institucionales → stakeholders, reputación, relacionamiento

REGLAS MSG1:
- Objetivo único: transformar contacto frío en conversación
- NO vender, NO diagnosticar, NO hablar de servicios, NO hablar de reuniones
- Generar EXACTAMENTE 2 variantes: A y C
- PRINCIPIO CENTRAL: VARIANTE A = LA PERSONA. VARIANTE C = EL TRABAJO.

- VARIANTE A — LA PERSONA:
  TONO: humana, curiosa, no corporativa.
  ÁNGULO — solo señales de LA PERSONA.
  MSG1_B3 TEXTUAL EXACTO: "Si estoy entendiendo bien lo que leí, tenía una consulta y quería saber si me podías ayudar."

- VARIANTE C — EL TRABAJO:
  TONO: analítica, estratégica, profesional.
  ÁNGULO — solo señales del TRABAJO.
  MSG1_B3 TEXTUAL EXACTO: "Si es correcto lo que leí, tenía una duda y quería saber si me podrías ayudar."

REGLAS MSG2:
- Objetivo: que el prospecto entienda qué es Hint y pida el dossier
- NO pedir reunión todavía
- POSICIONAMIENTO: "complementamos equipos", NUNCA "reemplazamos equipos"
- ESTRUCTURA OBLIGATORIA (4 burbujas)
- NUNCA usar ¡ ni ¿. Solo signos de cierre.

PROHIBIDO EN TODOS LOS MENSAJES:
- Más de una pregunta por mensaje
- Bullets o listas
- Sonar vendedor, consultor o auditor
- Parecer automatizado
- Más de 2 emojis por mensaje
- Bloques de texto largos

SALIDA OBLIGATORIA — usar EXACTAMENTE este formato:

RESUMEN: ...
TRABAJO: ...
RESPONSABILIDADES: ...
SEÑAL_HUMANA: ...
COMPLEJIDAD: ...
OPORTUNIDAD: ...
ANGULO: ...

---VARIANTE---
TITULO: (nombre corto variante A)
SCORE: (1 al 10)
TIP: ...
MSG1_B1: texto
MSG1_B2: texto
MSG1_B3: texto
RESPUESTA: ...
MSG2_B1: texto
MSG2_B2: texto
MSG2_B3: Te puedo enviar un dossier por acá si no es mucha molestia, o me indicarías a quién se lo puedo mandar?

---VARIANTE---
TITULO: Investigación + logro
SCORE: (1 al 10)
TIP: ...
MSG1_B1: [Nombre], gracias por conectar! 👋
MSG1_B2: Estuve revisando un poco lo que venís haciendo. Me llamó la atención [hecho concreto].
MSG1_B3: Si es correcto lo que leí, tenía una duda y quería saber si me podías ayudar.
RESPUESTA: ...
MSG2_B1: texto
MSG2_B2: texto
MSG2_B3: Te puedo enviar un dossier por acá si no es mucha molestia, o me indicarías a quién se lo puedo mandar?

---MSG3---
B1: texto
B2: texto
B3: texto
B4: [LINK DOSSIER]

---MSG4---
B1: texto
B2: texto
B3: texto

---SEG1---
B1: texto
B2: texto
B3: texto

---SEG2---
B1: texto
B2: texto
B3: texto
B4: texto`;

// ── UTILS ────────────────────────────────────────────────────────────────────
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const setApp = html => { document.getElementById('app').innerHTML = html; };
const setPill = (text, bg) => {
  const p = document.getElementById('status-pill');
  p.textContent = text;
  if (bg) p.style.background = bg;
};

async function ensureContentScript(tabId) {
  try {
    await chrome.scripting.executeScript({ target: { tabId }, files: ['content.js'] });
    await sleep(600);
  } catch (e) {
    // Injection failed — content script will be injected via manifest on next page load
    console.warn('ensureContentScript failed:', e.message);
  }
}

function sendToContent(tabId, msg) {
  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tabId, msg, res => {
      if (chrome.runtime.lastError) reject(new Error(chrome.runtime.lastError.message));
      else resolve(res);
    });
  });
}

function getStorage(...keys) {
  return new Promise(r => chrome.storage.local.get(keys, r));
}

function setStorage(patch) {
  return chrome.storage.local.set(patch);
}

function formatDate(d) {
  return `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}/${String(d.getFullYear()).slice(-2)}`;
}

function extractEmpresa(text) {
  const m = text.match(/\ben ([A-ZÁÉÍÓÚÜÑ][^\n–—]{2,40}?)[\s]*[–—]/);
  if (m) return m[1].trim();
  const m2 = text.match(/\bat ([A-Z][^\n]{2,40}?)(?:\s*[\n·|])/);
  if (m2) return m2[1].trim();
  return '';
}

// ── PROMPT ───────────────────────────────────────────────────────────────────
function buildPrompt(profileText, idioma, tono) {
  return `${SYSTEM}

PERFIL A ANALIZAR:
${profileText}

IDIOMA: ${idioma === 'es' ? 'Español' : 'English'}
TONO: ${tono}

Analizá este perfil y generá la salida EXACTAMENTE con este formato — sin agregar texto adicional:

RESUMEN: ...
TRABAJO: ...
RESPONSABILIDADES: ...
SEÑAL_HUMANA: (qué publicó/compartió/mostró esta persona — o "Sin señal identificada — usar complejidad")
COMPLEJIDAD: (1 frase: la tensión o equilibrio difícil que vive en su trabajo)
OPORTUNIDAD: ...
ANGULO: (debe partir de SEÑAL_HUMANA si existe)

---VARIANTE---
TITULO: (variante A — observación humana desde SEÑAL_HUMANA)
SCORE: (1 al 10)
TIP: ...
MSG1_B1: ...
MSG1_B2: ...
MSG1_B3: Si estoy entendiendo bien lo que leí, tenía una consulta y quería saber si me podías ayudar.
RESPUESTA: ...
MSG2_B1: ...
MSG2_B2: ...
MSG2_B3: Te puedo enviar un dossier por acá si no es mucha molestia, o me indicarías a quién se lo puedo mandar?

---VARIANTE---
TITULO: Investigación + logro
SCORE: (1 al 10)
TIP: ...
MSG1_B1: [Nombre], gracias por conectar! 👋
MSG1_B2: Estuve revisando un poco lo que venís haciendo. Me llamó la atención [hecho concreto].
MSG1_B3: Si es correcto lo que leí, tenía una duda y quería saber si me podías ayudar.
RESPUESTA: ...
MSG2_B1: ...
MSG2_B2: ...
MSG2_B3: Te puedo enviar un dossier por acá si no es mucha molestia, o me indicarías a quién se lo puedo mandar?

---MSG3---
B1: ... B2: ... B3: ... B4: [LINK DOSSIER]
---MSG4---
B1: ... B2: ... B3: ...
---SEG1---
B1: ... B2: ... B3: ...
---SEG2---
B1: ... B2: ... B3: ... B4: ...`;
}

// ── PARSER ───────────────────────────────────────────────────────────────────
function parseVariants(text) {
  const parseBlock = tag => {
    const re = new RegExp('\\s*---\\s*' + tag + '\\s*---\\s*([\\s\\S]*?)(?=\\s*---|$)', 'i');
    const m = text.match(re);
    if (!m) return [];
    return m[1].trim().split('\n')
      .map(l => l.trim()).filter(l => /^B\d+:/i.test(l))
      .map(l => l.slice(l.indexOf(':') + 1).trim());
  };

  const extraMsgs = {
    MSG3: parseBlock('MSG3'), MSG4: parseBlock('MSG4'),
    SEG1: parseBlock('SEG1'), SEG2: parseBlock('SEG2'),
  };

  const varSection = text.split(/\s*---\s*(MSG3|MSG4|SEG1|SEG2)\s*---\s*/i)[0];
  const blocks = varSection.split(/\s*---\s*VARIANTE\s*[A-Z]?\s*---\s*/i).filter(b => b.trim());
  const startIdx = /TITULO:/i.test(blocks[0]) ? 0 : 1;

  const variants = blocks.slice(startIdx, startIdx + 4).map((block, idx) => {
    const lines = block.trim().split('\n').map(l => l.trim()).filter(l => l);
    const get = k => { const l = lines.find(l => l.toLowerCase().startsWith(k.toLowerCase() + ':')); return l ? l.slice(l.indexOf(':') + 1).trim() : ''; };
    const getBubbles = prefix => lines.filter(l => l.toLowerCase().startsWith(prefix.toLowerCase())).map(l => l.slice(l.indexOf(':') + 1).trim());
    return {
      idx,
      title: get('TITULO') || get('TITLE') || (idx === 0 ? 'Variante A' : 'Variante C'),
      score: parseInt(get('SCORE')) || 0,
      tip: get('TIP'),
      msg1: getBubbles('MSG1_B'),
      msg2: getBubbles('MSG2_B'),
    };
  }).filter(v => v.msg1.length > 0);

  return { variants, extraMsgs };
}

// ── RENDER ───────────────────────────────────────────────────────────────────
function renderVariants(s) {
  const { variants, profileName, selectedIdx } = s;
  const maxScore = Math.max(...variants.map(v => v.score));
  const tagLabels = ['Variante A','Variante C','Variante C','Variante D'];
  const tagClasses = ['vtag-a','vtag-c','vtag-c','vtag-c'];

  setPill('Listo');

  let html = `
    <div class="profile-name">Perfil: <strong>${esc(profileName)}</strong></div>
    <div class="opts-row">
      <select id="idioma-sel">
        <option value="es"${s.idioma==='es'?' selected':''}>Español</option>
        <option value="en"${s.idioma==='en'?' selected':''}>English</option>
      </select>
      <select id="tono-sel">
        <option value="ameno"${s.tono==='ameno'?' selected':''}>Ameno y cercano</option>
        <option value="profesional"${s.tono==='profesional'?' selected':''}>Profesional</option>
        <option value="directo"${s.tono==='directo'?' selected':''}>Directo</option>
      </select>
      <button data-action="regenerate" style="background:#f5f5f5;border:1.5px solid #ddd;border-radius:6px;padding:4px 10px;cursor:pointer;font-size:12px;white-space:nowrap">↺ Regenerar</button>
    </div>
  `;

  variants.forEach((v, i) => {
    const isBest = maxScore > 0 && v.score === maxScore;
    const isSelected = selectedIdx === i;
    const tag = tagLabels[Math.min(i, tagLabels.length-1)];
    const tagCls = tagClasses[Math.min(i, tagClasses.length-1)];
    html += `
      <div class="variant-card${isBest?' best':''}${isSelected?' selected':''}" id="vcard-${i}" data-action="select-variant" data-idx="${i}">
        <div class="var-head">
          <span class="vtag ${tagCls}">${tag}</span>
          <span class="vtitle">${esc(v.title)}</span>
          ${isBest ? '<span class="best-badge">⭐ Mejor</span>' : ''}
          ${v.score ? `<span class="score-badge">${v.score}/10</span>` : ''}
        </div>
        <div class="bubbles">${v.msg1.map(b=>`<div class="bub">${esc(b)}</div>`).join('')}</div>
        ${v.tip ? `<div class="tip-text">${esc(v.tip)}</div>` : ''}
      </div>
    `;
  });

  const selV = selectedIdx !== null && selectedIdx >= 0 ? variants[selectedIdx] : null;
  html += `
    <div class="divider"></div>
    <button class="btn-primary" id="send-btn" data-action="start-send" ${selV ? '' : 'disabled'}>
      ${selV ? `Enviar MSG1 (${selV.msg1.length} burbujas) →` : 'Seleccioná una variante para enviar'}
    </button>
  `;

  setApp(html);
}

function renderSending(s) {
  const { sendCurrent, sendTotal, profileName } = s;
  const bubbles = s.sendBubbles || [];
  setPill('Enviando...');

  const items = bubbles.map((b, i) => {
    let icon, cls;
    if (i < sendCurrent) { icon = '✓'; cls = 'done'; }
    else if (i === sendCurrent) { icon = '⏳'; cls = 'active'; }
    else { icon = '○'; cls = ''; }
    return `<div class="progress-item ${cls}"><span class="prog-icon">${icon}</span><span>${esc(b.length > 55 ? b.substring(0,55)+'…' : b)}</span></div>`;
  }).join('');

  setApp(`
    <div class="profile-name">Enviando a <strong>${esc(profileName || '')}</strong>...</div>
    <div class="progress-list">${items}</div>
    <div style="font-size:11px;color:#aaa;margin-top:8px">Podés cerrar este popup — el envío continúa en segundo plano.</div>
  `);
}

function renderDone(s) {
  setPill('Listo!', 'rgba(27,122,60,.5)');
  setApp(`
    <div class="done-box">
      <div class="done-icon">✓</div>
      <div class="done-title">MSG1 enviado!</div>
      <div class="done-sub">Guardado en historial · ${esc(s.profileName || '')}</div>
    </div>
    <button class="btn-secondary" data-action="reset" style="margin-top:10px">Nuevo prospecto</button>
  `);
}

function renderOpenChatPrompt() {
  setPill('Acción requerida');
  setApp(`
    <div class="error-box" style="background:#FFF8F0;border-color:#FFD0A0;color:#7A3800">
      <strong>Abrí el chat manualmente:</strong><br><br>
      1. Hacé clic en <strong>"Enviar mensaje"</strong> en el perfil de LinkedIn<br>
      2. Cuando el chat esté abierto, volvé aquí y hacé clic en <strong>Continuar</strong>
      <br><button data-action="retry" style="margin-top:10px;background:#FF5A1F">✓ Chat abierto — Continuar</button>
    </div>
  `);
}

function renderError(s) {
  setPill('Error');
  setApp(`
    <div class="error-box">
      ${esc(s.sendError || s.errorMsg || 'Error desconocido').replace(/\n/g,'<br>')}
      <br><button data-action="retry">Reintentar</button>
    </div>
  `);
}

function renderLoading(msg, profileName) {
  setApp(`
    ${profileName ? `<div class="profile-name">Perfil: <strong>${esc(profileName)}</strong></div>` : ''}
    <div class="loading-wrap"><div class="spinner"></div><span>${esc(msg)}</span></div>
  `);
}

// ── ACTIONS (called from HTML onclick) ────────────────────────────────────────
async function doSelectVariant(idx) {
  const s = await getStorage('variants', 'selectedIdx');
  await setStorage({ selectedIdx: idx });
  // Update UI without full re-render
  document.querySelectorAll('.variant-card').forEach((el, i) => el.classList.toggle('selected', i === idx));
  const v = s.variants?.[idx];
  const btn = document.getElementById('send-btn');
  if (btn && v) {
    btn.disabled = false;
    btn.textContent = `Enviar MSG1 (${v.msg1.length} burbujas) →`;
  }
}

async function doRegenerate() {
  const idioma = document.getElementById('idioma-sel')?.value || 'es';
  const tono = document.getElementById('tono-sel')?.value || 'ameno';
  await setStorage({ idioma, tono, selectedIdx: null, phase: 'generating' });
  const s = await getStorage('tabId', 'profileText', 'profileName');
  await doGenerate(s.tabId, s.profileText, s.profileName, idioma, tono);
}

async function doStartSend(userConfirmedChatOpen = false) {
  // Show immediate feedback so user knows button worked
  setPill('Iniciando...');
  renderLoading('Iniciando envío...');

  let s;
  try {
    s = await getStorage('tabId', 'variants', 'selectedIdx', 'extraMsgs', 'profileName', 'profileText');
  } catch (e) {
    renderError({ sendError: 'Error al leer estado: ' + e.message });
    return;
  }

  if (s.selectedIdx === null || s.selectedIdx === undefined || s.selectedIdx < 0) {
    renderError({ sendError: 'Seleccioná una variante primero.' });
    return;
  }

  const v = s.variants?.[s.selectedIdx];
  if (!v?.msg1?.length) {
    renderError({ sendError: 'Variante inválida. Regenerá los mensajes.' });
    return;
  }

  // Ensure content script is injected
  await ensureContentScript(s.tabId);

  if (!userConfirmedChatOpen) {
    // Check chat is open
    setPill('Buscando chat...');
    let chatReady;
    try {
      chatReady = await sendToContent(s.tabId, { action: 'chat-ready' });
    } catch (e) {
      const isDisconnected = e.message.includes('Receiving end') || e.message.includes('establish connection');
      renderError({ sendError: isDisconnected
        ? 'Presioná F5 en la pestaña de LinkedIn y volvé a intentar.\n\n(Pasa una sola vez después de recargar la extensión.)'
        : 'No se pudo conectar con LinkedIn.\n' + e.message });
      return;
    }

    if (!chatReady?.ok) {
      await setStorage({ phase: 'open-chat', sendError: '__OPEN_CHAT__' });
      renderOpenChatPrompt();
      return;
    }
  }

  // Build historial entry
  const today = formatDate(new Date());
  const entry = {
    id: Date.now(),
    date: today,
    name: s.profileName,
    variantTitle: v.title,
    msg1: v.msg1.join('\n\n'),
    msg2: v.msg2.join('\n\n'),
    extraMsgs: s.extraMsgs || {},
    conversationHistory: [],
    stage: 1,
    stageHistory: [{ stage: 1, date: today, note: '' }],
    dossierMail: false,
    empresa: extractEmpresa(s.profileText || ''),
  };

  // Save send state and kick off background send
  await setStorage({
    phase: 'sending',
    sendCurrent: 0,
    sendTotal: v.msg1.length,
    sendBubbles: v.msg1,
    sendError: '',
  });

  chrome.runtime.sendMessage({ action: 'start-send', tabId: s.tabId, bubbles: v.msg1, entry });

  renderSending({ ...s, sendCurrent: 0, sendBubbles: v.msg1, phase: 'sending' });
}

function doRetryOrReset() {
  getStorage('sendError', 'variants', 'profileName', 'selectedIdx', 'idioma', 'tono', 'extraMsgs').then(s => {
    if (s.sendError === '__OPEN_CHAT__') {
      // User confirmed chat is open — skip chat-ready check, send directly
      setStorage({ phase: 'variants', sendError: '' }).then(() => doStartSend(true));
    } else if (s.variants?.length) {
      setStorage({ phase: 'variants', sendError: '' });
      renderVariants(s);
    } else {
      doReset();
    }
  });
}

async function doTestSend() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tabId = tabs[0]?.id;
  if (!tabId) { renderError({ sendError: 'No tab found' }); return; }

  const testBubbles = ['Hola! 👋', 'Esto es una prueba de envío.', 'Si ves esto, funciona!'];

  await setStorage({
    phase: 'open-chat', sendError: '__OPEN_CHAT__',
    tabId, profileName: 'TEST', profileText: '',
    variants: [{ idx: 0, title: 'Test', score: 10, tip: '', msg1: testBubbles, msg2: [] }],
    selectedIdx: 0, extraMsgs: {},
  });
  renderOpenChatPrompt();
}

async function doReset() {
  await chrome.storage.local.clear();
  setApp('<div class="loading-wrap" style="color:#aaa"><span>Abrí un perfil de LinkedIn para comenzar.</span></div>');
  setPill('—', 'rgba(255,255,255,.25)');
}

// ── CORE FLOW ─────────────────────────────────────────────────────────────────
async function doGenerate(tabId, profileText, profileName, idioma = 'es', tono = 'ameno') {
  setPill('Generando...');
  renderLoading('Generando mensajes...', profileName);

  const prompt = buildPrompt(profileText, idioma, tono);

  try {
    const res = await fetch('http://localhost:3000/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });
    if (!res.ok) throw new Error(`Error del servidor (${res.status})`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    const { variants, extraMsgs } = parseVariants(data.text);
    if (!variants.length) throw new Error('No se pudieron parsear las variantes. Intentá de nuevo.');

    const maxScore = Math.max(...variants.map(v => v.score));
    const bestIdx = maxScore > 0 ? variants.findIndex(v => v.score === maxScore) : 0;

    await setStorage({ phase: 'variants', variants, extraMsgs, selectedIdx: bestIdx });
    renderVariants({ variants, extraMsgs, profileName, selectedIdx: bestIdx, idioma, tono });

  } catch (e) {
    const msg = e.message.includes('Failed to fetch')
      ? 'Servidor no disponible.\nIniciá el servidor primero:\n\npython servidor.py'
      : e.message;
    await setStorage({ phase: 'error', sendError: msg });
    renderError({ sendError: msg });
  }
}

async function doScrapeAndGenerate(tabId, tabUrl) {
  setPill('Leyendo...');
  renderLoading('Leyendo perfil...');
  await setStorage({ phase: 'scraping', tabId, tabUrl, profileName: '', profileText: '', variants: [], selectedIdx: null });

  await sleep(300);
  await ensureContentScript(tabId);

  let scrapeResult;
  try {
    scrapeResult = await sendToContent(tabId, { action: 'scrape' });
  } catch (e) {
    const isDisconnected = e.message.includes('Receiving end') || e.message.includes('establish connection');
    const msg = isDisconnected
      ? 'Presioná F5 en la pestaña de LinkedIn y volvé a abrir la extensión.\n\n(Esto pasa una sola vez después de recargar la extensión.)'
      : 'No se pudo leer el perfil.\nRecargá la página e intentá de nuevo.\n\n' + e.message;
    await setStorage({ phase: 'error', sendError: msg });
    renderError({ sendError: msg });
    return;
  }

  if (!scrapeResult || scrapeResult.error) {
    const msg = scrapeResult?.error || 'No se pudo leer el perfil. Recargá la página e intentá de nuevo.';
    await setStorage({ phase: 'error', sendError: msg });
    renderError({ sendError: msg });
    return;
  }

  const { text: profileText, name: profileName } = scrapeResult;
  const s = await getStorage('idioma', 'tono');
  const idioma = s.idioma || 'es';
  const tono = s.tono || 'ameno';

  await setStorage({ profileText, profileName, phase: 'generating', idioma, tono });
  await doGenerate(tabId, profileText, profileName, idioma, tono);
}

// ── STORAGE CHANGE LISTENER — updates UI while popup is open ─────────────────
chrome.storage.local.onChanged.addListener(changes => {
  if (changes.phase) {
    const newPhase = changes.phase.newValue;
    if (newPhase === 'sending') {
      getStorage('sendCurrent', 'sendTotal', 'sendBubbles', 'profileName').then(s => renderSending(s));
    } else if (newPhase === 'done') {
      getStorage('profileName').then(s => renderDone(s));
    } else if (newPhase === 'open-chat') {
      renderOpenChatPrompt();
    } else if (newPhase === 'error') {
      getStorage('sendError').then(s => renderError(s));
    }
  }
  if (changes.sendCurrent) {
    getStorage('sendCurrent', 'sendTotal', 'sendBubbles', 'profileName').then(s => renderSending(s));
  }
});

// ── INIT ──────────────────────────────────────────────────────────────────────
async function init() {
  let tabs;
  try {
    tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  } catch (e) {
    renderError({ sendError: 'No se pudo acceder a la pestaña.' });
    return;
  }

  const tab = tabs[0];
  const isLinkedIn = tab?.url?.includes('linkedin.com/in/');

  if (!isLinkedIn) {
    setPill('—', 'rgba(255,255,255,.25)');
    setApp('<div class="loading-wrap" style="color:#aaa"><span>Abrí un perfil de LinkedIn para comenzar.</span></div>');
    return;
  }

  // DEV: inject test-send button (remove before production)
  const testBar = document.createElement('div');
  testBar.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#222;padding:6px;text-align:center;z-index:9999';
  testBar.innerHTML = '<button id="test-send-btn" style="background:#e67e22;color:white;border:none;border-radius:4px;padding:4px 12px;font-size:11px;cursor:pointer">⚡ Test envío (sin API)</button>';
  document.body.appendChild(testBar);
  document.getElementById('test-send-btn').addEventListener('click', doTestSend);

  // Read existing storage state
  const s = await getStorage('phase', 'tabUrl', 'tabId', 'variants', 'profileName', 'profileText',
    'selectedIdx', 'sendCurrent', 'sendTotal', 'sendBubbles', 'sendError', 'idioma', 'tono', 'extraMsgs');

  const sameProfile = s.tabUrl === tab.url && s.phase && s.phase !== 'idle';

  if (sameProfile) {
    // Restore state for same profile
    if (s.phase === 'variants') {
      renderVariants(s);
    } else if (s.phase === 'sending') {
      renderSending(s);
    } else if (s.phase === 'done') {
      renderDone(s);
    } else if (s.phase === 'open-chat') {
      renderOpenChatPrompt();
    } else if (s.phase === 'error') {
      renderError(s);
    } else if (s.phase === 'generating' || s.phase === 'scraping') {
      // Was generating when closed — resume
      renderLoading(s.phase === 'scraping' ? 'Leyendo perfil...' : 'Generando mensajes...', s.profileName);
      if (s.phase === 'generating' && s.profileText) {
        await doGenerate(s.tabId, s.profileText, s.profileName, s.idioma, s.tono);
      } else {
        await doScrapeAndGenerate(tab.id, tab.url);
      }
    } else {
      await doScrapeAndGenerate(tab.id, tab.url);
    }
  } else {
    // New profile — start fresh
    await chrome.storage.local.clear();
    await doScrapeAndGenerate(tab.id, tab.url);
  }
}

// ── EVENT DELEGATION (no inline onclick — CSP compliance) ────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('app').addEventListener('click', e => {
    const el = e.target.closest('[data-action]');
    if (!el) return;
    const action = el.dataset.action;
    const idx = el.dataset.idx !== undefined ? parseInt(el.dataset.idx) : undefined;
    if (action === 'select-variant') doSelectVariant(idx);
    else if (action === 'start-send') doStartSend();
    else if (action === 'reset') doReset();
    else if (action === 'retry') doRetryOrReset();
    else if (action === 'regenerate') doRegenerate();
    else if (action === 'test-send') doTestSend();
  });
  init();
});
