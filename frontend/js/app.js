/* ==========================================================
   City Liveability Dashboard — main application logic
   ========================================================== */

const CATEGORIES = ['air_quality','noise','safety','cleanliness','green_space','transport','general'];
const CLIMATE_METRICS = ['aqi','avg_temp_c','humidity_pct','precipitation_mm'];
const PERIODS = ['3m','6m','12m','24m'];

/* ---------------------- Helpers ---------------------- */
function $(sel, ctx = document) { return ctx.querySelector(sel); }
function $$(sel, ctx = document) { return [...ctx.querySelectorAll(sel)]; }
function show(el) { el.classList.remove('d-none'); el.classList.add('active'); }
function hide(el) { el.classList.add('d-none'); el.classList.remove('active'); }
function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
function scoreCls(v) {
  if (v >= 80) return 'excellent';
  if (v >= 60) return 'good';
  if (v >= 40) return 'average';
  if (v >= 20) return 'poor';
  return 'bad';
}
function scoreColor(v) {
  if (v >= 80) return '#198754';
  if (v >= 60) return '#20c997';
  if (v >= 40) return '#ffc107';
  if (v >= 20) return '#fd7e14';
  return '#dc3545';
}
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-GB') : '—'; }
function fmtNum(n, dec = 1) { return n != null ? Number(n).toFixed(dec) : '—'; }

/* Keep a reference to any live Chart.js instance so we can destroy before re-creating */
let _charts = {};
function makeChart(canvasId, cfg) {
  if (_charts[canvasId]) _charts[canvasId].destroy();
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  _charts[canvasId] = new Chart(ctx, cfg);
  return _charts[canvasId];
}

/* ==================== Toast ==================== */
function toast(msg, type = 'success') {
  const el = $('#app-toast');
  el.className = 'toast text-white bg-' + (type === 'error' ? 'danger' : type);
  el.querySelector('.toast-body').textContent = msg;
  bootstrap.Toast.getOrCreateInstance(el, { delay: 3000 }).show();
}

/* ==================== APP ==================== */
const App = {
  user: null,
  currentPage: null,
  cityCache: [],          // lightweight list for dropdowns

  async init() {
    /* Nav links */
    $$('[data-page]').forEach(a => a.addEventListener('click', e => {
      e.preventDefault();
      App.navigate(a.dataset.page);
    }));
    /* Auth forms */
    $('#form-login').addEventListener('submit',    Auth.handleLogin);
    $('#form-register').addEventListener('submit', Auth.handleRegister);
    $('#btn-logout').addEventListener('click',     Auth.logout);

    /* City form */
    $('#form-city').addEventListener('submit', CitiesPage.handleSave);

    /* Observation form */
    $('#form-observation').addEventListener('submit', CityDetail.handleSaveObservation);

    /* Metric forms */
    $('#form-climate').addEventListener('submit', CityDetail.handleSaveClimate);
    $('#form-socio').addEventListener('submit',   CityDetail.handleSaveSocio);
    $('#form-rent').addEventListener('submit',    CityDetail.handleSaveRent);

    /* Analytics controls */
    $('#btn-compare').addEventListener('click',   AnalyticsPage.handleCompare);
    $('#btn-trend').addEventListener('click',     AnalyticsPage.handleTrend);
    $('#btn-anomaly').addEventListener('click',   AnalyticsPage.handleAnomaly);

    /* Analytics sub-tabs */
    $$('#analytics-tabs [data-tab]').forEach(a => a.addEventListener('click', e => {
      e.preventDefault();
      $$('#analytics-tabs .nav-link').forEach(l => l.classList.remove('active'));
      a.classList.add('active');
      $$('.analytics-tab').forEach(t => hide(t));
      show($('#tab-' + a.dataset.tab));
    }));

    /* Query / Narrative controls */
    $('#btn-narrative').addEventListener('click', QueryPage.handleNarrative);

    /* Try restoring session */
    if (API.getToken()) {
      try {
        App.user = await API.me();
        Auth.updateUI();
      } catch {
        API.clearToken();
      }
    }
    Auth.updateUI();

    /* Load dashboard */
    App.navigate('dashboard');
  },

  navigate(page, params) {
    /* Update nav active state */
    $$('[data-page]').forEach(a => {
      a.classList.toggle('active', a.dataset.page === page || (page === 'city-detail' && a.dataset.page === 'cities'));
    });
    /* Hide all pages then show target */
    $$('.page-content').forEach(p => { p.style.display = 'none'; p.classList.remove('active'); });
    const el = $('#page-' + page);
    if (el) { el.style.display = 'block'; el.classList.add('active'); }
    App.currentPage = page;

    /* Page-specific load */
    switch (page) {
      case 'dashboard':     Dashboard.load(); break;
      case 'cities':        CitiesPage.load(); break;
      case 'city-detail':   CityDetail.load(params); break;
      case 'analytics':     AnalyticsPage.init(); break;
      case 'query':         QueryPage.init(); break;
    }
  },
};

