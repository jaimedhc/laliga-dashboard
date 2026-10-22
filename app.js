/* Dashboard LaLiga 2026-27. build.py genera los datos en window.DATA; este archivo los pinta. */
"use strict";
(function () {
const D = window.DATA;
const T = D.teams, NM = D.names, SH = D.short, NT = T.length;

/* ---------------------------------------------------------------- formato */
const NF = d => new Intl.NumberFormat('es-ES', {minimumFractionDigits: d, maximumFractionDigits: d});
const N0 = NF(0), N1 = NF(1), N2 = NF(2);
const ok = v => v != null && isFinite(v);
const f0 = v => ok(v) ? N0.format(v) : '–';
const f1 = v => ok(v) ? N1.format(v) : '–';
const f2 = v => ok(v) ? N2.format(v) : '–';
const pc = p => !ok(p) ? '–' : p < 0.005 ? '<1 %' : p > 0.995 ? '>99 %' : Math.round(p * 100) + ' %';
const pf = p => ok(p) ? Math.round(p * 100) + ' %' : '–';  // frecuencias observadas: aquí 100 % es exacto
const sgn = (v, f) => !ok(v) ? '–' : (f(Math.abs(v)) === f(0) ? '' : v > 0 ? '+' : '−') + f(Math.abs(v));
const sg0 = v => sgn(v, f0), sg1 = v => sgn(v, f1), sg2 = v => sgn(v, f2);
const ppt = v => sgn(v * 100, f0) + ' pp';
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const DOW = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];
const fd = iso => iso ? iso.slice(8, 10) + '/' + iso.slice(5, 7) : '–';
const fdl = iso => iso ? DOW[new Date(iso + 'T12:00:00Z').getUTCDay()] + ' ' + fd(iso) : '–';
const nm = i => esc(NM[i]);
const $ = id => document.getElementById(id);
const mean = a => a.length ? a.reduce((s, x) => s + x, 0) / a.length : null;
const vr = a => { if (a.length < 2) return null; const m = mean(a); return a.reduce((s, x) => s + (x - m) ** 2, 0) / (a.length - 1); };
const num = a => a.filter(ok);
const card = (title, body, cls = '') => `<section class="card ${cls}">${title ? `<h2>${title}</h2>` : ''}${body}</section>`;
const note = t => `<p class="note">${t}</p>`;
const tbl = (head, rows, cls = '') => `<div class="sc"><table class="${cls}"><thead><tr>${head.map(h => Array.isArray(h) ? `<th class="${h[1]}">${h[0]}</th>` : `<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
const LEVELS = {clear: 'Clara', maybe: 'Posible', noise: 'Ruido'};
const level = (d, e) => !ok(d) || !(e > 0) ? 'noise' : Math.abs(d) > 2 * e ? 'clear' : Math.abs(d) > e ? 'maybe' : 'noise';
const chip = lv => `<span class="chip ${lv}">${LEVELS[lv]}</span>`;

/* ---------------------------------------------------------------- datos */
const VARS = [
  {k: 'g', n: 'Goles', low: 'goles', fl: 'Goles a favor', al: 'Goles en contra'},
  {k: 'g1', n: 'Goles 1ª parte', low: 'goles en la 1ª parte', fl: 'Goles 1ª parte a favor', al: 'Goles 1ª parte en contra'},
  {k: 'g2', n: 'Goles 2ª parte', low: 'goles en la 2ª parte', fl: 'Goles 2ª parte a favor', al: 'Goles 2ª parte en contra'},
  {k: 'xg', n: 'xG', low: 'xG', fl: 'xG a favor', al: 'xG en contra', cont: true},
  {k: 's', n: 'Tiros', low: 'tiros', fl: 'Tiros', al: 'Tiros del rival'},
  {k: 'st', n: 'Tiros a puerta', low: 'tiros a puerta', fl: 'Tiros a puerta', al: 'Tiros a puerta del rival'},
  {k: 'c', n: 'Córners', low: 'córners', fl: 'Córners', al: 'Córners del rival'},
  {k: 'f', n: 'Faltas', low: 'faltas', fl: 'Faltas cometidas', al: 'Faltas recibidas'},
  {k: 'y', n: 'Amarillas', low: 'amarillas', fl: 'Amarillas', al: 'Amarillas del rival'},
  {k: 'r', n: 'Rojas', low: 'rojas', fl: 'Rojas', al: 'Rojas del rival'},
];
const VK = Object.fromEntries(VARS.map(v => [v.k, v]));
const SK = ['g1', 'xg', 's', 'st', 'c', 'f', 'y', 'r'], EK = ['g', 'g1', 'xg', 's', 'st', 'c', 'f', 'y', 'r'];
const M = D.M.map((r, idx) => {
  const m = {idx, d: r[0], tm: r[1], j: r[2], h: r[3], a: r[4], hg: r[5], ag: r[6], v: {g: [r[5], r[6]]}, e: {},
    odds: ok(r[23]) ? r.slice(23, 26) : null, ou: ok(r[26]) ? r.slice(26, 28) : null};
  SK.forEach((k, q) => { const x = r[7 + 2 * q], y = r[8 + 2 * q]; m.v[k] = ok(x) && ok(y) ? [x, y] : null; });
  m.v.g2 = m.v.g1 ? [m.hg - m.v.g1[0], m.ag - m.v.g1[1]] : null;
  const e = D.E[idx] || [];
  EK.forEach((k, q) => { const x = e[2 * q], y = e[2 * q + 1]; m.e[k] = ok(x) && ok(y) ? [x, y] : null; });
  m.e.g2 = m.e.g && m.e.g1 ? [m.e.g[0] - m.e.g1[0], m.e.g[1] - m.e.g1[1]] : null;
  return m;
});
const G = T.map(() => []);
M.forEach(m => [0, 1].forEach(s => {
  const t = s ? m.a : m.h, o = s ? m.h : m.a, g = {m, home: !s, t, o, f: {}, a: {}, ef: {}, ea: {}};
  VARS.forEach(({k}) => {
    const v = m.v[k], e = m.e[k];
    g.f[k] = v ? v[s] : null; g.a[k] = v ? v[1 - s] : null;
    g.ef[k] = e ? e[s] : null; g.ea[k] = e ? e[1 - s] : null;
  });
  g.gf = g.f.g; g.ga = g.a.g; g.res = g.gf > g.ga ? 'W' : g.gf < g.ga ? 'L' : 'D';
  G[t].push(g);
}));
const ST = {};  // media de la liga y variación de un partido a otro dentro de cada equipo
VARS.forEach(({k}) => {
  const per = G.map(gs => num(gs.map(g => g.f[k])));
  ST[k] = {mu: mean(per.flat()), w: mean(per.filter(a => a.length > 1).map(vr)) || 0};
});
const PTSV = vr(G.flat().map(g => g.res === 'W' ? 3 : g.res === 'D' ? 1 : 0)) || 1.5;  // variación de los puntos por partido en la liga
const TB = D.table, ROW = {};
TB.forEach(r => { ROW[r.t] = r; });
const POS = T.map((_, i) => ROW[i].pos);
const FX = D.fx.map(r => ({j: r[0], d: r[1], tm: r[2], h: r[3], a: r[4], src: r[5],
  odds: ok(r[6]) ? r.slice(6, 9) : null, ou: ok(r[9]) ? r.slice(9, 11) : null, ah: ok(r[11]) && ok(r[12]) ? r.slice(11, 14) : null, past: r[1] < D.meta.today}));
const implied = o => { if (!o) return null; const inv = o.map(x => 1 / x), s = inv[0] + inv[1] + inv[2]; return inv.map(x => x / s); };
const implied2 = o => { if (!o) return null; const a = 1 / o[0], b = 1 / o[1]; return a / (a + b); };

/* ---------------------------------------------------------------- modelos (idénticos a model.py) */
const GM = D.gm, SM = D.sm;
const GH = [[-2.0201828704560856, 0.011257411327720691], [-0.9585724646138185, 0.22207592200561265], [0, 0.5333333333333333],
  [0.9585724646138185, 0.22207592200561265], [2.0201828704560856, 0.011257411327720691]];
const lin = (p, i, j, home) => [p.mu + (home ? p.eta : 0) + p.a[i] - p.d[j], (home ? p.vh0 : p.va0) + p.va[i] + p.vd[j]];
function pmf(l, K) { const o = [Math.exp(-l)]; for (let k = 1; k <= K; k++) o.push(o[k - 1] * l / k); return o; }
function scoreMatrix(i, j, K = 10) {
  const [lh, vh] = lin(GM, i, j, 1), [la, va] = lin(GM, j, i, 0), rho = GM.rho || 0;
  const sh = Math.sqrt(2 * vh), sa = Math.sqrt(2 * va);
  const X = Array.from({length: K + 1}, () => new Array(K + 1).fill(0));
  for (const [xi, wi] of GH) {
    const l1 = Math.exp(lh + sh * xi), p1 = pmf(l1, K);
    for (const [xj, wj] of GH) {
      const l2 = Math.exp(la + sa * xj), p2 = pmf(l2, K), ww = wi * wj;
      for (let x = 0; x <= K; x++) { const c = ww * p1[x], row = X[x]; for (let y = 0; y <= K; y++) row[y] += c * p2[y]; }
      if (rho) {
        X[0][0] += ww * p1[0] * p2[0] * (Math.max(1 - l1 * l2 * rho, 0) - 1);
        X[0][1] += ww * p1[0] * p2[1] * (Math.max(1 + l1 * rho, 0) - 1);
        X[1][0] += ww * p1[1] * p2[0] * (Math.max(1 + l2 * rho, 0) - 1);
        X[1][1] += ww * p1[1] * p2[1] * (Math.max(1 - rho, 0) - 1);
      }
    }
  }
  let s = 0; X.forEach(r => r.forEach(v => { s += v; }));
  return X.map(r => r.map(v => v / s));
}
function summarize(X) {
  const K = X.length - 1; let pH = 0, pD = 0, pA = 0, eh = 0, ea = 0, bb = 0;
  const tot = new Array(2 * K + 1).fill(0), hx = new Array(K + 1).fill(0), ay = new Array(K + 1).fill(0), cells = [];
  for (let x = 0; x <= K; x++) for (let y = 0; y <= K; y++) {
    const q = X[x][y];
    if (x > y) pH += q; else if (x === y) pD += q; else pA += q;
    eh += x * q; ea += y * q; tot[x + y] += q; hx[x] += q; ay[y] += q; if (x && y) bb += q; cells.push([q, x, y]);
  }
  cells.sort((u, v) => v[0] - u[0]);
  const P = [pH, pD, pA], fav = P.indexOf(Math.max(pH, pD, pA));
  const fs = cells.find(c => (c[1] > c[2] ? 0 : c[1] === c[2] ? 1 : 2) === fav);
  const varOf = (d, m) => d.reduce((s, v, k) => s + v * (k - m) ** 2, 0);
  const dd = new Map(); for (let x = 0; x <= K; x++) for (let y = 0; y <= K; y++) dd.set(x - y, (dd.get(x - y) || 0) + X[x][y]);
  return {p: P, e: [eh, ea], V: [varOf(hx, eh), varOf(ay, ea), varOf(tot, eh + ea)], bb, tot, hx, ay, dd,
    ou: [0.5, 1.5, 2.5, 3.5, 4.5].map(L => over(tot, L)), top: cells.slice(0, 6).map(c => [c[1], c[2], c[0]]), fs: [fs[1], fs[2], fs[0]]};
}
const over = (dist, L) => dist.reduce((s, v, k) => s + (k > L ? v : 0), 0);
const PCACHE = new Map();
function predict(i, j) { const k = i * 64 + j; if (!PCACHE.has(k)) PCACHE.set(k, summarize(scoreMatrix(i, j))); return PCACHE.get(k); }
/* Media esperada (m), varianza en un partido (V) y error de la media (e) de la estadística k del equipo i contra j. */
function sPred(k, i, j, home) {
  if (k === 'g') {
    const pr = home ? predict(i, j) : predict(j, i), s = home ? 0 : 1, v = lin(GM, i, j, home)[1], m = pr.e[s];
    return {m, V: pr.V[s], e: m * Math.sqrt(Math.exp(v) - 1)};
  }
  if (k === 'g2') {
    const g = sPred('g', i, j, home), g1 = sPred('g1', i, j, home);
    if (!g1) return null;
    const m = Math.max(g.m - g1.m, 0.01);
    return {m, V: Math.max(g.V - g1.V, m), e: m * g.e / g.m};
  }
  const p = SM[k]; if (!p) return null;
  const [l, v] = lin(p, i, j, home), m = Math.exp(l + v / 2), e2 = m * m * (Math.exp(v) - 1);
  return {m, V: p.phi * m + e2, e: Math.sqrt(e2)};
}
/* Valor esperado frente a un rival medio en campo neutral (para comparar equipos). */
function neutral(k, i, side) {
  if (k === 'g2') { const g = neutral('g', i, side), g1 = neutral('g1', i, side); return ok(g) && ok(g1) ? g - g1 : null; }
  const p = k === 'g' ? GM : SM[k]; if (!p) return null;
  return Math.exp(p.mu + p.eta / 2 + (side === 'f' ? p.a[i] : -p.d[i]));
}
function Phi(z) {
  const t = 1 / (1 + 0.2316419 * Math.abs(z)), d = 0.3989422804014327 * Math.exp(-z * z / 2);
  const p = d * t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
  return z > 0 ? 1 - p : p;
}
/* Probabilidad de superar la línea L (p. ej. 9,5) con media m y varianza V. */
function pOver(x, L, cont) {
  const m = x.m, V = x.V;
  if (!(m > 0)) return 0;
  if (cont) { const s2 = Math.log(1 + V / (m * m)), mu = Math.log(m) - s2 / 2; return L <= 0 ? 1 : 1 - Phi((Math.log(L) - mu) / Math.sqrt(s2)); }
  const K = Math.floor(L);
  if (K < 0) return 1;
  if (V > m * 1.02) {
    const r = m * m / (V - m), q = m / (r + m); let pk = Math.pow(1 - q, r), c = pk;
    for (let k = 1; k <= K; k++) { pk *= (k - 1 + r) / k * q; c += pk; }
    return Math.max(0, 1 - c);
  }
  if (V >= m * 0.98) { let pk = Math.exp(-m), c = pk; for (let k = 1; k <= K; k++) { pk *= m / k; c += pk; } return Math.max(0, 1 - c); }
  return 1 - Phi((K + 0.5 - m) / Math.sqrt(V));
}
const perMatchSd = (k, m) => Math.sqrt(Math.max(m, 0.05) * ((k === 'g' || k === 'g1' || k === 'g2') ? 1 : (SM[k] ? SM[k].phi : 1)));

/* ---------------------------------------------------------------- rivales parecidos */
const CX = k => k === 'g' || k === 'g2' ? GM.cx[k] : SM[k] || null;
const near = (o, ex, win) => T.map((_, i) => i).filter(i => i !== o && i !== ex && Math.abs(POS[i] - POS[o]) <= win);
/* Cómo rinde t contra los equipos cercanos en la tabla a o, comparado con lo que esperaba el modelo. */
function cross(t, o, win) {
  const set = near(o, t, win), S = new Set(set), gs = G[t].filter(g => S.has(g.o)), rows = {};
  VARS.forEach(({k}) => {
    const c = CX(k); if (!c) return;
    const one = (vals, tau) => {
      const n = vals.length; if (!n) return {n: 0, adj: 0, av: 0};
      const r = mean(vals), e = Math.sqrt(c.s2 / n), w = tau > 0 ? tau / (tau + c.s2 / n) : 0;
      return {n, r, e, w, adj: w * r, av: w * c.s2 / n};
    };
    const gf = gs.filter(g => ok(g.f[k]) && ok(g.ef[k])), ga = gs.filter(g => ok(g.a[k]) && ok(g.ea[k]));
    rows[k] = {f: one(gf.map(g => g.f[k] - g.ef[k]), c.tf), a: one(ga.map(g => g.a[k] - g.ea[k]), c.ta),
      obs: mean(gf.map(g => g.f[k])), exp: mean(gf.map(g => g.ef[k])), obsA: mean(ga.map(g => g.a[k])), expA: mean(ga.map(g => g.ea[k]))};
  });
  const lo = Math.max(1, POS[o] - win), hi = Math.min(NT, POS[o] + win);
  return {set, gs, rows, lo, hi};
}

/* ---------------------------------------------------------------- vista: equipos */
const ST_ = {sel: TB[0].t, rk: 'g:f', mode: 'opt', win: 2, useX: true, fx: null, jsel: 'next', hreal: false};
const zone = p => p <= 4 ? 'ucl' : p <= 6 ? 'uel' : p > NT - 3 ? 'rel' : '';
function renderTable() {
  $('tabla').innerHTML = tbl(['#', 'Equipo', '<abbr title="Partidos jugados">PJ</abbr>', '<abbr title="Diferencia de goles">DG</abbr>', 'Pts',
    '<abbr title="Puntos esperados según el xG de cada partido">xPts</abbr>'],
    TB.map(r => `<tr class="${zone(r.pos)} ${r.t === ST_.sel ? 'on' : ''}"><td>${r.pos}</td><td><button class="lk" data-team="${r.t}">${nm(r.t)}</button></td>` +
      `<td>${r.pj}</td><td>${sg0(r.gf - r.ga)}</td><td><b>${r.pts}</b></td><td>${r.xn ? f1(r.xpts) : '–'}</td></tr>`), 'lg') +
    `<p class="legend"><span class="sw ucl"></span>Champions <span class="sw uel"></span>Europa <span class="sw rel"></span>Descenso</p>`;
}
const RKS = VARS.flatMap(v => [[v.k + ':f', v.fl], [v.k + ':a', v.al]]);
function renderRank() {
  const [k, side] = ST_.rk.split(':'), mu = ST[k].mu;
  const rows = T.map((_, i) => {
    const vals = num(G[i].map(g => side === 'f' ? g.f[k] : g.a[k])), n = vals.length;
    return {i, v: mean(vals), n, e: n ? Math.sqrt(ST[k].w / n) : null};
  }).filter(r => r.n).sort((x, y) => y.v - x.v);
  const mx = Math.max(...rows.map(r => r.v)) || 1;
  $('rank').innerHTML = `<p class="note">Media de la liga: ${f1(mu)} por partido. En negrita, los equipos que se alejan de la media más de dos errores.</p>` +
    rows.map((r, p) => `<div class="rk ${r.i === ST_.sel ? 'on' : ''}"><span>${p + 1}. ${nm(r.i)}</span><span class="bar"><i style="width:${(r.v / mx * 100).toFixed(1)}%"></i></span>` +
      `<span class="${level(r.v - mu, r.e) === 'clear' ? 'b' : ''}">${f1(r.v)} <small>±${f1(r.e)}</small></span></div>`).join('');
}
function nextFixture(i) { return FX.filter(f => (f.h === i || f.a === i)).sort((x, y) => (x.past - y.past) || (x.d < y.d ? -1 : 1)).find(f => !f.past) || null; }
function goalsChart(gs) {
  const n = gs.length, W = 640, H = 200, B = 34, top = 18, mx = Math.max(3, ...gs.flatMap(g => [g.gf, g.ga])), bw = (W - 20) / Math.max(n, 1);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Goles a favor y en contra en cada partido">`;
  for (let v = 0; v <= mx; v++) { const y = H - B - (H - B - top) * v / mx; s += `<line class="grid" x1="20" x2="${W}" y1="${y}" y2="${y}"/><text class="ax" x="14" y="${y + 4}" text-anchor="end">${v}</text>`; }
  gs.forEach((g, i) => {
    const x0 = 20 + i * bw, b = Math.min(bw * 0.32, 26), h1 = (H - B - top) * g.gf / mx, h2 = (H - B - top) * g.ga / mx, cx = x0 + bw / 2;
    const t = `${fd(g.m.d)} ${g.home ? 'vs' : 'en'} ${NM[g.o]}: ${g.gf}-${g.ga}`;
    s += `<g><title>${esc(t)}</title><rect class="s1" x="${cx - b - 1}" y="${H - B - h1}" width="${b}" height="${Math.max(h1, 0.01)}" rx="2"/>` +
      `<rect class="s2" x="${cx + 1}" y="${H - B - h2}" width="${b}" height="${Math.max(h2, 0.01)}" rx="2"/>` +
      `<text class="ax" x="${cx}" y="${H - B + 14}" text-anchor="middle">${SH[g.o]}</text><text class="ax" x="${cx}" y="${H - B + 27}" text-anchor="middle">${g.home ? 'C' : 'F'}</text></g>`;
  });
  return s + '</svg>';
}
function renderTeam() {
  const i = ST_.sel, gs = G[i], r = ROW[i], n = gs.length;
  if (!n) { $('team').innerHTML = card(nm(i), note('Aún no ha jugado ningún partido.')); return; }
  const H = gs.filter(g => g.home), A = gs.filter(g => !g.home);
  const sum = (k, side = 'f') => num(gs.map(g => g[side][k])).reduce((s, x) => s + x, 0);
  const cnt = f => gs.filter(f).length;
  const nx = nextFixture(i);
  const kp = [['Posición', `${r.pos}º · ${r.pts} pts`], ['Balance', `${r.w}G ${r.d}E ${r.l}P`], ['Goles', `${r.gf} a favor · ${r.ga} en contra`],
    ['xG', `${f1(sum('xg'))} a favor · ${f1(sum('xg', 'a'))} en contra`], ['Tarjetas', `${sum('y')} amarillas · ${sum('r')} rojas`]];
  const pts = gs.map(g => g.res === 'W' ? 3 : g.res === 'D' ? 1 : 0), shots = sum('s') || 1;
  const E = (x, m) => { const q = (x + 2) / (m + 4); return '±' + Math.round(Math.sqrt(q * (1 - q) / (m + 4)) * 100) + ' pp'; };  // Agresti-Coull: no da 0 con 9 de 9
  const c0 = cnt(g => g.ga === 0), c1 = cnt(g => g.gf === 0), c2 = cnt(g => g.gf > 0 && g.ga > 0), c3 = cnt(g => g.gf + g.ga > 2);
  const mk = gs.filter(g => g.m.odds), exp = mk.reduce((s, g) => { const q = implied(g.m.odds); return s + 3 * q[g.home ? 0 : 2] + q[1]; }, 0);
  const ptsM = mk.reduce((s, g) => s + (g.res === 'W' ? 3 : g.res === 'D' ? 1 : 0), 0);
  const gx = gs.filter(g => ok(g.f.xg)), gmx = gx.reduce((s, g) => s + g.gf - g.f.xg, 0);
  const adv = [['Puntos por partido', f2(r.pts / n), '±' + f2(Math.sqrt(PTSV / n))], ['Victorias', pf(r.w / n), E(r.w, n)],
    ['Portería a cero', `${c0} de ${n}`, ''], ['Sin marcar', `${c1} de ${n}`, ''], ['Ambos marcan', pf(c2 / n), E(c2, n)],
    ['Más de 2,5 goles', pf(c3 / n), E(c3, n)], ['Tiros a puerta / tiros', pf(sum('st') / shots), E(sum('st'), shots)],
    ['Goles por tiro', pf(sum('g') / shots), E(sum('g'), shots)],
    ['Goles menos xG', sg1(gmx), gx.length > 1 ? '±' + f1(Math.sqrt(vr(gx.map(g => g.gf - g.f.xg)) * gx.length)) : ''],
    ['Puntos frente a las cuotas', mk.length ? `${ptsM} reales · ${f1(exp)} esperados` : '–', '']];
  const form = gs.slice(-10).map(g => `<i class="fm ${g.res}" title="${esc(`${fd(g.m.d)} ${g.home ? 'vs' : 'en'} ${NM[g.o]} ${g.gf}-${g.ga}`)}">${{W: 'G', D: 'E', L: 'P'}[g.res]}</i>`).join('');
  const varRows = VARS.flatMap(v => ['f', 'a'].map(side => {
    const vals = num(gs.map(g => g[side][v.k])), m = mean(vals), sd = Math.sqrt(vr(vals) || 0), e = vals.length ? Math.sqrt(ST[v.k].w / vals.length) : null;
    const d = ok(m) ? m - ST[v.k].mu : null, lv = level(d, e);
    return `<tr><td>${side === 'f' ? v.fl : v.al}</td><td>${f1(m)}</td><td>${f1(sd)}</td><td>±${f1(e)}</td><td>${sg1(d)}</td><td>${chip(lv)}</td><td>${f1(neutral(v.k, i, side))}</td></tr>`;
  }));
  const avg = (arr, k, side = 'f') => mean(num(arr.map(g => g[side][k])));
  const avgRows = VARS.map(v => `<tr><td>${v.n}</td><td>${f1(avg(gs, v.k))}</td><td>${f1(avg(gs, v.k, 'a'))}</td><td>${f1(avg(H, v.k))}</td><td>${f1(avg(A, v.k))}</td><td>${f1(avg(H, v.k, 'a'))}</td><td>${f1(avg(A, v.k, 'a'))}</td></tr>`);
  const cell = (g, k) => {
    const f = g.f[k], a = g.a[k]; if (!ok(f) || !ok(a)) return '<td>–</td>';
    const show = x => k === 'xg' ? f1(x) : x;
    if (!ok(g.ef[k])) return `<td>${show(f)}-${show(a)}</td>`;
    const d1 = f - g.ef[k], d2 = a - g.ea[k], z1 = d1 / perMatchSd(k, g.ef[k]), z2 = d2 / perMatchSd(k, g.ea[k]);
    return `<td>${show(f)}-${show(a)}<br><span class="dv ${Math.max(Math.abs(z1), Math.abs(z2)) >= 2 ? 'b' : ''}" title="${esc(`${sg1(z1)} / ${sg1(z2)} desviaciones`)}">${sg1(d1)} / ${sg1(d2)}</span></td>`;
  };
  const mrows = gs.slice().reverse().map(g => {
    const q = implied(g.m.odds);
    return `<tr><td>${fd(g.m.d)}</td><td>${g.m.j || ''}</td><td class="l">${g.home ? 'Casa' : 'Fuera'}</td><td class="l">${nm(g.o)}</td><td><b>${g.gf}-${g.ga}</b>${g.m.v.g1 ? ` <span class="mu">(${g.f.g1}-${g.a.g1})</span>` : ''}</td>` +
      ['xg', 's', 'st', 'c', 'f', 'y', 'r'].map(k => cell(g, k)).join('') + `<td>${q ? pc(q[g.home ? 0 : 2]) : '–'}</td></tr>`;
  });
  $('team').innerHTML = `<div class="th"><h2 class="tn">${nm(i)}</h2>${nx ? `<button class="go" data-fx="${nx.h}-${nx.a}">Analizar ${nm(nx.h)} – ${nm(nx.a)} · ${fdl(nx.d)} →</button>` : ''}</div>
    <div class="tiles">${kp.map(k => `<div class="tile"><span>${k[0]}</span><b>${k[1]}</b></div>`).join('')}</div>
    ${card('Forma (últimos 10)', `<div class="form">${form}</div>`)}
    ${card('Goles por partido', `<div class="sc">${goalsChart(gs)}</div><p class="legend"><span class="sw s1"></span>A favor <span class="sw s2"></span>En contra · C = en casa, F = fuera</p>`)}
    ${card('Resumen avanzado', `<div class="tiles sm">${adv.map(k => `<div class="tile"><span>${k[0]}</span><b>${k[1]}</b><small>${k[2]}</small></div>`).join('')}</div>`)}
    ${card('Variación y señal de cada estadística', tbl(['', 'Media', 'Desv. típica', 'Error de la media', 'Frente a la liga', 'Señal', 'Esperable ajustado'], varRows, 'num') +
      note('<b>Desv. típica</b>: cuánto varía de un partido a otro. <b>Error de la media</b>: cuánto podría moverse su media solo por azar. <b>Señal</b>: clara si la diferencia con la liga supera dos errores, posible si supera uno (siendo optimistas) y ruido si no. <b>Esperable ajustado</b>: lo que el modelo espera contra un rival medio en campo neutral, ya corregido por la dificultad de los rivales y acercado a la media según lo que demuestran los datos.'))}
    ${card('Promedios por partido', tbl(['', 'Equipo', 'Rival', 'Equipo en casa', 'Equipo fuera', 'Rival cuando juega en casa', 'Rival cuando juega fuera'], avgRows, 'num'))}
    ${card('Partidos', tbl(['Fecha', 'J', ['Lugar', 'l'], ['Rival', 'l'], 'Resultado', 'xG', 'Tiros', 'A puerta', 'Córners', 'Faltas', 'Amarillas', 'Rojas', 'Gana según cuotas'], mrows, 'num mt') +
      note('Cada celda muestra el equipo y el rival. Debajo, la diferencia con lo que esperaba el modelo para ese partido (equipo / rival). En negrita, desviaciones de dos o más (al pasar el cursor se ven en desviaciones típicas).'))}
    ${squadHtml(i)}`;
}
const AL = {Alaves: ['alaves'], 'Ath Bilbao': ['athletic'], 'Ath Madrid': ['atletico'], Betis: ['betis'], Celta: ['celta'], Espanol: ['espanyol'],
  'La Coruna': ['coruna', 'deportivo'], Santander: ['racing'], Sociedad: ['sociedad'], Vallecano: ['vallecano', 'rayo'], 'Real Madrid': ['real madrid']};
const nz = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
let ps = 'min';
function squadHtml(i) {
  const keys = AL[T[i]] || [nz(T[i])], k = Object.keys(D.pl || {}).find(n => keys.some(a => nz(n).includes(a))), sq = k ? D.pl[k] : null;
  if (!sq || !sq.length) return '';
  const POSN = {Goalkeeper: 'POR', Defender: 'DEF', Midfielder: 'MED', Attacker: 'DEL'};
  const a = sq.slice().sort((x, y) => ps === 'n' ? x.n.localeCompare(y.n, 'es') : (y[ps] - x[ps]) || (y.min - x.min));
  const H = [['n', 'Jugador'], ['pj', 'PJ'], ['min', 'Min'], ['g', 'Goles'], ['a', 'Asist.'], ['y', 'Amarillas'], ['r', 'Rojas']];
  return card('Plantilla', tbl(H.map(h => `<button class="lk" data-ps="${h[0]}">${h[1]}${ps === h[0] ? ' ↓' : ''}</button>`),
    a.map(p => `<tr><td>${esc(p.n)} <span class="mu">${POSN[p.pos] || ''}</span></td><td>${p.pj}</td><td>${p.min}</td><td>${p.g}</td><td>${p.a}</td><td>${p.y}</td><td>${p.r}</td></tr>`), 'num'));
}
function renderEquipos() { renderTable(); renderRank(); renderTeam(); }

/* ---------------------------------------------------------------- vista: análisis de partido */
const MODES = {opt: {z: 1, thr: 0.6, name: 'Optimista', desc: '±1 error · umbrales con al menos 60 %'},
  pru: {z: 2, thr: 0.7, name: 'Prudente', desc: '±2 errores · umbrales con al menos 70 %'}};
const fxKey = f => f.h + '-' + f.a;
const byDate = (x, y) => (x.d < y.d ? -1 : x.d > y.d ? 1 : (x.tm || '') < (y.tm || '') ? -1 : 1);
const upcoming = () => FX.filter(f => !f.past).sort(byDate);
const statusOf = f => f.past ? '<span class="chip warn">Fecha pasada sin resultado: aplazado o pendiente de datos</span>'
  : f.src === 2 ? '<span class="chip">Fecha y hora de football-data</span>' : f.src === 1 ? '<span class="chip">Fecha corregida a mano</span>' : '<span class="chip">Fecha del calendario RFEF</span>';
function fixtureSelect(cur) {
  const groups = [], seen = {};
  upcoming().forEach(f => { const g = 'Jornada ' + f.j; if (!seen[g]) { seen[g] = []; groups.push([g, seen[g]]); } seen[g].push(f); });
  const past = FX.filter(f => f.past);
  if (past.length) groups.push(['Fecha pasada sin resultado', past]);
  return `<select id="fx-sel" aria-label="Partido">${groups.map(([g, fs]) => `<optgroup label="${g}">${fs.map(f =>
    `<option value="${fxKey(f)}" ${fxKey(f) === cur ? 'selected' : ''}>${f.past ? 'J' + f.j + ' · ' : fdl(f.d) + (f.tm ? ' ' + f.tm : '') + ' · '}${nm(f.h)} – ${nm(f.a)}</option>`).join('')}</optgroup>`).join('')}</select>`;
}
const probBar = (p, label) => `<div class="pb"><span class="pbl">${label}</span><div class="pbar">${p.map((x, k) =>
  `<i class="q${k}" style="width:${(x * 100).toFixed(2)}%" title="${['Local', 'Empate', 'Visitante'][k]}: ${pc(x)}">${x >= 0.14 ? pc(x) : ''}</i>`).join('')}</div></div>`;
function estimates(h, a, win, useX) {
  const pr = predict(h, a), cH = cross(h, a, win), cA = cross(a, h, win), est = {};
  VARS.forEach(({k}) => {
    const H = sPred(k, h, a, 1), A = sPred(k, a, h, 0), rH = cH.rows[k], rA = cA.rows[k];
    if (!H || !A) return;
    const on = useX && rH && rA;
    const addH = on ? rH.f.adj + rA.a.adj : 0, avH = on ? rH.f.av + rA.a.av : 0;
    const addA = on ? rA.f.adj + rH.a.adj : 0, avA = on ? rA.f.av + rH.a.av : 0;
    const Hm = Math.max(H.m + addH, 0.001), Am = Math.max(A.m + addA, 0.001), He = Math.sqrt(H.e ** 2 + avH), Ae = Math.sqrt(A.e ** 2 + avA);
    const p = SM[k] || {rr: 0, phi: 1};
    const TV = k === 'g' ? pr.V[2] + avH + avA : Math.max(H.V + avH + A.V + avA + 2 * (p.rr || 0) * (p.phi || 1) * Math.sqrt(Hm * Am), 1e-6);
    est[k] = {H: {m: Hm, e: He, V: H.V + avH}, A: {m: Am, e: Ae, V: A.V + avA}, T: {m: Hm + Am, e: Math.hypot(He, Ae), V: TV},
      adj: Math.abs(addH) + Math.abs(addA), w: on ? Math.max(rH.f.w || 0, rA.a.w || 0, rA.f.w || 0, rH.a.w || 0) : 0};
  });
  return {pr, cH, cA, est};
}
function lineP(X, k, side, L) {
  const x = X.est[k][side];
  if (k === 'g' && X.est.g.adj < 0.02) return over(side === 'H' ? X.pr.hx : side === 'A' ? X.pr.ay : X.pr.tot, L);
  return pOver(x, L, VK[k].cont);
}
function umbral(X, k, side, thr) {
  const x = X.est[k][side], sd = Math.sqrt(x.V), lo = Math.max(0.5, Math.floor(x.m - 3 * sd) + 0.5), hi = Math.floor(x.m + 3 * sd) + 0.5;
  let up = null, dn = null;
  for (let L = lo; L <= hi; L += 1) { const p = lineP(X, k, side, L); if (p >= thr) up = {L, p}; if (!dn && 1 - p >= thr) dn = {L, p: 1 - p}; }
  return {up, dn};
}
const lineTxt = L => f1(L).replace(',0', '');
/* Media según solo los rivales parecidos: lo que hizo t contra los parecidos a o y lo que concedió o contra los parecidos a t. */
function crossMean(X, k, side) {
  const one = (cT, cO) => {
    const a = cT.rows[k], b = cO.rows[k]; if (!a || !b) return null;
    const n1 = a.f.n, n2 = b.a.n; if (!n1 && !n2) return null;
    return {m: ((n1 ? a.obs * n1 : 0) + (n2 ? b.obsA * n2 : 0)) / (n1 + n2), n: n1 + n2};
  };
  const H = one(X.cH, X.cA), A = one(X.cA, X.cH);
  if (side === 'H') return H; if (side === 'A') return A;
  return H && A ? {m: H.m + A.m, n: Math.min(H.n, A.n)} : null;
}
/* Probabilidad de superar L según el modelo y según los rivales parecidos; la prudente es la menor de las dos. */
function bothOver(X, k, side, L) {
  const pm = lineP(X, k, side, L), c = crossMean(X, k, side), x = X.est[k][side];
  const px = c ? pOver({m: Math.max(c.m, 0.01), V: x.V * Math.max(c.m, 0.01) / x.m}, L, VK[k].cont) : null;
  return {pm, px, over: px == null ? pm : Math.min(pm, px), under: px == null ? 1 - pm : Math.min(1 - pm, 1 - px)};
}
const LEVELS3 = [['Muy prudente', 0.85], ['Prudente', 0.70], ['Optimista', 0.60]];
function prudentHtml(X, h, a) {
  const cell = (k, side, thr) => {
    const x = X.est[k][side], sd = Math.sqrt(x.V), lo = Math.max(0.5, Math.floor(x.m - 4 * sd) + 0.5), hi = Math.floor(x.m + 4 * sd) + 0.5;
    let up = null, dn = null;
    for (let L = lo; L <= hi; L += 1) { const b = bothOver(X, k, side, L); if (b.over >= thr) up = {L, p: b.over}; if (!dn && b.under >= thr) dn = {L, p: b.under}; }
    const fmt = (t, o) => `${t} ${lineTxt(o.L)} <small>(${pc(o.p)} · cuota justa ${f2(1 / o.p)})</small>`;
    return [up ? fmt('más de', up) : '', dn ? fmt('menos de', dn) : ''].filter(Boolean).join('<br>') || '–';
  };
  const rowsDef = [['g', 'T', 'Goles (total)'], ['c', 'T', 'Córners (total)'], ['y', 'T', 'Amarillas (total)'], ['st', 'T', 'Tiros a puerta (total)'],
    ['s', 'T', 'Tiros (total)'], ['f', 'T', 'Faltas (total)'], ['g', 'H', 'Goles ' + NM[h]], ['g', 'A', 'Goles ' + NM[a]],
    ['c', 'H', 'Córners ' + NM[h]], ['c', 'A', 'Córners ' + NM[a]], ['y', 'H', 'Amarillas ' + NM[h]], ['y', 'A', 'Amarillas ' + NM[a]]];
  const rows = rowsDef.filter(([k]) => X.est[k]).map(([k, side, lab]) => {
    const c = crossMean(X, k, side), m = X.est[k][side].m;
    const agree = c ? (Math.abs(c.m - m) <= Math.max(0.15 * m, 0.5) ? '<span class="chip clear">Coinciden</span>' : `<span class="chip maybe">${c.m > m ? 'Parecidos: más' : 'Parecidos: menos'}</span>`) : '<span class="chip">Sin cruce</span>';
    return `<tr><td class="l">${esc(lab)}</td><td>${f1(m)}</td><td>${c ? `${f1(c.m)} <small>(${c.n} p.)</small>` : '–'}</td><td>${agree}</td>${LEVELS3.map(([, t]) => `<td>${cell(k, side, t)}</td>`).join('')}</tr>`;
  });
  return card('Umbrales prudentes: modelo y rivales parecidos', tbl([['Estadística', 'l'], 'Esperado (modelo)', 'Rivales parecidos', 'Acuerdo',
    'Muy prudente (85 %)', 'Prudente (70 %)', 'Optimista (60 %)'], rows, 'num et') +
    note(`Una línea aparece solo si la cumplen a la vez el modelo y lo que han hecho los dos equipos contra rivales parecidos (se toma la menor de las dos probabilidades); si no hay partidos en el cruce, solo el modelo. "Rivales parecidos" mezcla lo que cada equipo hizo contra los parecidos al otro y lo que el otro concedió contra los parecidos a él; con pocos partidos es muy inestable. La <b>cuota justa</b> es la que correspondería a esa probabilidad: solo tendría sentido si una casa pagara claramente más (por su margen, al menos un 5-10 % más). Una línea muy probable paga muy poco, y que algo sea probable no lo convierte en buena apuesta.`));
}
/* ---------------------------------------------------------------- cara a cara y hándicaps */
const normDist = (mu, sd) => { const m = new Map(), s = Math.max(sd, 0.3);
  for (let d = Math.floor(mu - 6 * s); d <= Math.ceil(mu + 6 * s); d++) { const q = Phi((d + 0.5 - mu) / s) - Phi((d - 0.5 - mu) / s); if (q > 1e-7) m.set(d, q); } return m; };
const flip = dist => { const m = new Map(); dist.forEach((q, d) => m.set(-d, q)); return m; };
function settle(dist, h) { let w = 0, p = 0, l = 0; dist.forEach((q, d) => { const v = d + h; if (Math.abs(v) < 1e-9) p += q; else if (v > 0) w += q; else l += q; }); return {w, p, l}; }
/* Hándicap asiático h sobre la diferencia (equipo − rival): líneas de cuarto se reparten en dos mitades. */
function ah(dist, h) {
  const parts = Math.abs(Math.round(h * 4)) % 2 === 1 ? [h - 0.25, h + 0.25] : [h]; let w = 0, p = 0, l = 0;
  parts.forEach(x => { const s = settle(dist, x); w += s.w / parts.length; p += s.p / parts.length; l += s.l / parts.length; });
  return {w, p, l, fair: w > 0 ? 1 + l / w : 1e9};
}
const hTxt = h => (h > 0 ? '+' : h < 0 ? '−' : '') + f2(Math.abs(h)).replace(/,00$/, '').replace(/(,\d)0$/, '$1');
const fairTxt = x => isFinite(x) && x < 100 ? f2(x) : '–';
function h2hHtml(X, f) {
  const h = f.h, a = f.a, md = MODES[ST_.mode], NMx = s => NM[s === 'H' ? h : a];
  const keys = [['g', 'goles'], ['xg', 'xG'], ['s', 'tiros'], ['st', 'tiros a puerta'], ['c', 'córners'], ['y', 'amarillas'], ['f', 'faltas']];
  const rows = [], good = [], clash = [];
  keys.forEach(([k, lab]) => {
    const E = X.est[k], rH = X.cH.rows[k], rA = X.cA.rows[k]; if (!E || !rH || !rA) return;
    const pH = crossMean(X, k, 'H'), pA = crossMean(X, k, 'A'), dm = E.H.m - E.A.m;
    const distM = k === 'g' ? X.pr.dd : normDist(dm, Math.sqrt(E.H.V + E.A.V));
    let distX = null, dx = null;
    if (pH && pA) {
      const VH = E.H.V * pH.m / E.H.m, VA = E.A.V * pA.m / E.A.m;
      dx = pH.m - pA.m; distX = normDist(dx, Math.sqrt(VH + VA + VH / pH.n + VA / pA.n));
    }
    const fav = (dx != null ? dx : dm) >= 0 ? 'H' : 'A', und = fav === 'H' ? 'A' : 'H';
    const dM = fav === 'H' ? distM : flip(distM), dX = distX ? (fav === 'H' ? distX : flip(distX)) : null;
    const both = hh => { const m = ah(dM, hh), x = dX ? ah(dX, hh) : null; const w = x ? Math.min(m.w, x.w) : m.w, l = x ? Math.max(m.l, x.l) : m.l; return {m, x, w, l, fair: w > 0 ? 1 + l / w : 1e9}; };
    const more = both(-0.5), agree = !dX || (dm >= 0) === (dx >= 0);
    let best = null, safe = null;
    if (!VK[k].cont) for (let hh = -0.5; hh >= -40; hh -= 1) { const b = both(hh); if (b.w >= md.thr) best = {hh, ...b}; if (b.w >= 0.85) safe = {hh, ...b}; if (b.w < 0.5) break; }
    const cell = b => b ? `${esc(NMx(fav))} ${hTxt(b.hh)} <small>(${pc(b.w)} · cuota justa ${fairTxt(b.fair)})</small>` : '–';
    rows.push(`<tr><td class="l">${VK[k].n}</td><td>${f1(rH.obs)} <small>(${rH.f.n})</small></td><td>${f1(rA.obs)} <small>(${rA.f.n})</small></td>` +
      `<td>${f1(rH.obsA)}</td><td>${f1(rA.obsA)}</td><td>${dx != null ? sg1(dx) : '–'}</td><td>${sg1(dm)}</td>` +
      `<td>${agree ? `<b>${esc(NMx(fav))}</b> ${more.x ? pc(more.x.w) + ' / ' : ''}${pc(more.m.w)}` : '<span class="chip maybe">No coinciden</span>'}</td>` +
      `<td>${agree ? cell(best) : '–'}</td><td>${agree ? cell(safe) : '–'}</td></tr>`);
    if (!agree) clash.push(lab);
    else if (more.w >= md.thr) good.push([more.w, `<b>${esc(NMx(fav))}</b> debería tener más ${lab} que el ${esc(NMx(und))}: contra rivales parecidos ${esc(NMx(fav))} hace ${f1((fav === 'H' ? rH : rA).obs)} y ${esc(NMx(und))} ${f1((fav === 'H' ? rA : rH).obs)}; proyección para este partido ${f1(fav === 'H' ? pH && pH.m : pA && pA.m)} frente a ${f1(fav === 'H' ? pA && pA.m : pH && pH.m)}. Probabilidad ${more.x ? pc(more.x.w) + ' según el cruce y ' : ''}${pc(more.m.w)} según el modelo.` +
        (best ? ` Hándicap ${md.name.toLowerCase()}: <b>${esc(NMx(fav))} ${hTxt(best.hh)} ${lab}</b> (${pc(best.w)}, cuota justa ${fairTxt(best.fair)}).` : '')]);
  });
  good.sort((x, y) => y[0] - x[0]);
  const warn = [];
  const vH = X.cH.gs, vA = X.cA.gs;
  if (vH.length && vH.every(g => !g.home)) warn.push(`Todos los partidos del cruce del ${esc(NM[h])} fueron fuera de casa y hoy juega en casa.`);
  if (vA.length && vA.every(g => g.home)) warn.push(`Todos los partidos del cruce del ${esc(NM[a])} fueron en casa y hoy juega fuera.`);
  const n1 = vH.length, n2 = vA.length;
  return card('Cara a cara con rivales parecidos', `<p class="note" style="margin-top:0">${esc(NM[h])}: ${n1} partidos contra rivales parecidos al ${esc(NM[a])} · ${esc(NM[a])}: ${n2} contra rivales parecidos al ${esc(NM[h])}. Ventana ±${ST_.win} puestos; modo ${md.name.toLowerCase()} (${Math.round(md.thr * 100)} %).</p>` +
    (warn.length ? `<p class="note"><span class="chip warn">Atención</span> ${warn.join(' ')}</p>` : '') +
    `<h3>Conclusiones</h3>` + (good.length ? `<ul class="cl">${good.map(x => `<li>${x[1]}</li>`).join('')}</ul>` : note('Ninguna estadística cumple a la vez el cruce y el modelo con la probabilidad exigida.')) +
    (clash.length ? note(`El cruce y el modelo no coinciden en quién tendrá más ${clash.join(', ')}: ahí no hay conclusión.`) : '') +
    `<h3>Detalle</h3>` + tbl([['Estadística', 'l'], `${esc(NM[h])} hace`, `${esc(NM[a])} hace`, `${esc(NM[h])} concede`, `${esc(NM[a])} concede`,
      'Local − visitante (cruce)', 'Local − visitante (modelo)', 'Quién más (cruce / modelo)', `Hándicap ${md.name.toLowerCase()}`, 'Hándicap muy prudente (85 %)'], rows, 'num et') +
    note(`"Hace" y "concede" son medias contra los rivales parecidos al otro equipo (entre paréntesis, partidos). La diferencia del cruce proyecta cada equipo mezclando lo que hace él contra los parecidos al rival y lo que el rival concede contra los parecidos a él. Las probabilidades del hándicap son las menores entre cruce y modelo, para ser prudentes. Un hándicap −1,5 significa ganar esa estadística por 2 o más. La cuota justa es la que corresponde a esa probabilidad: solo hay valor si una casa paga claramente más.`));
}
function ahGoalsHtml(X, f) {
  const dd = X.pr.dd, lines = [-1.5, -1.25, -1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1, 1.25, 1.5];
  const mk = f.ah, rows = lines.map(hh => {
    const H = ah(dd, hh), A = ah(flip(dd), -hh), isM = mk && Math.abs(mk[0] - hh) < 1e-9;
    return `<tr class="${isM ? 'on' : ''}"><td class="l">${esc(NM[f.h])} ${hTxt(hh)} · ${esc(NM[f.a])} ${hTxt(-hh)}</td><td>${pc(H.w)}</td><td>${H.p > 0.001 ? pc(H.p) : '–'}</td><td>${pc(H.l)}</td><td>${fairTxt(H.fair)}</td><td>${fairTxt(A.fair)}</td>` +
      `<td>${isM ? `${f2(mk[1])} / ${f2(mk[2])}` : ''}</td></tr>`;
  });
  let mtxt = 'football-data todavía no ha publicado el hándicap asiático de este partido.';
  if (mk) {
    const H = ah(dd, mk[0]), A = ah(flip(dd), -mk[0]), evH = H.w * (mk[1] - 1) - H.l, evA = A.w * (mk[2] - 1) - A.l;
    mtxt = `Línea del mercado: ${esc(NM[f.h])} ${hTxt(mk[0])} a ${f2(mk[1])} y ${esc(NM[f.a])} ${hTxt(-mk[0])} a ${f2(mk[2])}. Con las probabilidades del modelo, apostar 1 € daría de media ${sgn(evH * 100, f0)} céntimos al ${esc(NM[f.h])} y ${sgn(evA * 100, f0)} al ${esc(NM[f.a])}. Recuerda que en la prueba retrospectiva el modelo ha sido peor que el mercado: un valor positivo aquí es más probablemente un error del modelo que de la casa.`;
  }
  return card('Hándicap asiático (goles)', tbl([['Línea', 'l'], 'Gana local', 'Nulo', 'Pierde local', 'Cuota justa local', 'Cuota justa visitante', 'Mercado (local / visitante)'], rows, 'num et') +
    note(`${mtxt} En las líneas de cuarto (,25 y ,75) la apuesta se reparte entre las dos líneas vecinas; "nulo" es la probabilidad de que se devuelva el dinero.`));
}
function renderPartido() {
  const f = FX.find(x => fxKey(x) === ST_.fx) || upcoming()[0] || FX[0];
  if (!f) { $('c-partido').innerHTML = card('', note('No quedan partidos pendientes.')); return; }
  ST_.fx = fxKey(f);
  const h = f.h, a = f.a, md = MODES[ST_.mode], z = md.z, X = estimates(h, a, ST_.win, ST_.useX), pr = X.pr, est = X.est;
  const mk = implied(f.odds), mo = implied2(f.ou), names = [NM[h], 'Empate', NM[a]];
  /* conclusiones */
  const C = {res: [], dif: [], lin: [], cx: []};
  const fav = pr.p.indexOf(Math.max(...pr.p));
  C.res.push(`Según el modelo, ${fav === 1 ? 'el empate es el resultado más probable' : `el favorito es el ${esc(names[fav])}`}: ${esc(NM[h])} ${pc(pr.p[0])}, empate ${pc(pr.p[1])}, ${esc(NM[a])} ${pc(pr.p[2])}. Goles esperados ${f1(pr.e[0])} – ${f1(pr.e[1])}.`);
  if (mk) {
    const dd = pr.p.map((x, k) => x - mk[k]), kk = dd.map(Math.abs).indexOf(Math.max(...dd.map(Math.abs)));
    const b = D.bt;
    C.res.push(`El mercado da ${esc(NM[h])} ${pc(mk[0])}, empate ${pc(mk[1])}, ${esc(NM[a])} ${pc(mk[2])}. La mayor diferencia está en ${kk === 1 ? 'el empate' : 'la victoria del ' + esc(names[kk])} (${ppt(dd[kk])}).` +
      (b && ok(b.dll) && b.dll > 2 * (b.dse || 0) ? ' En la prueba retrospectiva el modelo predice peor que el mercado, así que una diferencia así se explica antes por error del modelo que por un fallo de las casas.' : ''));
  } else C.res.push('No hay cuotas publicadas todavía para este partido; football-data las suele publicar unos días antes.');
  if (mo != null) C.res.push(`Más de 2,5 goles: modelo ${pc(pr.ou[2])}, mercado ${pc(mo)}.`);
  ['g', 'xg', 's', 'st', 'c', 'f', 'y'].forEach(k => {
    const E = est[k]; if (!E) return;
    const dm = E.H.m - E.A.m, de = Math.hypot(E.H.e, E.A.e), lv = level(dm, de);
    if ((lv === 'clear') || (lv === 'maybe' && z === 1)) {
      const [w, l] = dm > 0 ? [h, a] : [a, h];
      C.dif.push([Math.abs(dm) / de, `${chip(lv)} <b>${esc(NM[w])}</b>: más ${VK[k].low} que el ${esc(NM[l])} (${f1(Math.max(E.H.m, E.A.m))} frente a ${f1(Math.min(E.H.m, E.A.m))}; diferencia ${f1(Math.abs(dm))} ± ${f1(de)}).`]);
    }
  });
  C.dif.sort((x, y) => y[0] - x[0]);
  [['g', 'goles'], ['c', 'córners'], ['y', 'amarillas'], ['st', 'tiros a puerta'], ['s', 'tiros'], ['f', 'faltas']].forEach(([k, lab]) => {
    if (!est[k]) return;
    const u = umbral(X, k, 'T', md.thr), parts = [];
    if (u.up) parts.push(`más de ${lineTxt(u.up.L)} (${pc(u.up.p)})`);
    if (u.dn) parts.push(`menos de ${lineTxt(u.dn.L)} (${pc(u.dn.p)})`);
    if (parts.length) C.lin.push(`Total de ${lab}: ${parts.join(' y ')}. Esperado ${f1(est[k].T.m)}.`);
    if (k === 'g' || k === 'c') ['H', 'A'].forEach(s => {
      const v = umbral(X, k, s, md.thr);
      if (v.up) C.lin.push(`${esc(NM[s === 'H' ? h : a])}: más de ${lineTxt(v.up.L)} ${lab} (${pc(v.up.p)}).`);
    });
  });
  [[X.cH, h, a], [X.cA, a, h]].forEach(([c, t, o]) => VARS.forEach(({k}) => {
    const r = c.rows[k]; if (!r) return;
    [['f', 'más', 'menos', VK[k].low], ['a', 'más', 'menos', VK[k].low + ' en contra']].forEach(([side, mas, menos, lab]) => {
      const q = r[side]; if (!q.n) return;
      const lv = level(q.r, q.e);
      if (lv === 'clear' || (lv === 'maybe' && z === 1))
        C.cx.push([Math.abs(q.r) / q.e, `${chip(lv)} Contra rivales parecidos al ${esc(NM[o])} (${q.n} ${q.n === 1 ? 'partido' : 'partidos'}), el <b>${esc(NM[t])}</b> ha tenido ${f1(Math.abs(q.r))} ${q.r > 0 ? mas : menos} ${esc(lab)} de lo que esperaba el modelo (± ${f1(q.e)}).`]);
    });
  }));
  C.cx.sort((x, y) => y[0] - x[0]);
  const nCross = X.cH.gs.length + X.cA.gs.length;
  const li = arr => `<ul class="cl">${arr.map(x => `<li>${Array.isArray(x) ? x[1] : x}</li>`).join('')}</ul>`;
  const concl = `<h3>Resultado</h3>${li(C.res)}
    <h3>Diferencias entre los dos equipos</h3>${C.dif.length ? li(C.dif) : note(`Ninguna diferencia entre los dos equipos supera ${z === 1 ? 'un error' : 'dos errores'}.`)}
    <h3>Umbrales del partido</h3>${C.lin.length ? li(C.lin) : note('Ninguna línea alcanza la probabilidad mínima.')}
    <h3>Rivales parecidos</h3>${C.cx.length ? li(C.cx.slice(0, 8)) : note(nCross ? `Con ${nCross} partidos en el cruce, nada se aparta de lo que ya espera el modelo más allá del error${z === 1 ? ' (ni siendo optimistas)' : ''}.` : 'Ninguno de los dos ha jugado todavía contra rivales de esa zona de la tabla.')}`;
  /* tabla de estimaciones */
  const rng = x => `${f1(x.m)} <small>${f1(Math.max(x.m - z * x.e, 0))}–${f1(x.m + z * x.e)}</small>`;
  const erows = VARS.map(v => {
    const E = est[v.k]; if (!E) return '';
    const L0 = Math.floor(E.T.m) + 0.5, lines = v.cont ? '–' : [L0 - 1, L0, L0 + 1].filter(L => L > 0).map(L => `+${lineTxt(L)}: ${pc(lineP(X, v.k, 'T', L))}`).join(' · ');
    return `<tr><td>${v.n}</td><td>${rng(E.H)}</td><td>${rng(E.A)}</td><td>${rng(E.T)}</td><td class="ln">${lines}</td></tr>`;
  });
  const wmax = Math.max(0, ...Object.values(est).map(E => E.w || 0));
  /* tablas del cruce */
  const crossBlock = (c, t, o) => {
    const list = c.gs.length ? tbl(['Fecha', ['Lugar', 'l'], ['Rival (puesto actual)', 'l'], 'Resultado', 'xG', 'Córners', 'Amarillas'], c.gs.map(g =>
      `<tr><td>${fd(g.m.d)}</td><td class="l">${g.home ? 'Casa' : 'Fuera'}</td><td class="l">${nm(g.o)} (${POS[g.o]}º)</td><td><b>${g.gf}-${g.ga}</b></td><td>${f1(g.f.xg)}-${f1(g.a.xg)}</td><td>${f0(g.f.c)}-${f0(g.a.c)}</td><td>${f0(g.f.y)}-${f0(g.a.y)}</td></tr>`), 'num') : '';
    const rows = VARS.map(v => {
      const r = c.rows[v.k]; if (!r || !r.f.n) return '';
      const one = (q, obs, ex) => q.n ? `<td>${f1(obs)}</td><td>${f1(ex)}</td><td>${sg1(q.r)} <small>±${f1(q.e)}</small></td><td>${chip(level(q.r, q.e))}</td>` : '<td colspan="4">–</td>';
      return `<tr><td>${v.n}</td>${one(r.f, r.obs, r.exp)}${one(r.a, r.obsA, r.expA)}</tr>`;
    }).filter(Boolean);
    return `<h3>${nm(t)} contra rivales parecidos al ${nm(o)} <span class="mu">(puestos ${c.lo}º a ${c.hi}º: ${c.set.map(nm).join(', ')})</span></h3>` +
      (c.gs.length ? list + tbl(['', 'Real', 'Esperado', 'Diferencia', 'Señal', 'Real', 'Esperado', 'Diferencia', 'Señal'], rows, 'num xt') +
        '<p class="note">Las cuatro primeras columnas son lo que hizo el equipo y las cuatro siguientes lo que le hicieron sus rivales.</p>'
        : note(`${nm(t)} aún no ha jugado contra ninguno de ellos.`));
  };
  const head = `<div class="mh"><div><h2 class="tn">${nm(h)} – ${nm(a)}</h2><p class="sub">Jornada ${f.j} · ${fdl(f.d)}${f.tm ? ' · ' + f.tm : ''} ${statusOf(f)}</p></div></div>`;
  const ctr = `<div class="ctr">${fixtureSelect(ST_.fx)}
    <label>Rivales parecidos <select id="win-sel">${[2, 3, 4].map(v => `<option value="${v}" ${v === ST_.win ? 'selected' : ''}>±${v} puestos</option>`).join('')}</select></label>
    <div class="seg" role="group" aria-label="Nivel de exigencia">${Object.entries(MODES).map(([k, m]) => `<button data-mode="${k}" aria-pressed="${k === ST_.mode}" title="${m.desc}">${m.name}</button>`).join('')}</div>
    <label class="ck"><input type="checkbox" id="x-chk" ${ST_.useX ? 'checked' : ''}> Ajustar con rivales parecidos</label></div>
    <p class="note">${md.name}: rangos de ±${z} ${z === 1 ? 'error' : 'errores'} y umbrales con al menos ${Math.round(md.thr * 100)} % de probabilidad.</p>`;
  const sum = `<div class="pbs">${probBar(pr.p, 'Modelo')}${mk ? probBar(mk, 'Mercado') : ''}</div>
    <p class="legend"><span class="sw q0"></span>${nm(h)} <span class="sw q1"></span>Empate <span class="sw q2"></span>${nm(a)}</p>
    <div class="tiles sm"><div class="tile"><span>Goles esperados</span><b>${f1(pr.e[0])} – ${f1(pr.e[1])}</b></div>
    <div class="tile"><span>Marcador más probable</span><b>${pr.top[0][0]}-${pr.top[0][1]}</b><small>${pc(pr.top[0][2])} · luego ${pr.top.slice(1, 3).map(t => `${t[0]}-${t[1]} ${pc(t[2])}`).join(', ')}</small></div>
    <div class="tile"><span>Más de 2,5 goles</span><b>${pc(pr.ou[2])}</b>${mo != null ? `<small>mercado ${pc(mo)}</small>` : ''}</div>
    <div class="tile"><span>Ambos marcan</span><b>${pc(pr.bb)}</b></div></div>`;
  $('c-partido').innerHTML = ctr + head + card('Resumen', sum) + h2hHtml(X, f) + ahGoalsHtml(X, f) + prudentHtml(X, h, a) + card('Conclusiones', concl, 'concl') +
    card('Estimaciones y umbrales', tbl(['', esc(NM[h]), esc(NM[a]), 'Total', 'Probabilidad de superar la línea (total)'], erows, 'num et') +
      note(`Cada celda da la media esperada y, en pequeño, su rango con ±${z} ${z === 1 ? 'error' : 'errores'}: lo que cabe esperar de media, no de un partido concreto. Las probabilidades de la derecha sí son para este partido e incluyen la variación normal entre partidos. ` +
        `${!ST_.useX ? 'El ajuste con rivales parecidos está desactivado.' : wmax < 0.01
          ? 'El cruce con rivales parecidos no mueve estas cifras: con los datos de toda la liga, ninguna estadística muestra que el rendimiento cambie según la zona de la tabla del rival más de lo que daría el azar (prueba de permutación). Empezará a pesar solo si los datos llegan a demostrarlo.'
          : `El cruce con rivales parecidos pesa como mucho un ${Math.round(wmax * 100)} %, y solo en ${VARS.filter(v => { const c = CX(v.k); return c && (c.tf > 0 || c.ta > 0); }).map(v => v.low).join(', ')}: las estadísticas en las que los datos de toda la liga demuestran ese efecto.`}`)) +
    card('Cruce con rivales parecidos', crossBlock(X.cH, h, a) + crossBlock(X.cA, a, h) +
      note('El esperado es lo que el modelo preveía en esos mismos partidos, teniendo en cuenta el rival y si se jugaba en casa. La diferencia muestra si el equipo rinde por encima o por debajo de lo previsto contra ese tipo de rival. Se usa la clasificación actual.'));
}

/* ---------------------------------------------------------------- vista: predicciones */
function nextList() {
  const up = upcoming(), js = [...new Set(up.map(f => f.j))].slice(0, 2), first = up.length ? up[0].d : null;
  return FX.filter(f => f.past).concat(up.filter(f => js.includes(f.j) || f.d === first));
}
function renderPred() {
  const js = [...new Set(upcoming().map(f => f.j))].sort((x, y) => x - y);
  const list = ST_.jsel === 'next' ? nextList() : FX.filter(f => String(f.j) === ST_.jsel).sort(byDate);
  const rows = list.map(f => {
    const pr = predict(f.h, f.a), mk = implied(f.odds), mo = implied2(f.ou);
    let dif = '–';
    if (mk) { const d = pr.p.map((x, k) => x - mk[k]), k = d.map(Math.abs).indexOf(Math.max(...d.map(Math.abs))); dif = `${['1', 'X', '2'][k]} ${ppt(d[k])}`; }
    return `<tr><td class="l"><button class="lk" data-fx="${fxKey(f)}">${nm(f.h)} – ${nm(f.a)}</button></td><td>${f.past ? `J${f.j} · ${fd(f.d)} <span class="chip warn">pasada</span>` : `J${f.j} · ${fdl(f.d)}${f.tm ? ' ' + f.tm : ''}`}</td>` +
      `<td>${pr.p.map(pc).join(' · ')}</td><td>${mk ? mk.map(pc).join(' · ') : '–'}</td><td>${dif}</td><td>${f1(pr.e[0])} – ${f1(pr.e[1])}</td>` +
      `<td>${pc(pr.ou[2])}${mo != null ? ` <small>(${pc(mo)})</small>` : ''}</td><td>${pc(pr.bb)}</td><td>${pr.fs[0]}-${pr.fs[1]} <small>${pc(pr.fs[2])}</small></td></tr>`;
  });
  const SKS = ['xg', 's', 'st', 'c', 'f', 'y', 'r'];
  const srows = list.map(f => `<tr><td class="l">${nm(f.h)} – ${nm(f.a)}</td>${SKS.map(k => {
    const A = sPred(k, f.h, f.a, 1), B = sPred(k, f.a, f.h, 0); if (!A || !B) return '<td>–</td>';
    const p = SM[k], m = A.m + B.m, sd = Math.sqrt(A.V + B.V + 2 * (p.rr || 0) * p.phi * Math.sqrt(A.m * B.m));
    return `<td>${f1(m)} <small>${f1(Math.max(m - sd, 0))}–${f1(m + sd)}</small></td>`;
  }).join('')}</tr>`);
  const sel = `<div class="ctr"><label>Partidos <select id="j-sel"><option value="next" ${ST_.jsel === 'next' ? 'selected' : ''}>Próximos</option>${js.map(j => `<option value="${j}" ${String(j) === ST_.jsel ? 'selected' : ''}>Jornada ${j}</option>`).join('')}</select></label></div>`;
  const b = D.bt;
  const sim = D.sim.map((s, t) => ({t, s})).sort((x, y) => y.s[0] - x.s[0]);
  const heat = p => `<i style="--p:${Math.min(1, p * 2.2).toFixed(3)}" title="${pc(p)}"></i>`;
  const srows2 = sim.map(({t, s}) => `<tr><td class="l">${nm(t)}</td><td>${ROW[t].pts}</td><td>${f0(s[0])} <small>${s[1]}–${s[2]}</small></td>` +
    `<td>${pc(s[3])}</td><td>${pc(s[4])}</td><td>${pc(s[5])}</td><td>${pc(s[6])}</td><td><span class="heat" title="Probabilidad de cada puesto final">${s[7].map((p, k) => heat(p).replace('title="', `title="${k + 1}º: `)).join('')}</span></td></tr>`);
  $('c-pred').innerHTML = sel +
    card('Partidos', tbl(['Partido', 'Cuándo', 'Modelo 1 · X · 2', 'Mercado 1 · X · 2', 'Mayor diferencia', 'Goles esperados', '+2,5 goles (mercado)', 'Ambos marcan', 'Marcador'], rows, 'num pt') +
      note(`Pulsa un partido para analizarlo. El mercado son las cuotas medias de football-data sin su margen; aparecen unos días antes de cada jornada. ${b && ok(b.dll) ? `En la prueba retrospectiva (${b.n} partidos), el modelo tiene una log-loss ${f2(b.llmod)} frente a ${f2(b.llm)} del mercado (diferencia ${sg2(b.dll)} ± ${f2(b.dse)}; más baja es mejor), así que las diferencias con las cuotas no deben leerse como errores de las casas.` : ''}`)) +
    card('Estadísticas esperadas (total del partido)', tbl(['Partido', 'xG', 'Tiros', 'A puerta', 'Córners', 'Faltas', 'Amarillas', 'Rojas'], srows, 'num') +
      note('Valor esperado y, en pequeño, el rango de una desviación típica de un partido: cubre aproximadamente dos de cada tres partidos.')) +
    card('Simulación del resto de la liga', tbl(['Equipo', 'Pts', 'Pts finales (80 %)', 'Campeón', 'Top 4', 'Top 6', 'Descenso', 'Puesto final: 1º → 20º'], srows2, 'num sim') +
      note(`${D.meta.sims} temporadas simuladas con los partidos pendientes. En cada una se sortea también la fuerza de cada equipo, con su incertidumbre y una variación extra porque los equipos cambian durante la temporada. Los empates a puntos se resuelven con el art. 10 de las normas de la RFEF (enfrentamientos directos primero). El rango de puntos cubre el 80 % de las simulaciones.`)) +
    card('Fuerza de cada equipo', `<div class="sc">${strengthChart()}</div>` + tbl(['Equipo', 'Ataque', 'Defensa (goles encajados)'],
      T.map((_, i) => i).sort((x, y) => (GM.a[y] + GM.d[y]) - (GM.a[x] + GM.d[x])).map(i => `<tr><td class="l">${nm(i)}</td><td>×${f2(Math.exp(GM.a[i]))} <small>±${f2(Math.exp(GM.a[i]) * Math.sqrt(GM.va[i]))}</small></td><td>×${f2(Math.exp(-GM.d[i]))} <small>±${f2(Math.exp(-GM.d[i]) * Math.sqrt(GM.vd[i]))}</small></td></tr>`), 'num') +
      note(`Frente a un equipo medio: ataque ×1,20 son un 20 % más de goles; en defensa, menos de 1 es encajar menos. Ventaja de local: +${f0((Math.exp(GM.eta) - 1) * 100)} % de goles. Diferencia típica entre equipos estimada con los datos: ±${f0((Math.exp(GM.sa) - 1) * 100)} % en ataque y ±${f0((Math.exp(GM.sd) - 1) * 100)} % en defensa. Corrección de marcadores bajos (Dixon-Coles): ${f2(GM.rho)}.`));
}
function strengthChart() {
  const W = 640, H = 360, L = 52, R = 18, Tp = 18, B = 40;
  const xs = GM.a.map(Math.exp), ys = GM.d.map(d => Math.exp(-d));
  const xr = [Math.min(...xs, 0.9) * 0.95, Math.max(...xs, 1.1) * 1.03], yr = [Math.min(...ys, 0.9) * 0.95, Math.max(...ys, 1.1) * 1.03];
  const X = v => L + (v - xr[0]) / (xr[1] - xr[0]) * (W - L - R), Y = v => Tp + (v - yr[0]) / (yr[1] - yr[0]) * (H - Tp - B);
  const ticks = r => { const out = [], st = (r[1] - r[0]) > 1 ? 0.5 : 0.2; for (let v = Math.ceil(r[0] / st) * st; v <= r[1] + 1e-9; v += st) out.push(+v.toFixed(2)); return out; };
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Ataque frente a defensa de cada equipo">`;
  ticks(xr).forEach(v => { s += `<line class="grid" x1="${X(v)}" x2="${X(v)}" y1="${Tp}" y2="${H - B}"/><text class="ax" x="${X(v)}" y="${H - B + 16}" text-anchor="middle">×${f1(v)}</text>`; });
  ticks(yr).forEach(v => { s += `<line class="grid" x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}"/><text class="ax" x="${L - 8}" y="${Y(v) + 4}" text-anchor="end">×${f1(v)}</text>`; });
  s += `<line class="ref" x1="${X(1)}" x2="${X(1)}" y1="${Tp}" y2="${H - B}"/><line class="ref" x1="${L}" x2="${W - R}" y1="${Y(1)}" y2="${Y(1)}"/>`;
  s += `<text class="ax" x="${W - R}" y="${H - 6}" text-anchor="end">Ataque: goles marcados frente a un equipo medio →</text><text class="ax" x="${L}" y="12">↑ Defensa: menos goles encajados</text>`;
  const pts = xs.map((x, i) => ({i, x: X(x), y: Y(ys[i])})).sort((u, v) => u.y - v.y), placed = [];
  pts.forEach(p => {
    let ly = p.y - 9;
    while (placed.some(q => Math.abs(q.x - p.x) < 30 && Math.abs(q.y - ly) < 12)) ly += 12;
    placed.push({x: p.x, y: ly});
    s += `<g><title>${esc(NM[p.i])}: ataque ×${f2(xs[p.i])}, defensa ×${f2(ys[p.i])}</title><circle class="dot" cx="${p.x}" cy="${p.y}" r="5"/><text class="lab" x="${p.x}" y="${ly}" text-anchor="middle">${SH[p.i]}</text></g>`;
  });
  return s + '</svg>';
}

/* ---------------------------------------------------------------- vista: historial */
const LL = (p, o) => -Math.log(Math.max(p[o], 1e-9));
function aggJs(rows) {
  if (!rows.length) return null;
  const wm = rows.filter(r => r.mk), d = wm.map(r => LL(r.p, r.o) - LL(r.mk, r.o));
  return {n: rows.length, acc: mean(rows.map(r => r.p.indexOf(Math.max(...r.p)) === r.o ? 1 : 0)), ll: mean(rows.map(r => LL(r.p, r.o))),
    nm: wm.length, accm: wm.length ? mean(wm.map(r => r.mk.indexOf(Math.max(...r.mk)) === r.o ? 1 : 0)) : null,
    llm: wm.length ? mean(wm.map(r => LL(r.mk, r.o))) : null, llmod: wm.length ? mean(wm.map(r => LL(r.p, r.o))) : null,
    dll: d.length ? mean(d) : null, dse: d.length > 1 ? Math.sqrt(vr(d) / d.length) : null};
}
function renderHist() {
  const Lg = D.log, real = ST_.hreal && Lg.nreal > 0, rows = Lg.rows.filter(r => !real || !r.bf), A = aggJs(rows);
  const tog = `<div class="ctr"><div class="seg" role="group" aria-label="Qué predicciones">
    <button data-hreal="0" aria-pressed="${!real}">Todas (${Lg.n})</button><button data-hreal="1" aria-pressed="${real}" ${Lg.nreal ? '' : 'disabled'}>Guardadas antes del partido (${Lg.nreal})</button></div></div>
    ${note(Lg.nreal ? 'Las predicciones guardadas antes del partido son la prueba limpia. Las reconstruidas se calcularon después, pero solo con los partidos anteriores a cada uno.' : 'Todavía no se ha jugado ningún partido con predicción guardada antes de empezar: el registro arrancó con esta versión. De momento todas son reconstruidas, calculadas solo con los partidos anteriores a cada uno.')}`;
  if (!A) { $('c-hist').innerHTML = tog + card('', note('Aún no hay predicciones evaluadas.')); return; }
  const bets = rows.filter(r => r.bet).map(r => r.bet[2]), bm = mean(bets), bse = bets.length > 1 ? Math.sqrt(vr(bets) / bets.length) : null;
  const tiles = [['Partidos evaluados', `${A.n}`, real ? 'guardados antes del partido' : `${Lg.nreal} guardados antes · ${Lg.n - Lg.nreal} reconstruidos`],
    ['Aciertos del favorito', pc(A.acc), A.nm ? `mercado ${pc(A.accm)}` : ''],
    ['Log-loss (más bajo es mejor)', `${f2(A.llmod != null ? A.llmod : A.ll)} frente a ${f2(A.llm)}`, A.dll != null ? `modelo − mercado ${sg2(A.dll)} ± ${f2(A.dse)} · ${LEVELS[level(A.dll, A.dse)].toLowerCase()}` : ''],
    ['Apuestas simuladas', bets.length ? `${sg1(bets.reduce((s, x) => s + x, 0))} u. en ${bets.length}` : 'ninguna', bets.length ? `rentabilidad ${sgn(bm * 100, f0)} % ± ${f0((bse || 0) * 100)} %` : '']];
  const js = [...new Set(rows.map(r => r.j).filter(Boolean))].sort((x, y) => x - y);
  const jrows = js.map(j => { const rj = rows.filter(r => r.j === j), a = aggJs(rj);
    return `<tr><td>J${j}</td><td>${a.n}</td><td>${rj.filter(r => !r.bf).length}</td><td>${pc(a.acc)}</td><td>${f2(a.llmod != null ? a.llmod : a.ll)}</td><td>${f2(a.llm)}</td><td>${a.dll != null ? sg2(a.dll) : '–'}</td></tr>`; });
  const bins = [0, 0.2, 0.4, 0.6, 0.8].map(lo => ({lo, s: 0, h: 0, n: 0}));
  rows.forEach(r => r.p.forEach((p, k) => { const b = bins[Math.min(4, Math.floor(p * 5))]; b.s += p; b.h += r.o === k ? 1 : 0; b.n++; }));
  const crows = bins.filter(b => b.n).map(b => `<tr><td>${f0(b.lo * 100)}–${f0(b.lo * 100 + 20)} %</td><td>${b.n}</td><td>${pc(b.s / b.n)}</td><td>${pf(b.h / b.n)}</td><td>±${f0(Math.sqrt((b.s / b.n) * (1 - b.s / b.n) / b.n) * 100)} pp</td></tr>`);
  const skeys = ['xg', 's', 'st', 'c', 'f', 'y', 'r'];
  const strows = skeys.map(k => { const tr = rows.filter(r => r.st && r.st[k]).map(r => r.st[k]); if (!tr.length) return '';
    const mae = mean(tr.map(([p, o]) => Math.abs(p - o))), base = tr.filter(t => ok(t[2])), maeb = base.length ? mean(base.map(([, o, b]) => Math.abs(b - o))) : null, bias = mean(tr.map(([p, o]) => p - o));
    return `<tr><td>${VK[k].n}</td><td>${tr.length}</td><td>${f2(mae)}</td><td>${f2(maeb)}</td><td>${ok(maeb) ? sg0((mae / maeb - 1) * 100) + ' %' : '–'}</td><td>${sg2(bias)}</td></tr>`; }).filter(Boolean);
  const mrows = rows.slice(0, 60).map(r => {
    const hit = r.p.indexOf(Math.max(...r.p)) === r.o;
    return `<tr><td>${fd(r.d)}</td><td>${r.j ? 'J' + r.j : ''}</td><td class="l">${nm(r.h)} – ${nm(r.a)}</td><td><b>${r.hg}-${r.ag}</b></td><td>${r.p.map(pc).join(' · ')}</td><td>${r.mk ? r.mk.map(pc).join(' · ') : '–'}</td>` +
      `<td><span class="chip ${hit ? 'clear' : 'noise'}">${hit ? 'Acierto' : 'Fallo'}</span></td><td>${r.bet ? `${['1', 'X', '2'][r.bet[0]]} a ${f2(r.bet[1])}: ${sg2(r.bet[2])}` : '–'}</td><td>${r.bf ? 'Reconstruida' : 'Guardada ' + fd(r.made)}</td></tr>`;
  });
  const b = D.bt;
  const vrows = (D.var || []).map(v => `<tr><td class="l">${esc(v.name)}</td><td>${v.n}</td><td>${f2(v.ll)}</td><td>${sg2(v.dll)} <small>±${f2(v.dse)}</small></td><td>${pc(v.acc)}</td><td>${pc(v.pd)} / ${pc(v.fd)}</td></tr>`);
  $('c-hist').innerHTML = tog + `<div class="tiles">${tiles.map(t => `<div class="tile"><span>${t[0]}</span><b>${t[1]}</b><small>${t[2]}</small></div>`).join('')}</div>` +
    card('Por jornada', tbl(['Jornada', 'Partidos', 'Guardadas antes', 'Aciertos', 'Log-loss modelo', 'Log-loss mercado', 'Diferencia'], jrows, 'num') +
      note('Log-loss: castiga dar poca probabilidad a lo que pasó; repartir un tercio a cada resultado da 1,10. Una diferencia positiva significa que el modelo fue peor que el mercado.')) +
    card('Calibración', tbl(['Probabilidad dada', 'Casos', 'Media predicha', 'Frecuencia real', 'Error'], crows, 'num') +
      note('Si el modelo está bien calibrado, lo que predice al 30 % ocurre cerca del 30 % de las veces. Cada partido aporta tres casos (1, X y 2).')) +
    card('Apuestas simuladas', note(bets.length ? `Regla: apostar 1 unidad al resultado con más valor cuando la probabilidad del modelo por la cuota de cierre supera 1,05. Resultado: ${sg2(bets.reduce((s, x) => s + x, 0))} unidades en ${bets.length} apuestas (${bets.filter(x => x > 0).length} ganadas), rentabilidad ${sgn(bm * 100, f0)} % por apuesta con un error de ±${f0((bse || 0) * 100)} %. Con tan pocas apuestas el resultado es casi todo azar; harían falta cientos para saber si hay ventaja real. Es una simulación sin dinero, no una recomendación.` : 'Ninguna predicción cumple la regla de valor.')) +
    card('Estadísticas: error de los totales', strows.length ? tbl(['Estadística', 'Partidos', 'Error medio del modelo', 'Error usando la media de la liga', 'Cambio del error', 'Sesgo medio'], strows, 'num') +
      note('Error medio absoluto del total del partido. El cambio del error compara con predecir simplemente la media de la liga; un valor negativo indica que el modelo se equivoca menos. El sesgo positivo indica que el modelo esperaba más de lo que hubo.') : note('Sin datos todavía.')) +
    (b ? card('Prueba retrospectiva del modelo actual', note(`Cada partido desde que hay al menos 30 jugados se predice con un modelo ajustado solo con los partidos de días anteriores (${b.n} partidos). Log-loss: modelo ${f2(b.llmod)}, mercado ${f2(b.llm)}, mezcla 50/50 ${f2(b.llb)}. Empates: el modelo dio de media un ${pc(b.pd)} y hubo un ${pc(b.fd)}.${b.ou ? ` Más de 2,5 goles: log-loss ${f2(b.ou.ll)} el modelo y ${f2(b.ou.llm)} el mercado.` : ''}`) +
      tbl(['Variante', 'Partidos', 'Log-loss', 'Frente al mercado', 'Aciertos', 'Empates predichos / reales'], vrows, 'num') +
      note('Las variantes cambian una sola pieza del modelo. Diferencias de unas centésimas están dentro del error con tan pocos partidos.')) : '') +
    card('Partidos evaluados', tbl(['Fecha', 'J', ['Partido', 'l'], 'Resultado', 'Modelo 1 · X · 2', 'Mercado', '', 'Apuesta simulada', 'Predicción'], mrows, 'num'));
}

/* ---------------------------------------------------------------- vista: tendencias */
const TK = [['s', 'Tiros'], ['st', 'Tiros a puerta'], ['c', 'Córners'], ['y', 'Amarillas'], ['f', 'Faltas'], ['g', 'Goles']];
const TSt = {fx: 'all', k: 'all', min: 0.6, sort: 'gap', line: {}, odds: {}};
try { const sv = JSON.parse(localStorage.getItem('tend-odds') || '{}'); if (sv && typeof sv === 'object') TSt.odds = sv; } catch (e) { /* sin almacenamiento */ }
const saveOdds = () => { try { localStorage.setItem('tend-odds', JSON.stringify(TSt.odds)); } catch (e) { /* sin almacenamiento */ } };
const lapl = (h, n) => (h + 1) / (n + 2);  // frecuencia suavizada: con 2 de 2 no da 100 %
function tendRows() {
  const rows = [], STR = (D.streak || {})['5'];
  nextList().filter(f => TSt.fx === 'all' || fxKey(f) === TSt.fx).forEach(f => {
    const X = estimates(f.h, f.a, ST_.win, false);
    [['H', f.h, f.a, true], ['A', f.a, f.h, false], ['T', null, null, null]].forEach(([side, t, o, home]) => {
      TK.forEach(([k, lab]) => {
        if (TSt.k !== 'all' && TSt.k !== k) return;
        if (side === 'T' && !['c', 'y', 's', 'st', 'g'].includes(k)) return;
        const E = X.est[k]; if (!E) return;
        const val = g => side === 'T' ? (ok(g.f[k]) && ok(g.a[k]) ? g.f[k] + g.a[k] : null) : g.f[k];
        const tm = side === 'T' ? f.h : t, hist = G[tm].filter(g => ok(val(g)));
        const last = hist.slice(-5).map(val);
        if (last.length < 3) return;
        const key = `${fxKey(f)}|${side}|${k}`;
        const L = TSt.line[key] != null ? TSt.line[key] : Math.min(...last) - 0.5;
        if (L < 0.5) return;
        const same = side === 'T' ? null : hist.filter(g => g.home === home).slice(-5).map(val);
        let cr = null;
        if (side !== 'T') { const S = new Set(near(o, t, ST_.win)), gs = G[t].filter(g => S.has(g.o) && ok(g.f[k])); cr = {n: gs.length, h: gs.filter(g => g.f[k] > L).length, v: gs.map(g => g.f[k])}; }
        else { const S1 = new Set(near(f.a, f.h, ST_.win)), S2 = new Set(near(f.h, f.a, ST_.win));
          const g1 = G[f.h].filter(g => S1.has(g.o)), g2 = G[f.a].filter(g => S2.has(g.o)), all = g1.concat(g2).map(val).filter(ok);
          cr = {n: all.length, h: all.filter(v => v > L).length, v: all}; }
        const pm = lineP(X, k, side, L), hits = last.filter(v => v > L).length;
        const parts = [pm]; if (cr && cr.n) parts.push(lapl(cr.h, cr.n));
        const pp = Math.min(...parts), odds = TSt.odds[key + '|' + L], emp = lapl(hits + (cr ? cr.h : 0), last.length + (cr ? cr.n : 0));
        rows.push({f, side, t, k, lab, key, L, last, hits, same, cr, pm, pp, odds, emp, gap: emp - pm, ev: ok(odds) ? pp * odds - 1 : null,
          custom: TSt.line[key] != null, calib: STR && STR.by[k] ? STR.by[k].hit : null, mean: E[side].m});
      });
    });
  });
  const keep = r => r.custom || ok(r.odds) || (r.pp >= TSt.min && r.pm <= 0.92);
  const by = TSt.sort === 'gap' ? (x, y) => y.gap - x.gap : (x, y) => y.pp - x.pp;
  return rows.filter(keep).sort((x, y) => (ok(y.ev) - ok(x.ev)) || ((y.ev || 0) - (x.ev || 0)) || by(x, y));
}
function renderTend() {
  const rows = tendRows(), S5 = (D.streak || {})['5'], S4 = (D.streak || {})['4'];
  const fxs = nextList();
  const ctr = `<div class="ctr"><label>Partido <select id="t-fx"><option value="all">Todos los próximos</option>${fxs.map(f => `<option value="${fxKey(f)}" ${fxKey(f) === TSt.fx ? 'selected' : ''}>${nm(f.h)} – ${nm(f.a)}</option>`).join('')}</select></label>
    <label>Estadística <select id="t-k"><option value="all">Todas</option>${TK.map(([k, l]) => `<option value="${k}" ${k === TSt.k ? 'selected' : ''}>${l}</option>`).join('')}</select></label>
    <label>Ordenar <select id="t-sort"><option value="gap" ${TSt.sort === 'gap' ? 'selected' : ''}>La racha supera al modelo</option><option value="pp" ${TSt.sort === 'pp' ? 'selected' : ''}>Más probables</option></select></label>
    <label>Probabilidad prudente mínima <select id="t-min">${[0.5, 0.6, 0.7, 0.8].map(v => `<option value="${v}" ${v === TSt.min ? 'selected' : ''}>${Math.round(v * 100)} %</option>`).join('')}</select></label></div>`;
  const spark = (vals, L) => vals.map(v => `<span class="tv ${v > L ? 'hit' : 'miss'}">${f0(v)}</span>`).join('');
  const body = rows.slice(0, 150).map(r => {
    const who = r.side === 'T' ? 'Total del partido' : NM[r.t];
    const sm = r.same && r.same.length ? `${r.same.filter(v => v > r.L).length}/${r.same.length}` : '–';
    const evc = ok(r.ev) ? `<span class="chip ${r.ev > 0.05 ? 'clear' : r.ev > 0 ? 'maybe' : 'noise'}">${sgn(r.ev * 100, f0)} cént.</span>` : '–';
    return `<tr><td class="l">${nm(r.f.h)} – ${nm(r.f.a)}<br><small>${r.f.past ? 'aplazado' : fdl(r.f.d)}</small></td><td class="l">${esc(who)}</td><td class="l">${r.lab}</td>` +
      `<td><input class="tin tl" data-key="${r.key}" type="number" step="1" min="0.5" value="${r.L}" aria-label="Línea" style="width:5.2em"></td>` +
      `<td class="l"><span class="tvs">${spark(r.last, r.L)}</span> <small>${r.hits}/${r.last.length}</small></td><td>${sm}</td>` +
      `<td>${r.cr && r.cr.n ? `${r.cr.h}/${r.cr.n}` : '–'}</td><td>${f1(r.mean)}</td><td>${pc(r.emp)}</td><td>${pc(r.pm)}</td><td>${ppt(r.gap)}</td><td><b>${pc(r.pp)}</b></td><td>${fairTxt(1 / r.pp)}</td>` +
      `<td><input class="tin to" data-key="${r.key}|${r.L}" type="number" step="0.01" min="1.01" value="${ok(r.odds) ? r.odds : ''}" placeholder="cuota" aria-label="Cuota de la casa" style="width:5.6em"></td><td>${evc}</td></tr>`;
  });
  const calib = S5 ? `En lo que va de temporada, cuando un equipo superaba una línea en sus 5 últimos partidos, la volvió a superar en el siguiente el <b>${pc(S5.hit)}</b> de las veces (${S5.n} casos); el modelo ya preveía de media un ${pc(S5.model)}.` +
    (S4 ? ` Con 4 de 5, se cumplió el ${pc(S4.hit)} (modelo: ${pc(S4.model)}).` : '') +
    ` Es decir: la racha se cumple a menudo, pero no aporta nada que el modelo no supiera ya. La racha elige líneas bajas, que por eso se cumplen mucho y pagan poco. Una apuesta solo tiene valor si la casa paga más que la cuota justa.` : '';
  $('c-tend').innerHTML = ctr + card('Qué dicen los datos sobre las rachas', note(calib) + (S5 ? tbl([['Estadística', 'l'], 'Casos', 'Se cumplió', 'El modelo decía'],
      Object.entries(S5.by).map(([k, v]) => `<tr><td class="l">${VK[k].n}</td><td>${v.n}</td><td>${pc(v.hit)}</td><td>${pc(v.model)}</td></tr>`), 'num') : '')) +
    card('Tendencias de los próximos partidos', tbl([['Partido', 'l'], ['Equipo', 'l'], ['Estadística', 'l'], 'Línea (más de)', ['Últimos partidos', 'l'], 'Mismo campo', 'Rivales parecidos',
      'Esperado (modelo)', 'Según la racha', 'Según el modelo', 'Diferencia', 'Prudente', 'Cuota justa', 'Cuota de la casa', 'Valor por 1 €'], body, 'num et tt') +
      note(`La línea por defecto es la más alta que el equipo superó en sus 5 últimos partidos; puedes cambiarla y escribir la cuota que te ofrece la casa. <b>Mismo campo</b>: veces que la superó en sus últimos partidos en casa (o fuera, según toque hoy). <b>Rivales parecidos</b>: veces que la superó contra los rivales a ±${ST_.win} puestos del de hoy. <b>Según la racha</b>: veces que la superó en los últimos partidos y contra rivales parecidos, juntas y suavizadas. <b>Diferencia</b>: cuánto más optimista es la racha que el modelo; al ordenar por ella salen primero casos como el del Rayo, en los que el equipo viene rindiendo muy por encima de lo que el modelo espera (y donde una casa que no lo tenga en cuenta podría pagar de más). Se ocultan las líneas casi seguras (el modelo da más del 92 %), que no pagan nada. <b>Prudente</b>: la menor entre el modelo y los rivales parecidos (suavizada para que 2 de 2 no cuente como 100 %). <b>Valor</b>: lo que ganarías de media por euro con la probabilidad prudente; en verde si supera 5 céntimos. Las cuotas que escribas se guardan solo en este navegador. ${rows.length > 150 ? `Se muestran 150 de ${rows.length}; filtra por partido o estadística.` : ''} No es una recomendación de apuesta.`));
}

/* ---------------------------------------------------------------- arranque */
const VIEWS = ['equipos', 'partido', 'predicciones', 'tendencias', 'historial', 'metodo'];
const rendered = {};
function show(view, scroll) {
  if (!VIEWS.includes(view)) view = 'equipos';
  VIEWS.forEach(v => { $('v-' + v).hidden = v !== view; const b = document.querySelector(`[data-view="${v}"]`); if (b) b.setAttribute('aria-selected', String(v === view)); });
  if (view === 'equipos') renderEquipos(); else if (view === 'partido') renderPartido(); else if (view === 'predicciones') renderPred(); else if (view === 'historial') renderHist(); else if (view === 'tendencias') renderTend();
  rendered[view] = true;
  try { history.replaceState(null, '', '#' + view); } catch (e) { /* sin historial */ }
  if (scroll) window.scrollTo({top: 0});
}
document.addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b || b.disabled) return;
  const d = b.dataset;
  if (d.view) show(d.view);
  else if (d.team != null) { ST_.sel = +d.team; renderEquipos(); if (window.innerWidth < 900) $('team').scrollIntoView({block: 'start'}); }
  else if (d.fx) { ST_.fx = d.fx; show('partido', true); }
  else if (d.ps) { ps = d.ps; renderTeam(); }
  else if (d.mode) { ST_.mode = d.mode; renderPartido(); }
  else if (d.hreal != null) { ST_.hreal = d.hreal === '1'; renderHist(); }
});
document.addEventListener('change', e => {
  const t = e.target;
  if (t.id === 'rk-sel') { ST_.rk = t.value; renderRank(); }
  else if (t.id === 'fx-sel') { ST_.fx = t.value; renderPartido(); }
  else if (t.id === 'win-sel') { ST_.win = +t.value; renderPartido(); }
  else if (t.id === 'x-chk') { ST_.useX = t.checked; renderPartido(); }
  else if (t.id === 'j-sel') { ST_.jsel = t.value; renderPred(); }
  else if (t.id === 't-fx') { TSt.fx = t.value; renderTend(); }
  else if (t.id === 't-k') { TSt.k = t.value; renderTend(); }
  else if (t.id === 't-min') { TSt.min = +t.value; renderTend(); }
  else if (t.id === 't-sort') { TSt.sort = t.value; renderTend(); }
  else if (t.classList.contains('tl')) { const v = parseFloat(t.value); if (ok(v) && v > 0) { TSt.line[t.dataset.key] = Math.floor(v) + 0.5; renderTend(); } }
  else if (t.classList.contains('to')) { const v = parseFloat(String(t.value).replace(',', '.')); if (ok(v) && v > 1) TSt.odds[t.dataset.key] = v; else delete TSt.odds[t.dataset.key]; saveOdds(); renderTend(); }
});
$('rk-sel').innerHTML = RKS.map(([v, l]) => `<option value="${v}">${l} por partido</option>`).join('');
const m = D.meta;
$('sub').textContent = `${m.n} partidos · datos hasta el ${fdl(m.last)} · actualizado ${m.gen}`;
$('foot').innerHTML = `Datos: football-data.co.uk (resultados, estadísticas, xG y cuotas) y calendario de la RFEF. Modelo ${esc(m.ver)}. ` +
  (m.fx ? `Cuotas de ${m.fx} próximos partidos.` : 'Sin cuotas de próximos partidos en esta actualización.') + (m.warn.length ? '<br>' + m.warn.map(esc).join('<br>') : '');
const h0 = (location.hash || '').slice(1);
show(VIEWS.includes(h0) ? h0 : 'equipos');
window.__app = {predict, sPred, pOver, cross, estimates, M, G, FX, POS};
})();
