---
name: project-estado
description: Stack actual, archivos, cómo correr el proyecto, estado funcional
metadata:
  type: project
---

# Estado del proyecto — Linkedin Generator (Hint Media)

Ultima actualizacion: 2026-06-01 (sesion 2)

## Archivos

- `servidor.py` — backend Python, puerto 3000, sirve index.html en GET / y API en POST /api/generate
- `index.html` — UI nueva con diseno premium (DM Serif + DM Sans, colores orange/dark), sidebar historial localStorage, variantes A/B/C con burbujas, hilo de conversacion con pasos
- `MEMORY.md` — indice de memoria del proyecto
- `hint_media.md` — contexto Hint Media, clientes, prompt sistema
- `feedback_fixes.md` — errores ya resueltos

## Estado actual

FUNCIONAL. index.html actualizado por el usuario a version premium con nuevo diseno.
callAPI() corregido para usar localhost:3000 en vez de llamar a Anthropic directamente (causaba NetworkError CORS).

## Cómo correr

```powershell
cd "c:\Users\neces\Desktop\CLAUDE\Linkedin"
python servidor.py
```

Luego abrir: `http://localhost:3000`
(NO abrir index.html como file:// — CORS bloquea el fetch)

## Stack

- Backend: Python stdlib (http.server, socketserver) + httpx para llamadas a API
- Frontend: HTML/CSS/JS vanilla, Google Fonts (DM Serif Display + DM Sans), sin frameworks
- API: Anthropic claude-haiku-4-5-20251001, max_tokens 2200
- Puerto: 3000, solo localhost (127.0.0.1)

## Flujo

1. Usuario pega perfil LinkedIn + elige idioma/tono
2. Frontend arma prompt con SYSTEM de Hint Media y llama POST /api/generate a localhost:3000
3. servidor.py llama Anthropic API con httpx.Client persistente
4. Devuelve texto que el frontend parsea (variantes A/B/C)
5. Usuario selecciona variante → hilo de conversacion con pasos de seguimiento

## Arquitectura callAPI (IMPORTANTE)

callAPI() en index.html llama a `http://localhost:3000/api/generate` con solo `{ prompt }`.
El servidor agrega API key, model, headers. El browser NUNCA toca Anthropic directamente.

## Por qué se sirve desde el servidor

Browser bloquea fetch a localhost desde file://. Solucion: do_GET en servidor.py sirve index.html.