/* ==================== AUTH ==================== */
const Auth = {
  updateUI() {
    const logged = !!App.user;
    document.body.classList.toggle('logged-in', logged);
    if (logged) {
      $('#auth-user-name').textContent = App.user.username;
      show($('#auth-logged-in'));
      hide($('#auth-guest'));
    } else {
      hide($('#auth-logged-in'));
      show($('#auth-guest'));
    }
  },

  async handleLogin(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const res = await API.login({ username: fd.get('username'), password: fd.get('password') });
      API.setToken(res.access_token);
      App.user = await API.me();
      Auth.updateUI();
      bootstrap.Modal.getInstance($('#loginModal')).hide();
      e.target.reset();
      toast('Welcome back, ' + App.user.username);
    } catch (err) { toast(err.message, 'error'); }
  },

  async handleRegister(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await API.register({ username: fd.get('username'), email: fd.get('email'), password: fd.get('password') });
      toast('Account created! You can now log in.');
      bootstrap.Modal.getInstance($('#registerModal')).hide();
      e.target.reset();
      new bootstrap.Modal($('#loginModal')).show();
    } catch (err) { toast(err.message, 'error'); }
  },

  logout() {
    API.clearToken();
    App.user = null;
    Auth.updateUI();
    toast('Logged out');
    App.navigate('dashboard');
  },
};

/* ==================== DASHBOARD ==================== */
const Dashboard = {
  async load() {
    try {
      const [health, cities] = await Promise.all([API.health(), API.getCities({ limit: 100 })]);
      $('#health-status').innerHTML =
        health.status === 'healthy'
          ? '<span class="badge bg-success"><i class="bi bi-check-circle"></i> Healthy</span>'
          : '<span class="badge bg-danger">Down</span>';
      $('#health-version').textContent = 'v' + (health.version || '?');
      $('#city-count').textContent = cities.total;

      /* Cache city list for dropdowns */
      App.cityCache = cities.items;
      _populateCityDropdowns(cities.items);

      /* Render city cards */
      const container = $('#dashboard-cities');
      container.innerHTML = '';
      for (const c of cities.items.slice(0, 6)) {
        container.innerHTML += `
          <div class="col-md-4 col-lg-3 mb-3">
            <div class="card stat-card h-100 clickable" onclick="App.navigate('city-detail',${c.id})">
              <div class="card-body">
                <h6 class="card-title mb-1">${escapeHtml(c.name)}</h6>
                <small class="text-muted">${escapeHtml(c.region)}</small>
                ${c.population ? `<p class="mb-0 mt-2 text-muted" style="font-size:.85rem">Pop: ${c.population.toLocaleString()}</p>` : ''}
              </div>
            </div>
          </div>`;
      }
    } catch (err) { toast(err.message, 'error'); }
  },
};

