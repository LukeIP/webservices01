/* ---------- API Client ---------- */
const API = {
  BASE: '/api/v1',

  /* --- Token helpers --- */
  getToken()       { return localStorage.getItem('access_token'); },
  setToken(t)      { localStorage.setItem('access_token', t); },
  clearToken()     { localStorage.removeItem('access_token'); },

  /* --- Generic request --- */
  async request(method, path, { body, params } = {}) {
    const url = new URL(this.BASE + path, location.origin);
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
      }
    }
    const headers = {};
    if (body) headers['Content-Type'] = 'application/json';
    const token = this.getToken();
    if (token) headers['Authorization'] = 'Bearer ' + token;

    const res = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 204) return null;
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      const err = new Error(data?.detail || res.statusText);
      err.status = res.status;
      err.code = data?.code;
      throw err;
    }
    return data;
  },

  get(p, params)   { return this.request('GET',    p, { params }); },
  post(p, body)    { return this.request('POST',   p, { body }); },
  put(p, body)     { return this.request('PUT',    p, { body }); },
  del(p)           { return this.request('DELETE', p); },

  /* ===== Auth ===== */
  register(d)       { return this.post('/auth/register', d); },
  login(d)          { return this.post('/auth/login', d); },
  me()              { return this.get('/auth/me'); },
  refresh()         { return this.post('/auth/refresh'); },

  /* ===== Cities ===== */
  getCities(p)      { return this.get('/cities', p); },
  getCity(id)       { return this.get('/cities/' + id); },
  createCity(d)     { return this.post('/cities', d); },
  updateCity(id, d) { return this.put('/cities/' + id, d); },
  deleteCity(id)    { return this.del('/cities/' + id); },

  /* ===== Observations ===== */
  getObservations(cid, p)  { return this.get('/cities/' + cid + '/observations', p); },
  createObservation(cid,d) { return this.post('/cities/' + cid + '/observations', d); },
  updateObservation(id, d) { return this.put('/observations/' + id, d); },
  deleteObservation(id)    { return this.del('/observations/' + id); },

  /* ===== Climate Metrics ===== */
  getClimateMetrics(cid, p)   { return this.get('/cities/' + cid + '/climate-metrics', p); },
  getClimateMetric(id)        { return this.get('/climate-metrics/' + id); },
  createClimateMetric(cid, d) { return this.post('/cities/' + cid + '/climate-metrics', d); },
  deleteClimateMetric(id)     { return this.del('/climate-metrics/' + id); },

  /* ===== Socioeconomic Metrics ===== */
  getSocioMetrics(cid, p)   { return this.get('/cities/' + cid + '/socioeconomic-metrics', p); },
  getSocioMetric(id)        { return this.get('/socioeconomic-metrics/' + id); },
  createSocioMetric(cid, d) { return this.post('/cities/' + cid + '/socioeconomic-metrics', d); },
  deleteSocioMetric(id)     { return this.del('/socioeconomic-metrics/' + id); },

  /* ===== Analytics ===== */
  liveability(cid)           { return this.get('/cities/' + cid + '/liveability'); },
  compareCities(ids)         { return this.get('/cities/compare', { ids: ids.join(',') }); },
  trends(cid, p)             { return this.get('/cities/' + cid + '/trends', p); },
  anomalies(cid, p)          { return this.get('/cities/' + cid + '/anomalies', p); },

  /* ===== Query ===== */
  query(question)            { return this.post('/query', { question }); },
  narrative(cid)             { return this.get('/cities/' + cid + '/narrative'); },

  /* ===== Rent Submissions (crowdsourced) ===== */
  submitRent(cid, d)         { return this.post('/cities/' + cid + '/rent-submissions', d); },
  getRentSubmissions(cid, p) { return this.get('/cities/' + cid + '/rent-submissions', p); },
  getRentMedian(cid, p)      { return this.get('/cities/' + cid + '/rent-median', p); },

  /* ===== Health ===== */
  health()                   { return fetch('/').then(r => r.json()); },
};
