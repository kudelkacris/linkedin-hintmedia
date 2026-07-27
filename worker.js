export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    const cors = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') return new Response(null, { headers: cors });

    const json = (data, status = 200) =>
      new Response(JSON.stringify(data), {
        status,
        headers: { ...cors, 'Content-Type': 'application/json' },
      });

    const getAll = async () => {
      const raw = await env.LINKEDIN_KV.get('clientes');
      return raw ? JSON.parse(raw) : [];
    };

    const saveAll = (list) =>
      env.LINKEDIN_KV.put('clientes', JSON.stringify(list));

    // GET /api/clientes
    if (path === '/api/clientes' && request.method === 'GET') {
      return json(await getAll());
    }

    // POST /api/clientes
    if (path === '/api/clientes' && request.method === 'POST') {
      const body = await request.json();
      const list = await getAll();
      const nuevo = {
        id: Date.now().toString(),
        autor: body.autor || 'Anónimo',
        titulo: body.titulo || '',
        texto: body.texto || '',
        urgencia: body.urgencia || 'media',
        categoria: body.categoria || 'interno',
        estado: 'pendiente',
        fecha: new Date().toISOString(),
        respuestas: [],
      };
      list.unshift(nuevo);
      await saveAll(list);
      return json(nuevo, 201);
    }

    // PUT /api/clientes/:id/responder
    const mResp = path.match(/^\/api\/clientes\/(\w+)\/responder$/);
    if (mResp && request.method === 'PUT') {
      const id = mResp[1];
      const body = await request.json();
      const list = await getAll();
      const idx = list.findIndex(c => c.id === id);
      if (idx === -1) return json({ error: 'Not found' }, 404);
      list[idx].respuestas.push({
        autor: body.autor || 'Anónimo',
        texto: body.texto || '',
        link: body.link || null,
        fecha: new Date().toISOString(),
      });
      if (body.resolverAlResponder) list[idx].estado = 'resuelto';
      await saveAll(list);
      return json(list[idx]);
    }

    // PUT /api/clientes/:id/estado
    const mEst = path.match(/^\/api\/clientes\/(\w+)\/estado$/);
    if (mEst && request.method === 'PUT') {
      const id = mEst[1];
      const { estado } = await request.json();
      const list = await getAll();
      const idx = list.findIndex(c => c.id === id);
      if (idx === -1) return json({ error: 'Not found' }, 404);
      list[idx].estado = estado;
      await saveAll(list);
      return json(list[idx]);
    }

    // PUT /api/clientes/:id/editar
    const mEdit = path.match(/^\/api\/clientes\/(\w+)\/editar$/);
    if (mEdit && request.method === 'PUT') {
      const id = mEdit[1];
      const body = await request.json();
      const list = await getAll();
      const idx = list.findIndex(c => c.id === id);
      if (idx === -1) return json({ error: 'Not found' }, 404);
      if (body.titulo)    list[idx].titulo    = body.titulo;
      if (body.texto !== undefined) list[idx].texto = body.texto;
      if (body.urgencia)  list[idx].urgencia  = body.urgencia;
      if (body.categoria) list[idx].categoria = body.categoria;
      if (body.asignado !== undefined) list[idx].asignado = body.asignado;
      await saveAll(list);
      return json(list[idx]);
    }

    // DELETE /api/clientes/:id
    const mDel = path.match(/^\/api\/clientes\/(\w+)$/);
    if (mDel && request.method === 'DELETE') {
      const id = mDel[1];
      const list = await getAll();
      await saveAll(list.filter(c => c.id !== id));
      return json({ ok: true });
    }

    // POST /api/files
    if (path === '/api/files' && request.method === 'POST') {
      const formData = await request.formData();
      const file = formData.get('file');
      if (!file) return json({ error: 'No file' }, 400);
      const MAX = 5 * 1024 * 1024;
      const buf = await file.arrayBuffer();
      if (buf.byteLength > MAX) return json({ error: 'Archivo muy grande (máx 5 MB)' }, 413);
      const id = Date.now().toString();
      await env.LINKEDIN_KV.put(`file_${id}`, buf, {
        metadata: { name: file.name, type: file.type },
      });
      const fileUrl = `${new URL(request.url).origin}/api/files/${id}`;
      return json({ id, url: fileUrl, name: file.name, type: file.type }, 201);
    }

    // GET /api/files/:id
    const mFile = path.match(/^\/api\/files\/(\w+)$/);
    if (mFile && request.method === 'GET') {
      const { value, metadata } = await env.LINKEDIN_KV.getWithMetadata(`file_${mFile[1]}`, 'arrayBuffer');
      if (!value) return json({ error: 'Not found' }, 404);
      return new Response(value, {
        headers: {
          ...cors,
          'Content-Type': metadata?.type || 'application/octet-stream',
          'Content-Disposition': `inline; filename="${metadata?.name || 'file'}"`,
        },
      });
    }

    return json({ error: 'Not found' }, 404);
  },
};