/* ==================== CITIES PAGE ==================== */
const CitiesPage = {
  offset: 0,
  limit: 20,

  async load() {
    try {
      const region = $('#filter-region').value || undefined;
      const data = await API.getCities({ offset: this.offset, limit: this.limit, region });
      App.cityCache = data.items.length > App.cityCache.length ? data.items : App.cityCache;
      this.render(data);
    } catch (err) { toast(err.message, 'error'); }
  },

  render({ items, total, offset, limit }) {
    const tbody = $('#cities-tbody');
    tbody.innerHTML = '';
    if (!items.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No cities found</td></tr>';
    }
    for (const c of items) {
      tbody.innerHTML += `
        <tr class="clickable" onclick="App.navigate('city-detail',${c.id})">
          <td>${c.id}</td>
          <td>${escapeHtml(c.name)}</td>
          <td>${escapeHtml(c.region)}</td>
          <td>${c.population ? c.population.toLocaleString() : '—'}</td>
          <td>${fmtNum(c.latitude, 4)}, ${fmtNum(c.longitude, 4)}</td>
          <td>
            <button class="btn btn-sm btn-outline-primary auth-only" title="Edit"
              onclick="event.stopPropagation(); CitiesPage.openEdit(${c.id})"><i class="bi bi-pencil"></i></button>
            <button class="btn btn-sm btn-outline-danger auth-only" title="Delete"
              onclick="event.stopPropagation(); CitiesPage.handleDelete(${c.id})"><i class="bi bi-trash"></i></button>
          </td>
        </tr>`;
    }
    /* Pagination */
    const pages = Math.ceil(total / limit);
    const cur = Math.floor(offset / limit);
    let pg = '<nav><ul class="pagination pagination-sm justify-content-center">';
    pg += `<li class="page-item ${cur === 0 ? 'disabled' : ''}"><a class="page-link" onclick="CitiesPage.goPage(${cur - 1})">«</a></li>`;
    for (let i = 0; i < pages; i++) {
      pg += `<li class="page-item ${i === cur ? 'active' : ''}"><a class="page-link" onclick="CitiesPage.goPage(${i})">${i + 1}</a></li>`;
    }
    pg += `<li class="page-item ${cur >= pages - 1 ? 'disabled' : ''}"><a class="page-link" onclick="CitiesPage.goPage(${cur + 1})">»</a></li>`;
    pg += '</ul></nav>';
    $('#cities-pagination').innerHTML = pg;

    /* Region filter */
    const sel = $('#filter-region');
    if (sel.options.length <= 1 && items.length) {
      const regions = [...new Set(items.map(c => c.region))].sort();
      regions.forEach(r => { const o = new Option(r, r); sel.add(o); });
    }
  },

  goPage(p) { this.offset = p * this.limit; this.load(); },

  /* Add / Edit city */
  editingCityId: null,

  openAdd() {
    this.editingCityId = null;
    $('#cityModalLabel').textContent = 'Add City';
    $('#form-city').reset();
    $('#city-country').value = 'United Kingdom';
    new bootstrap.Modal($('#cityModal')).show();
  },

  async openEdit(id) {
    try {
      const c = await API.getCity(id);
      this.editingCityId = id;
      $('#cityModalLabel').textContent = 'Edit City';
      $('#city-name').value = c.name;
      $('#city-region').value = c.region;
      $('#city-country').value = c.country;
      $('#city-lat').value = c.latitude;
      $('#city-lng').value = c.longitude;
      $('#city-pop').value = c.population || '';
      new bootstrap.Modal($('#cityModal')).show();
    } catch (err) { toast(err.message, 'error'); }
  },

  async handleSave(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      name: fd.get('name'),
      region: fd.get('region'),
      country: fd.get('country'),
      latitude: parseFloat(fd.get('latitude')),
      longitude: parseFloat(fd.get('longitude')),
    };
    const pop = fd.get('population');
    if (pop) body.population = parseInt(pop, 10);

    try {
      if (CitiesPage.editingCityId) {
        await API.updateCity(CitiesPage.editingCityId, body);
        toast('City updated');
      } else {
        await API.createCity(body);
        toast('City created');
      }
      bootstrap.Modal.getInstance($('#cityModal')).hide();
      e.target.reset();
      CitiesPage.load();
    } catch (err) { toast(err.message, 'error'); }
  },

  async handleDelete(id) {
    if (!confirm('Delete this city? This cannot be undone.')) return;
    try { await API.deleteCity(id); toast('City deleted'); this.load(); }
    catch (err) { toast(err.message, 'error'); }
  },
};

/* Region filter change */
document.addEventListener('DOMContentLoaded', () => {
  $('#filter-region')?.addEventListener('change', () => { CitiesPage.offset = 0; CitiesPage.load(); });
});

