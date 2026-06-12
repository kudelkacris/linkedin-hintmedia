---
name: feedback-fixes
description: Errores ya resueltos en este proyecto — no repetir
metadata:
  type: feedback
---

# Problemas resueltos

## Emoji en print() rompe Windows (cp1252)
`print(f'🚀 ...')` → UnicodeEncodeError en Python/Windows.
**Fix:** sacar el emoji del print.

## Model ID incorrecto
`claude-opus-4-1` no existe. `claude-haiku-4-5-20241022` tampoco.
**Correcto:** `claude-haiku-4-5-20251001`
**How to apply:** siempre verificar model ID contra la lista oficial antes de escribirlo.

## fetch falla desde file://
Browser bloquea requests a localhost cuando index.html se abre como file://.
**Fix:** servidor.py sirve index.html en do_GET('/'), abrir desde http://localhost:3000.

## Puerto ocupado (WinError 10048)
Servidor anterior sigue corriendo.
**Fix:** `netstat -ano | findstr :3000` → `taskkill /PID XXXX /F` → reiniciar.

## const SYSTEM esta en index.html, no en servidor.py
El prompt del sistema vive en el JS del frontend.
**How to apply:** editar index.html para cambiar el prompt/contexto de Hint Media.

## NetworkError al generar (CORS) — sesion 2
index.html nuevo tenia callAPI() llamando a Anthropic directamente desde el browser.
El browser bloquea eso por CORS (no se puede llamar a APIs externas con API key desde el frontend).
**Fix:** reemplazar fetch(API_URL, { headers: {'x-api-key': ...} }) por fetch('http://localhost:3000/api/generate', { body: { prompt } }).
El servidor es quien habla con Anthropic, no el browser.
**How to apply:** si en index.html aparece API_URL o x-api-key en un fetch, es el bug.

## index.html vacia / archivo sin extension
En sesion 2 el archivo se llamo 'index' sin extension y estaba vacio.
**Fix:** escribir index.html completo desde Claude con Write tool.