/* ==================== CITY DETAIL ==================== */
const CityDetail = {
  cityId: null,
  city: null,

  async load(cityId) {
    this.cityId = cityId;
    const container = $('#city-detail-content');
    container.innerHTML = '<div class="spinner-overlay"><div class="spinner-border text-primary"></div></div>';
    try {
      const city = await API.getCity(cityId);
      this.city = city;
      this.renderShell(city);
      /* Default to liveability tab */
      this.switchTab('liveability');
    } catch (err) {
      container.innerHTML = '<div class="alert alert-danger">City not found.</div>';
    }
  },

  renderShell(c) {
    const container = $('#city-detail-content');
    container.innerHTML = `
      <div class="d-flex align-items-center mb-3">
        <button class="btn btn-sm btn-outline-secondary me-3" onclick="App.navigate('cities')"><i class="bi bi-arrow-left"></i> Back</button>
        <h2 class="mb-0">${escapeHtml(c.name)}</h2>
        <span class="badge bg-secondary ms-2">${escapeHtml(c.region)}</span>
      </div>
      <div class="row mb-3">
        <div class="col-md-8">
          <div class="card">
            <div class="card-body">
              <div class="row text-center">
                <div class="col"><small class="text-muted">Country</small><p class="mb-0 fw-bold">${escapeHtml(c.country)}</p></div>
                <div class="col"><small class="text-muted">Population</small><p class="mb-0 fw-bold">${c.population ? c.population.toLocaleString() : '—'}</p></div>
                <div class="col"><small class="text-muted">Latitude</small><p class="mb-0 fw-bold">${fmtNum(c.latitude, 4)}</p></div>
                <div class="col"><small class="text-muted">Longitude</small><p class="mb-0 fw-bold">${fmtNum(c.longitude, 4)}</p></div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-4 d-flex align-items-center justify-content-end gap-2">
          <button class="btn btn-outline-primary btn-sm auth-only" onclick="CitiesPage.openEdit(${c.id})"><i class="bi bi-pencil"></i> Edit</button>
          <button class="btn btn-outline-danger btn-sm auth-only" onclick="CityDetail.deleteCity()"><i class="bi bi-trash"></i> Delete</button>
        </div>
      </div>

      <!-- Tabs -->
      <ul class="nav nav-tabs detail-tabs mb-3">
        <li class="nav-item"><a class="nav-link active" href="#" onclick="CityDetail.switchTab('liveability',event)">Liveability</a></li>
        <li class="nav-item"><a class="nav-link" href="#" onclick="CityDetail.switchTab('observations',event)">Observations</a></li>
        <li class="nav-item"><a class="nav-link" href="#" onclick="CityDetail.switchTab('climate',event)">Climate Metrics</a></li>
        <li class="nav-item"><a class="nav-link" href="#" onclick="CityDetail.switchTab('socio',event)">Socioeconomic</a></li>
      </ul>
      <div id="detail-tab-content"></div>
    `;
    /* Re-apply auth visibility */
    Auth.updateUI();
  },

  switchTab(tab, e) {
    if (e) e.preventDefault();
    $$('.detail-tabs .nav-link').forEach(l => l.classList.remove('active'));
    /* find the matching tab link */
    const link = $$('.detail-tabs .nav-link').find(l => l.textContent.toLowerCase().includes(tab === 'socio' ? 'socio' : tab === 'climate' ? 'climate' : tab));
    if (link) link.classList.add('active');

    switch (tab) {
      case 'liveability':   this.loadLiveability(); break;
      case 'observations':  this.loadObservations(); break;
      case 'climate':       this.loadClimate(); break;
      case 'socio':         this.loadSocio(); break;
    }
  },

  /* --- Liveability --- */
  async loadLiveability() {
    const el = $('#detail-tab-content');
    el.innerHTML = '<div class="spinner-overlay"><div class="spinner-border text-primary"></div></div>';
    try {
      const data = await API.liveability(this.cityId);
      const scores = [
        { label: 'Overall',        value: data.overall_score },
        { label: 'Climate',        value: data.climate_score },
        { label: 'Affordability',  value: data.affordability_score },
        { label: 'Safety',         value: data.safety_score },
        { label: 'Environment',    value: data.environment_score },
      ];
      el.innerHTML = `
        <div class="row">
          <div class="col-lg-6">
            <div class="card mb-3"><div class="card-body text-center">
              <h5>Overall Liveability Score</h5>
              <div class="score-badge ${scoreCls(data.overall_score)} mx-auto mb-2" style="width:90px;height:90px;font-size:1.6rem;">
                ${fmtNum(data.overall_score, 0)}
              </div>
              <p class="text-muted mb-0">Computed ${fmtDate(data.computed_at)}</p>
            </div></div>
            <div class="card"><div class="card-body">
              <h6>Score Breakdown</h6>
              ${scores.map(s => `
                <div class="d-flex align-items-center mb-2">
                  <span class="me-2" style="width:110px;font-size:.9rem">${s.label}</span>
                  <div class="score-bar flex-grow-1 me-2">
                    <div class="score-bar-fill" style="width:${s.value}%;background:${scoreColor(s.value)}"></div>
                  </div>
                  <span class="fw-bold" style="width:40px;text-align:right">${fmtNum(s.value, 0)}</span>
                </div>`).join('')}
            </div></div>
          </div>
          <div class="col-lg-6">
            <div class="card"><div class="card-body">
              <h6>Weights Used</h6>
              <pre class="mb-0" style="font-size:.85rem">${JSON.stringify(data.weights_used, null, 2)}</pre>
            </div></div>
          </div>
        </div>`;
    } catch (err) {
      el.innerHTML = `<div class="alert alert-warning">${escapeHtml(err.message)}</div>`;
    }
  },

  /* --- Observations --- */
  obsOffset: 0,
  async loadObservations() {
    const el = $('#detail-tab-content');
    el.innerHTML = '<div class="spinner-overlay"><div class="spinner-border text-primary"></div></div>';
    try {
      const data = await API.getObservations(this.cityId, { offset: this.obsOffset, limit: 20 });
      let html = `
        <div class="d-flex justify-content-between mb-2">
          <h5>Observations <span class="badge bg-secondary">${data.total}</span></h5>
          <button class="btn btn-sm btn-primary auth-only" onclick="CityDetail.openAddObservation()">+ Add</button>
        </div>
        <div class="table-responsive"><table class="table table-sm table-striped">
          <thead><tr><th>ID</th><th>Category</th><th>Value</th><th>Note</th><th>Recorded</th><th class="auth-only">Actions</th></tr></thead>
          <tbody>`;
      for (const o of data.items) {
        html += `<tr>
          <td>${o.id}</td>
          <td><span class="badge bg-info badge-category">${escapeHtml(o.category)}</span></td>
          <td>${fmtNum(o.value)}</td>
          <td>${o.note ? escapeHtml(o.note) : '—'}</td>
          <td>${fmtDate(o.recorded_at)}</td>
          <td class="auth-only">
            <button class="btn btn-sm btn-outline-primary" onclick="CityDetail.openEditObservation(${o.id},'${escapeHtml(o.category)}',${o.value},'${o.note ? escapeHtml(o.note).replace(/'/g, "\\'") : ''}')"><i class="bi bi-pencil"></i></button>
            <button class="btn btn-sm btn-outline-danger" onclick="CityDetail.deleteObservation(${o.id})"><i class="bi bi-trash"></i></button>
          </td></tr>`;
      }
      html += '</tbody></table></div>';
      el.innerHTML = html;
      Auth.updateUI();
    } catch (err) { $('#detail-tab-content').innerHTML = `<div class="alert alert-warning">${escapeHtml(err.message)}</div>`; }
  },

  openAddObservation() {
    $('#form-observation').reset();
    $('#obs-id').value = '';
    $('#observationModalLabel').textContent = 'Add Observation';
    new bootstrap.Modal($('#observationModal')).show();
  },

  openEditObservation(id, cat, val, note) {
    $('#obs-id').value = id;
    $('#obs-category').value = cat;
    $('#obs-value').value = val;
    $('#obs-note').value = note;
    $('#observationModalLabel').textContent = 'Edit Observation';
    new bootstrap.Modal($('#observationModal')).show();
  },

  async handleSaveObservation(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = { category: fd.get('category'), value: parseFloat(fd.get('value')) };
    const note = fd.get('note');
    if (note) body.note = note;
    const obsId = fd.get('obs_id');
    try {
      if (obsId) {
        await API.updateObservation(obsId, body);
        toast('Observation updated');
      } else {
        await API.createObservation(CityDetail.cityId, body);
        toast('Observation created');
      }
      bootstrap.Modal.getInstance($('#observationModal')).hide();
      CityDetail.loadObservations();
    } catch (err) { toast(err.message, 'error'); }
  },

  async deleteObservation(id) {
    if (!confirm('Delete this observation?')) return;
    try { await API.deleteObservation(id); toast('Deleted'); this.loadObservations(); }
    catch (err) { toast(err.message, 'error'); }
  },

  /* --- Climate Metrics --- */
  async loadClimate() {
    const el = $('#detail-tab-content');
    el.innerHTML = '<div class="spinner-overlay"><div class="spinner-border text-primary"></div></div>';
    try {
      const data = await API.getClimateMetrics(this.cityId, { limit: 50 });
      let html = `
        <div class="d-flex justify-content-between mb-2">
          <h5>Climate Metrics <span class="badge bg-secondary">${data.total}</span></h5>
          <button class="btn btn-sm btn-primary auth-only" onclick="CityDetail.openAddClimate()">+ Add</button>
        </div>
        <div class="table-responsive"><table class="table table-sm table-striped">
          <thead><tr><th>Date</th><th>Avg Temp (°C)</th><th>AQI</th><th>Humidity (%)</th><th>Precip. (mm)</th><th>Source</th><th class="auth-only">Actions</th></tr></thead>
          <tbody>`;
      for (const m of data.items) {
        html += `<tr>
          <td>${m.date}</td>
          <td>${fmtNum(m.avg_temp_c)}</td>
          <td>${fmtNum(m.aqi)}</td>
          <td>${fmtNum(m.humidity_pct)}</td>
          <td>${fmtNum(m.precipitation_mm)}</td>
          <td>${m.source ? escapeHtml(m.source) : '—'}</td>
          <td class="auth-only">
            <button class="btn btn-sm btn-outline-danger" onclick="CityDetail.deleteClimateMetric(${m.id})"><i class="bi bi-trash"></i></button>
          </td></tr>`;
      }
      html += '</tbody></table></div>';
      el.innerHTML = html;
      Auth.updateUI();
    } catch (err) { el.innerHTML = `<div class="alert alert-warning">${escapeHtml(err.message)}</div>`; }
  },

  openAddClimate() {
    $('#form-climate').reset();
    new bootstrap.Modal($('#climateModal')).show();
  },

  async handleSaveClimate(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = { date: fd.get('date') };
    ['avg_temp_c','aqi','humidity_pct','precipitation_mm'].forEach(k => {
      const v = fd.get(k);
      if (v !== '') body[k] = parseFloat(v);
    });
    const src = fd.get('source');
    if (src) body.source = src;
    try {
      await API.createClimateMetric(CityDetail.cityId, body);
      toast('Climate metric added');
      bootstrap.Modal.getInstance($('#climateModal')).hide();
      CityDetail.loadClimate();
    } catch (err) { toast(err.message, 'error'); }
  },

  async deleteClimateMetric(id) {
    if (!confirm('Delete this climate metric?')) return;
    try { await API.deleteClimateMetric(id); toast('Deleted'); this.loadClimate(); }
    catch (err) { toast(err.message, 'error'); }
  },

  /* --- Socioeconomic Metrics --- */
  async loadSocio() {
    const el = $('#detail-tab-content');
    el.innerHTML = '<div class="spinner-overlay"><div class="spinner-border text-primary"></div></div>';
    try {
      const [data, rentData] = await Promise.all([
        API.getSocioMetrics(this.cityId, { limit: 50 }),
        API.getRentMedian(this.cityId),
      ]);

      /* Rent card */
      const hasMedian = rentData.median_rent_gbp != null;
      const rentCard = `
        <div class="card mb-4">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
              <div>
                <h6 class="mb-1"><i class="bi bi-house"></i> Crowdsourced Median Rent — ${rentData.year}</h6>
                <p class="text-muted small mb-0">
                  Based on ${rentData.submission_count} user submission${rentData.submission_count !== 1 ? 's' : ''}.
                  This figure is used for the Affordability liveability score.
                </p>
              </div>
              <button class="btn btn-sm btn-outline-primary auth-only" onclick="CityDetail.openRentModal()">
                <i class="bi bi-pencil-square"></i> Report Your Rent
              </button>
            </div>
            <div class="mt-3">
              ${hasMedian
                ? `<span class="display-6 fw-bold text-success">£${Math.round(rentData.median_rent_gbp).toLocaleString()}</span>
                   <span class="text-muted ms-1">/ month</span>`
                : `<span class="text-muted fst-italic">No submissions yet — be the first to report your rent!</span>`
              }
            </div>
          </div>
        </div>`;

      /* Socioeconomic table */
      let tableHtml = `
        <div class="d-flex justify-content-between mb-2">
          <h5>Socioeconomic Metrics <span class="badge bg-secondary">${data.total}</span></h5>
          <button class="btn btn-sm btn-primary auth-only" onclick="CityDetail.openAddSocio()">+ Add</button>
        </div>
        <div class="table-responsive"><table class="table table-sm table-striped">
          <thead><tr><th>Year</th><th>Median Rent (£)</th><th>Green Space (%)</th><th>Crime Index</th><th>Avg Commute (min)</th><th>Source</th><th class="auth-only">Actions</th></tr></thead>
          <tbody>`;
      for (const m of data.items) {
        const rentDisplay = m.median_rent_gbp != null
          ? fmtNum(m.median_rent_gbp, 0)
          : '<span class="text-muted fst-italic small">crowdsourced</span>';
        tableHtml += `<tr>
          <td>${m.year}</td>
          <td>${rentDisplay}</td>
          <td>${fmtNum(m.green_space_pct)}</td>
          <td>${fmtNum(m.crime_index)}</td>
          <td>${fmtNum(m.avg_commute_min)}</td>
          <td>${m.source ? escapeHtml(m.source) : '—'}</td>
          <td class="auth-only">
            <button class="btn btn-sm btn-outline-danger" onclick="CityDetail.deleteSocioMetric(${m.id})"><i class="bi bi-trash"></i></button>
          </td></tr>`;
      }
      tableHtml += '</tbody></table></div>';

      el.innerHTML = rentCard + tableHtml;
      Auth.updateUI();
    } catch (err) { el.innerHTML = `<div class="alert alert-warning">${escapeHtml(err.message)}</div>`; }
  },

  openAddSocio() {
    $('#form-socio').reset();
    new bootstrap.Modal($('#socioModal')).show();
  },

  async handleSaveSocio(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = { year: parseInt(fd.get('year'), 10) };
    ['median_rent_gbp','green_space_pct','crime_index','avg_commute_min'].forEach(k => {
      const v = fd.get(k);
      if (v !== '') body[k] = parseFloat(v);
    });
    const src = fd.get('source');
    if (src) body.source = src;
    try {
      await API.createSocioMetric(CityDetail.cityId, body);
      toast('Socioeconomic metric added');
      bootstrap.Modal.getInstance($('#socioModal')).hide();
      CityDetail.loadSocio();
    } catch (err) { toast(err.message, 'error'); }
  },

  async deleteSocioMetric(id) {
    if (!confirm('Delete this metric?')) return;
    try { await API.deleteSocioMetric(id); toast('Deleted'); this.loadSocio(); }
    catch (err) { toast(err.message, 'error'); }
  },

  /* --- Rent submission --- */
  async openRentModal() {
    const form = $('#form-rent');
    form.reset();

    // Show current median in the modal for context
    const infoEl = $('#rent-current-median');
    try {
      const rentData = await API.getRentMedian(this.cityId);
      if (rentData.median_rent_gbp != null) {
        infoEl.textContent =
          `Current median for ${this.city.name}: £${Math.round(rentData.median_rent_gbp).toLocaleString()}/month`
          + ` (${rentData.submission_count} submission${rentData.submission_count !== 1 ? 's' : ''})`;
        infoEl.classList.remove('d-none');
      } else {
        infoEl.classList.add('d-none');
      }
    } catch { infoEl.classList.add('d-none'); }

    new bootstrap.Modal($('#rentModal')).show();
  },

  async handleSaveRent(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = { rent_amount_gbp: parseFloat(fd.get('rent_amount_gbp')) };
    try {
      await API.submitRent(CityDetail.cityId, body);
      toast('Rent submitted — thank you!');
      bootstrap.Modal.getInstance($('#rentModal')).hide();
      CityDetail.loadSocio();
    } catch (err) { toast(err.message, 'error'); }
  },

  /* --- Delete whole city --- */
  async deleteCity() {
    if (!confirm('Delete ' + this.city.name + '? This cannot be undone.')) return;
    try { await API.deleteCity(this.cityId); toast('City deleted'); App.navigate('cities'); }
    catch (err) { toast(err.message, 'error'); }
  },
};

/* ==================== ANALYTICS ==================== */
const AnalyticsPage = {
  async init() {
    /* Populate city selects */
    if (!App.cityCache.length) {
      try { const d = await API.getCities({ limit: 100 }); App.cityCache = d.items; } catch {}
    }
    _populateCityDropdowns(App.cityCache);
  },

  async handleCompare() {
    const sel = $$('#compare-cities option:checked').map(o => parseInt(o.value)).filter(Boolean);
    if (sel.length < 2) { toast('Select at least 2 cities', 'error'); return; }
    const el = $('#compare-results');
    el.innerHTML = '<div class="spinner-overlay"><div class="spinner-border text-primary"></div></div>';
    try {
      const data = await API.compareCities(sel);
      const cities = data.cities;
      let html = `<div class="table-responsive"><table class="table table-bordered">
        <thead><tr><th>City</th><th>Overall</th><th>Climate</th><th>Affordability</th><th>Safety</th><th>Environment</th></tr></thead><tbody>`;
      for (const c of cities) {
        html += `<tr>
          <td class="fw-bold">${escapeHtml(c.city_name)}</td>
          <td><span class="score-badge ${scoreCls(c.overall_score)}" style="width:40px;height:40px;font-size:.85rem">${fmtNum(c.overall_score, 0)}</span></td>
          <td>${fmtNum(c.climate_score, 0)}</td>
          <td>${fmtNum(c.affordability_score, 0)}</td>
          <td>${fmtNum(c.safety_score, 0)}</td>
          <td>${fmtNum(c.environment_score, 0)}</td>
        </tr>`;
      }
      html += '</tbody></table></div>';

      /* Bar chart */
      html += '<div class="chart-container mt-3"><canvas id="chart-compare"></canvas></div>';
      el.innerHTML = html;

      makeChart('chart-compare', {
        type: 'bar',
        data: {
          labels: cities.map(c => c.city_name),
          datasets: [
            { label: 'Overall',       data: cities.map(c => c.overall_score),       backgroundColor: 'rgba(13,110,253,.7)' },
            { label: 'Climate',       data: cities.map(c => c.climate_score),       backgroundColor: 'rgba(25,135,84,.6)' },
            { label: 'Affordability', data: cities.map(c => c.affordability_score), backgroundColor: 'rgba(255,193,7,.6)' },
            { label: 'Safety',        data: cities.map(c => c.safety_score),        backgroundColor: 'rgba(220,53,69,.6)' },
            { label: 'Environment',   data: cities.map(c => c.environment_score),   backgroundColor: 'rgba(32,201,151,.6)' },
          ],
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 100 } } },
      });
    } catch (err) { el.innerHTML = `<div class="alert alert-warning">${escapeHtml(err.message)}</div>`; }
  },

  async handleTrend() {
    const cityId = $('#trend-city').value;
    const metric = $('#trend-metric').value;
    const period = $('#trend-period').value;
    if (!cityId) { toast('Select a city', 'error'); return; }
    const el = $('#trend-results');
    el.innerHTML = '<div class="spinner-overlay"><div class="spinner-border text-primary"></div></div>';
    try {
      const data = await API.trends(cityId, { metric, period });
      let html = '<div class="chart-container"><canvas id="chart-trend"></canvas></div>';
      html += `<p class="text-muted mt-2">${data.data_points.length} data points for <strong>${escapeHtml(data.metric)}</strong> over ${escapeHtml(data.period)}</p>`;
      el.innerHTML = html;

      makeChart('chart-trend', {
        type: 'line',
        data: {
          labels: data.data_points.map(p => p.date),
          datasets: [{
            label: data.metric,
            data: data.data_points.map(p => p.value),
            borderColor: 'rgb(13,110,253)',
            backgroundColor: 'rgba(13,110,253,.1)',
            fill: true,
            tension: .3,
          }],
        },
        options: { responsive: true, maintainAspectRatio: false,
          scales: { x: { ticks: { maxTicksToShow: 15, autoSkip: true } } },
        },
      });
    } catch (err) { el.innerHTML = `<div class="alert alert-warning">${escapeHtml(err.message)}</div>`; }
  },

  async handleAnomaly() {
    const cityId = $('#anomaly-city').value;
    const threshold = $('#anomaly-threshold').value;
    if (!cityId) { toast('Select a city', 'error'); return; }
    const el = $('#anomaly-results');
    el.innerHTML = '<div class="spinner-overlay"><div class="spinner-border text-primary"></div></div>';
    try {
      const data = await API.anomalies(cityId, { threshold });
      const anomalies = data.anomalies.filter(a => a.is_anomaly);
      let html = `<p class="mb-2"><strong>${anomalies.length}</strong> anomalies detected (threshold z-score: ${data.threshold})</p>`;
      if (anomalies.length) {
        html += `<div class="table-responsive"><table class="table table-sm table-striped">
          <thead><tr><th>Date</th><th>Metric</th><th>Value</th><th>Z-Score</th></tr></thead><tbody>`;
        for (const a of anomalies) {
          html += `<tr class="table-warning"><td>${a.date}</td><td>${escapeHtml(a.metric)}</td><td>${fmtNum(a.value)}</td><td>${fmtNum(a.z_score, 2)}</td></tr>`;
        }
        html += '</tbody></table></div>';
      } else {
        html += '<p class="text-muted">No anomalies found at this threshold.</p>';
      }
      el.innerHTML = html;
    } catch (err) { el.innerHTML = `<div class="alert alert-warning">${escapeHtml(err.message)}</div>`; }
  },
};

/* ==================== QUERY / NARRATIVE ==================== */
const QueryPage = {
  async init() {
    if (!App.cityCache.length) {
      try { const d = await API.getCities({ limit: 100 }); App.cityCache = d.items; } catch {}
    }
    _populateCityDropdowns(App.cityCache);
  },

  async handleNarrative() {
    const cityId = $('#narrative-city').value;
    if (!cityId) { toast('Select a city', 'error'); return; }
    const el = $('#narrative-result');
    el.innerHTML = '<div class="spinner-overlay"><div class="spinner-border text-primary"></div></div>';
    try {
      const data = await API.narrative(cityId);
      el.innerHTML = `<div class="card"><div class="card-body">
        <h6>${escapeHtml(data.city_name)}</h6>
        <p class="mb-0" style="white-space:pre-wrap">${escapeHtml(data.narrative)}</p>
      </div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-warning">${escapeHtml(err.message)}</div>`; }
  },
};

/* ==================== Shared helpers ==================== */
function _populateCityDropdowns(cities) {
  const selectors = ['#compare-cities', '#trend-city', '#anomaly-city', '#narrative-city'];
  for (const sel of selectors) {
    const el = $(sel);
    if (!el) continue;
    const current = el.value;
    const isMultiple = el.multiple;
    el.innerHTML = isMultiple ? '' : '<option value="">— Select city —</option>';
    for (const c of cities) {
      el.innerHTML += `<option value="${c.id}">${escapeHtml(c.name)}</option>`;
    }
    if (current) el.value = current;
  }
}

/* ==================== Boot ==================== */
document.addEventListener('DOMContentLoaded', () => App.init());
