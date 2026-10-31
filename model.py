"""Modelos estadísticos del dashboard de LaLiga 2026-27. Solo usan partidos de la temporada en curso.

Todo está escrito en Python estándar (sin numpy) para que GitHub Actions lo ejecute sin instalar nada.

- glm(): modelo log-lineal tipo Poisson con ataque y defensa por equipo, ventaja de local y
  sobredispersión. El encogimiento hacia la media se estima con los propios datos (Bayes empírico):
  cuanto más se diferencian de verdad los equipos, menos se encogen. Sirve para goles y estadísticas.
- Goles: el objetivo mezcla goles reales y xG, se corrigen los marcadores bajos (Dixon-Coles, que
  ajusta 0-0, 1-0, 0-1 y 1-1) y la incertidumbre de los parámetros se integra en cada predicción.
- simulate(): resto de la liga con los desempates del art. 10 de las normas de competición RFEF.
- walk_forward_*(): prueba retrospectiva; cada partido se predice solo con los anteriores.
- update_log() / evaluate_log(): predicciones congeladas antes de cada partido y su evaluación.
"""
import math
import random
from datetime import date, timedelta

VERSION = "4.1"

# Estadísticas que se modelan aparte de los goles (clave, nombre).
STATS = [("g1", "Goles 1ª parte"), ("xg", "xG"), ("s", "Tiros"), ("st", "Tiros a puerta"),
         ("c", "Córners"), ("f", "Faltas"), ("y", "Amarillas"), ("r", "Rojas")]
CROSS_KEYS = ["g", "g1", "g2", "xg", "s", "st", "c", "f", "y", "r"]

# w: peso de los goles reales frente al xG en el objetivo. half_life: vida media en días del peso
# temporal (None = todos los partidos pesan igual). dc: corrección de marcadores bajos.
GOALS = {"w": 0.5, "half_life": None, "dc": True}

# Cuadratura de Gauss-Hermite (5 puntos, pesos ya divididos por raíz de pi).
GH = [(-2.0201828704560856, 0.011257411327720691), (-0.9585724646138185, 0.22207592200561265),
      (0.0, 0.5333333333333333), (0.9585724646138185, 0.22207592200561265),
      (2.0201828704560856, 0.011257411327720691)]


# ----------------------------------------------------------------- utilidades
def days(d1, d2):
    return (date.fromisoformat(d2) - date.fromisoformat(d1)).days


def pmf(lam, K=10):
    out = [math.exp(-lam)]
    for k in range(1, K + 1):
        out.append(out[-1] * lam / k)
    return out


def outcome(x, y):
    return 0 if x > y else (1 if x == y else 2)


def mkey(h, a):
    return h + "|" + a


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def corr(x, y):
    n = len(x)
    if n < 3:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else 0.0


def implied(odds):
    """Probabilidades del mercado quitando el margen (normalización proporcional)."""
    if not odds or any((not o) or o <= 1 for o in odds):
        return None
    inv = [1 / o for o in odds]
    s = sum(inv)
    return [x / s for x in inv]


def value(m, key):
    """Valores [local, visitante] de una estadística en un partido (None si falta)."""
    if key == "g":
        return [m["hg"], m["ag"]]
    if key == "g2":
        g1 = m.get("g1")
        return None if g1 is None else [m["hg"] - g1[0], m["ag"] - g1[1]]
    return m.get(key)


# ----------------------------------------------------------------- modelo de equipos
def glm(obs, n, outer=14, tol=1e-7):
    """Ajusta log m = mu + eta*local + a[i] - d[j] con previas a ~ N(0, sa²) y d ~ N(0, sd²).

    obs: lista de (equipo, rival, local 0/1, valor, peso). sa y sd se estiman con los datos (Bayes
    empírico) y phi (dispersión: varianza = phi * media) con los residuos de Pearson.
    Devuelve las medias posteriores, sus varianzas (va, vd) y la varianza de los niveles base."""
    N = len(obs)
    I = [o[0] for o in obs]
    J = [o[1] for o in obs]
    H = [o[2] for o in obs]
    Y = [float(o[3]) for o in obs]
    W = [float(o[4]) for o in obs]
    sw = sum(W)
    mu = math.log(max(sum(w * y for w, y in zip(W, Y)) / sw, 1e-3))
    eta = 0.0
    a = [0.0] * n
    d = [0.0] * n
    byI = [[] for _ in range(n)]
    byJ = [[] for _ in range(n)]
    for k in range(N):
        byI[I[k]].append(k)
        byJ[J[k]].append(k)
    hk = [k for k in range(N) if H[k]]
    sa2 = sd2 = 0.09
    phi = 1.0
    eta_prec = 4.0  # previa débil para la ventaja de local: N(0, 0,5²)
    m = [1.0] * N
    for _ in range(outer):
        for k in range(N):
            m[k] = math.exp(mu + eta * H[k] + a[I[k]] - d[J[k]])
        for _ in range(100):
            big = 0.0
            st = sum(W[k] * (Y[k] - m[k]) for k in range(N)) / sum(W[k] * m[k] for k in range(N))
            mu += st
            big = max(big, abs(st))
            f = math.exp(st)
            for k in range(N):
                m[k] *= f
            if hk:
                num = sum(W[k] * (Y[k] - m[k]) for k in hk) / phi - eta * eta_prec
                den = sum(W[k] * m[k] for k in hk) / phi + eta_prec
                st = num / den
                eta += st
                big = max(big, abs(st))
                f = math.exp(st)
                for k in hk:
                    m[k] *= f
            for i in range(n):
                ks = byI[i]
                num = sum(W[k] * (Y[k] - m[k]) for k in ks) / phi - a[i] / sa2
                den = sum(W[k] * m[k] for k in ks) / phi + 1 / sa2
                st = num / den
                a[i] += st
                big = max(big, abs(st))
                f = math.exp(st)
                for k in ks:
                    m[k] *= f
            for j in range(n):
                ks = byJ[j]
                num = -sum(W[k] * (Y[k] - m[k]) for k in ks) / phi - d[j] / sd2
                den = sum(W[k] * m[k] for k in ks) / phi + 1 / sd2
                st = num / den
                d[j] += st
                big = max(big, abs(st))
                f = math.exp(-st)
                for k in ks:
                    m[k] *= f
            if big < tol:
                break
        Ia = [sum(W[k] * m[k] for k in byI[i]) / phi for i in range(n)]
        Id = [sum(W[k] * m[k] for k in byJ[j]) / phi for j in range(n)]
        va = [1 / (Ia[i] + 1 / sa2) for i in range(n)]
        vd = [1 / (Id[j] + 1 / sd2) for j in range(n)]
        pe = 2 + sum(Ia[i] * va[i] for i in range(n)) + sum(Id[j] * vd[j] for j in range(n))
        pear = sum(W[k] * (Y[k] - m[k]) ** 2 / max(m[k], 1e-6) for k in range(N))
        phi = min(max(pear / max(sw - pe, 0.5 * sw), 0.2), 5.0)
        sa2 = min(max(sum(x * x + v for x, v in zip(a, va)) / n, 0.03 ** 2), 0.6 ** 2)
        sd2 = min(max(sum(x * x + v for x, v in zip(d, vd)) / n, 0.03 ** 2), 0.6 ** 2)
    Ia = [sum(W[k] * m[k] for k in byI[i]) / phi for i in range(n)]
    Id = [sum(W[k] * m[k] for k in byJ[j]) / phi for j in range(n)]
    va = [1 / (Ia[i] + 1 / sa2) for i in range(n)]
    vd = [1 / (Id[j] + 1 / sd2) for j in range(n)]
    mh = sum(W[k] * m[k] for k in hk) / phi
    ma = sum(W[k] * m[k] for k in range(N)) / phi - mh
    return {"mu": mu, "eta": eta, "a": a, "d": d, "va": va, "vd": vd,
            "vh0": 1 / mh if mh > 0 else 0.0, "va0": 1 / ma if ma > 0 else 0.0,
            "phi": phi, "sa": math.sqrt(sa2), "sd": math.sqrt(sd2), "m": m[:]}


def lin(p, i, j, home):
    """Logaritmo de la media esperada del equipo i contra j y su varianza (incertidumbre)."""
    return (p["mu"] + (p["eta"] if home else 0.0) + p["a"][i] - p["d"][j],
            (p["vh0"] if home else p["va0"]) + p["va"][i] + p["vd"][j])


def weight(m, half_life, ref):
    return 0.5 ** (max(days(m["date"], ref), 0) / half_life) if (half_life and ref) else 1.0


# ----------------------------------------------------------------- goles
def fit_rho(pairs, sd=0.2):
    """Parámetro de Dixon-Coles por máxima verosimilitud con una previa suave N(0, 0,2²)."""
    best_r, best = 0.0, -1e18
    for k in range(-50, 31):
        r = k / 200
        ll = -r * r / (2 * sd * sd)
        ok = True
        for x, y, lh, la in pairs:
            if x > 1 or y > 1:
                continue
            t = (1 - lh * la * r) if (x == 0 and y == 0) else (1 + lh * r) if x == 0 else (1 + la * r) if y == 0 else (1 - r)
            if t <= 1e-9:
                ok = False
                break
            ll += math.log(t)
        if ok and ll > best:
            best, best_r = ll, r
    return best_r


def fit_goals(matches, teams, cfg=None, ref=None):
    c = dict(GOALS, **(cfg or {}))
    ix = {t: k for k, t in enumerate(teams)}
    obs = []
    for m in matches:
        wt = weight(m, c["half_life"], ref)
        xg = m.get("xg")
        yh = m["hg"] if xg is None else c["w"] * m["hg"] + (1 - c["w"]) * xg[0]
        ya = m["ag"] if xg is None else c["w"] * m["ag"] + (1 - c["w"]) * xg[1]
        i, j = ix[m["h"]], ix[m["a"]]
        obs += [(i, j, 1, yh, wt), (j, i, 0, ya, wt)]
    p = glm(obs, len(teams))
    pairs = [(m["hg"], m["ag"], math.exp(lin(p, ix[m["h"]], ix[m["a"]], 1)[0]),
              math.exp(lin(p, ix[m["a"]], ix[m["h"]], 0)[0])) for m in matches]
    p["rho"] = fit_rho(pairs) if c["dc"] else 0.0
    p.update(ix=ix, teams=teams, w=c["w"])
    return p


def score_matrix(p, i, j, K=10):
    """Probabilidad de cada marcador, promediando sobre la incertidumbre de los parámetros."""
    lh, vh = lin(p, i, j, 1)
    la, va = lin(p, j, i, 0)
    rho = p.get("rho", 0.0)
    sh, sa = math.sqrt(2 * vh), math.sqrt(2 * va)
    M = [[0.0] * (K + 1) for _ in range(K + 1)]
    for xi, wi in GH:
        l1 = math.exp(lh + sh * xi)
        p1 = pmf(l1, K)
        for xj, wj in GH:
            l2 = math.exp(la + sa * xj)
            p2 = pmf(l2, K)
            ww = wi * wj
            for x in range(K + 1):
                c = ww * p1[x]
                row = M[x]
                for y in range(K + 1):
                    row[y] += c * p2[y]
            if rho:
                M[0][0] += ww * p1[0] * p2[0] * (max(1 - l1 * l2 * rho, 0.0) - 1)
                M[0][1] += ww * p1[0] * p2[1] * (max(1 + l1 * rho, 0.0) - 1)
                M[1][0] += ww * p1[1] * p2[0] * (max(1 + l2 * rho, 0.0) - 1)
                M[1][1] += ww * p1[1] * p2[1] * (max(1 - rho, 0.0) - 1)
    s = sum(map(sum, M))
    return [[v / s for v in row] for row in M]


def summarize(M):
    K = len(M) - 1
    pH = pD = pA = eh = ea = bb = 0.0
    tot = [0.0] * (2 * K + 1)
    hx = [0.0] * (K + 1)
    ay = [0.0] * (K + 1)
    cells = []
    for x in range(K + 1):
        for y in range(K + 1):
            q = M[x][y]
            if x > y:
                pH += q
            elif x == y:
                pD += q
            else:
                pA += q
            eh += x * q
            ea += y * q
            tot[x + y] += q
            hx[x] += q
            ay[y] += q
            if x and y:
                bb += q
            cells.append((q, x, y))
    cells.sort(reverse=True)
    over = lambda dist, L: sum(v for k, v in enumerate(dist) if k > L)
    fav = max(range(3), key=lambda k: (pH, pD, pA)[k])
    fs = next(c for c in cells if outcome(c[1], c[2]) == fav)
    var = lambda dist, m: sum(v * (k - m) ** 2 for k, v in enumerate(dist))
    return {"p": [pH, pD, pA], "e": [eh, ea], "V": [var(hx, eh), var(ay, ea), var(tot, eh + ea)],
            "ou": [over(tot, L) for L in (0.5, 1.5, 2.5, 3.5, 4.5)],
            "bb": bb, "th": [over(hx, L) for L in (0.5, 1.5, 2.5)], "ta": [over(ay, L) for L in (0.5, 1.5, 2.5)],
            "top": [[c[1], c[2], c[0]] for c in cells[:6]], "fs": [fs[1], fs[2], fs[0]]}


def predict_goals(p, h, a):
    return summarize(score_matrix(p, p["ix"][h], p["ix"][a]))


# ----------------------------------------------------------------- estadísticas
def fit_stat(matches, teams, key, cfg=None, ref=None):
    c = dict(GOALS, **(cfg or {}))
    ix = {t: k for k, t in enumerate(teams)}
    obs = []
    for m in matches:
        v = m.get(key)
        if v is None:
            continue
        wt = weight(m, c["half_life"], ref)
        i, j = ix[m["h"]], ix[m["a"]]
        obs += [(i, j, 1, v[0], wt), (j, i, 0, v[1], wt)]
    if len(obs) < 40:
        return None
    p = glm(obs, len(teams))
    m, ph = p["m"], p["phi"]
    rh = [(obs[k][3] - m[k]) / math.sqrt(m[k] * ph) for k in range(0, len(obs), 2)]
    ra = [(obs[k + 1][3] - m[k + 1]) / math.sqrt(m[k + 1] * ph) for k in range(0, len(obs), 2)]
    p["rr"] = max(-0.6, min(0.6, corr(rh, ra)))  # correlación entre los dos equipos del mismo partido
    p.update(ix=ix, key=key)
    return p


def stat_pred(p, i, j, home):
    """Media esperada, varianza del partido y error de la media para el equipo i contra j."""
    l, v = lin(p, i, j, home)
    mean_ = math.exp(l + v / 2)
    err2 = mean_ * mean_ * (math.exp(v) - 1)
    return mean_, p["phi"] * mean_ + err2, math.sqrt(err2)


def stat_total(p, i, j):
    m1, v1, e1 = stat_pred(p, i, j, 1)
    m2, v2, e2 = stat_pred(p, j, i, 0)
    cov = p["rr"] * p["phi"] * math.sqrt(m1 * m2)
    return m1 + m2, max(v1 + v2 + 2 * cov, 1e-6), math.sqrt(e1 * e1 + e2 * e2)


def expectations(played, gm, sms):
    """Valor esperado por el modelo (en la muestra) de cada estadística en cada partido jugado."""
    out = []
    for m in played:
        i, j = gm["ix"][m["h"]], gm["ix"][m["a"]]
        e = {"g": [math.exp(lin(gm, i, j, 1)[0]), math.exp(lin(gm, j, i, 0)[0])]}
        for k, p in sms.items():
            if p:
                e[k] = [math.exp(lin(p, i, j, 1)[0]), math.exp(lin(p, j, i, 0)[0])]
        if "g1" in e:
            e["g2"] = [e["g"][0] - e["g1"][0], e["g"][1] - e["g1"][1]]
        out.append(e)
    return out


def cross_tau(played, E, key, pos, tiers=4):
    """Cuánto cambia de verdad el rendimiento de un equipo según el nivel del rival, más allá del modelo.

    Agrupa los rivales en 4 franjas de la clasificación, calcula el residuo medio (real - esperado) de
    cada equipo en cada franja y le resta el ruido esperado. Devuelve las varianzas reales (tau²) de lo
    producido y de lo concedido, y la varianza de un residuo individual (s2)."""
    gf, ga, allr = {}, {}, []
    nt = len(pos)
    for m, e in zip(played, E):
        obs = value(m, key)
        if obs is None or key not in e:
            continue
        for s in (0, 1):
            t, o = (m["h"], m["a"]) if s == 0 else (m["a"], m["h"])
            tier = min(tiers - 1, (pos[o] - 1) * tiers // nt)
            rf = obs[s] - e[key][s]
            gf.setdefault((t, tier), []).append(rf)
            ga.setdefault((t, tier), []).append(obs[1 - s] - e[key][1 - s])
            allr.append(rf)
    if len(allr) < 20:
        return {"tf": 0.0, "ta": 0.0, "s2": 1.0}
    s2 = sum(r * r for r in allr) / len(allr)

    def est(g):
        v = [(sum(r) / len(r)) ** 2 - s2 / len(r) for r in g.values()]
        return max(0.0, sum(v) / len(v))
    return {"tf": est(gf), "ta": est(ga), "s2": s2}


def cross_tau_tested(played, E, key, pos, R=200, alpha=0.01, seed=1):
    """cross_tau con una prueba de permutación: se barajan los puestos de los equipos R veces y el efecto
    solo se usa si el real supera al del azar con p <= alpha (exigente porque se prueban 20 efectos)."""
    c = cross_tau(played, E, key, pos)
    rnd = random.Random(seed)
    names, vals = list(pos.keys()), list(pos.values())
    nf = na = 0
    for _ in range(R):
        rnd.shuffle(vals)
        z = cross_tau(played, E, key, dict(zip(names, vals)))
        nf += z["tf"] >= c["tf"]
        na += z["ta"] >= c["ta"]
    c["pf"], c["pa"] = (nf + 1) / (R + 1), (na + 1) / (R + 1)
    if c["tf"] <= 0 or c["pf"] > alpha:
        c["tf"] = 0.0
    if c["ta"] <= 0 or c["pa"] > alpha:
        c["ta"] = 0.0
    return c


# ----------------------------------------------------------------- clasificación y simulación
def xpts(xh, xa, K=10):
    """Puntos esperados de cada equipo según el xG del partido."""
    p1, p2 = pmf(xh, K), pmf(xa, K)
    w = sum(p1[x] * p2[y] for x in range(K + 1) for y in range(x))
    l = sum(p1[x] * p2[y] for y in range(K + 1) for x in range(y))
    dr = sum(p1[x] * p2[x] for x in range(K + 1))
    s = w + l + dr
    return (3 * w + dr) / s, (3 * l + dr) / s


def h2h(grp, G):
    pt = {t: 0 for t in grp}
    dg = {t: 0 for t in grp}
    for t in grp:
        for u in grp:
            r = G[t][u] if t != u else None
            if r is None:
                continue
            x, y = r
            dg[t] += x - y
            dg[u] += y - x
            if x > y:
                pt[t] += 3
            elif x < y:
                pt[u] += 3
            else:
                pt[t] += 1
                pt[u] += 1
    return pt, dg


def h2h_away(grp, G):
    """Puntos y goles marcados fuera de casa en los partidos entre los equipos del grupo."""
    pt = {t: 0 for t in grp}
    aw = {t: 0 for t in grp}
    for t in grp:
        for u in grp:
            r = G[t][u] if t != u else None
            if r is None:
                continue
            x, y = r
            aw[u] += y
            if x > y:
                pt[t] += 3
            elif x < y:
                pt[u] += 3
            else:
                pt[t] += 1
                pt[u] += 1
    return pt, aw


def rank(n, pts, gd, gf, G, rnd=None, rule="h2h"):
    """Orden final.
    rule='h2h' (LaLiga, art. 10 RFEF): entre dos, diferencia de goles en sus partidos; entre más de dos, puntos
    y luego diferencia de goles en la mini-liga entre ellos; después diferencia de goles general y goles a favor.
    rule='gd' (Premier League): diferencia de goles, goles a favor y después puntos y goles fuera en los partidos
    entre ellos. En los dos casos el último criterio (juego limpio o partido de desempate) se sustituye por sorteo."""
    tie = (lambda t: rnd.random()) if rnd else (lambda t: 0)
    if rule == "gd":
        order = sorted(range(n), key=lambda t: (-pts[t], -gd[t], -gf[t]))
        key = lambda t: (pts[t], gd[t], gf[t])
        out, k = [], 0
        while k < n:
            e = k
            while e + 1 < n and key(order[e + 1]) == key(order[k]):
                e += 1
            grp = order[k:e + 1]
            if len(grp) > 1:
                pt, aw = h2h_away(grp, G)
                grp = sorted(grp, key=lambda t: (-pt[t], -aw[t], tie(t)))
            out += grp
            k = e + 1
        return out
    order = sorted(range(n), key=lambda t: -pts[t])
    out = []
    k = 0
    while k < n:
        e = k
        while e + 1 < n and pts[order[e + 1]] == pts[order[k]]:
            e += 1
        grp = order[k:e + 1]
        if len(grp) > 1:
            pt, dg = h2h(grp, G)
            if len(grp) == 2:
                grp = sorted(grp, key=lambda t: (-dg[t], -gd[t], -gf[t], tie(t)))
            else:
                grp = sorted(grp, key=lambda t: (-pt[t], -dg[t], -gd[t], -gf[t], tie(t)))
        out += grp
        k = e + 1
    return out


def standings(played, teams, rule="h2h"):
    n = len(teams)
    ix = {t: k for k, t in enumerate(teams)}
    rows = [{"t": t, "pj": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "pts": 0, "xpts": 0.0, "xn": 0, "form": ""}
            for t in teams]
    G = [[None] * n for _ in range(n)]
    for m in played:
        i, j = ix[m["h"]], ix[m["a"]]
        x, y = m["hg"], m["ag"]
        G[i][j] = (x, y)
        for t, f, c in ((i, x, y), (j, y, x)):
            r = rows[t]
            r["pj"] += 1
            r["gf"] += f
            r["ga"] += c
            if f > c:
                r["w"] += 1
                r["pts"] += 3
                r["form"] += "W"
            elif f == c:
                r["d"] += 1
                r["pts"] += 1
                r["form"] += "D"
            else:
                r["l"] += 1
                r["form"] += "L"
        if m.get("xg"):
            xh, xa = xpts(*m["xg"])
            rows[i]["xpts"] += xh
            rows[j]["xpts"] += xa
            rows[i]["xn"] += 1
            rows[j]["xn"] += 1
    order = rank(n, [r["pts"] for r in rows], [r["gf"] - r["ga"] for r in rows], [r["gf"] for r in rows], G, rule=rule)
    out = []
    for p, t in enumerate(order):
        r = rows[t]
        r["pos"] = p + 1
        r["form"] = r["form"][-5:]
        out.append(r)
    return out


def pois(lam, rnd):
    u = rnd.random()
    k = 0
    q = math.exp(-lam)
    c = q
    while u > c and k < 20:
        k += 1
        q *= lam / k
        c += q
    return k


def dc_sample(lh, la, rho, rnd):
    if not rho:
        return pois(lh, rnd), pois(la, rnd)
    t = (max(1 - lh * la * rho, 0.0), max(1 + lh * rho, 0.0), max(1 + la * rho, 0.0), max(1 - rho, 0.0))
    tmax = max(1.0, *t)
    while True:
        x, y = pois(lh, rnd), pois(la, rnd)
        w = t[2 * x + y] if (x < 2 and y < 2) else 1.0
        if rnd.random() * tmax <= w:
            return x, y


def simulate(p, teams, played, pending, sims=5000, seed=2026, drift=0.08, rule="h2h", ntop=4, nrel=3, neu=6):
    """Simula los partidos pendientes muchas veces, sorteando también la fuerza de cada equipo.

    drift añade una variación extra (desviación en escala logarítmica) porque la fuerza de los equipos
    cambia a lo largo de la temporada: lesiones, entrenadores, fichajes de invierno."""
    n = len(teams)
    ix = p["ix"]
    pts0, gd0, gf0 = [0] * n, [0] * n, [0] * n
    G0 = [[None] * n for _ in range(n)]
    for m in played:
        i, j = ix[m["h"]], ix[m["a"]]
        x, y = m["hg"], m["ag"]
        G0[i][j] = (x, y)
        gf0[i] += x
        gf0[j] += y
        gd0[i] += x - y
        gd0[j] += y - x
        if x > y:
            pts0[i] += 3
        elif x < y:
            pts0[j] += 3
        else:
            pts0[i] += 1
            pts0[j] += 1
    sched = [(ix[f["h"]], ix[f["a"]]) for f in pending]
    rnd = random.Random(seed)
    rho = p.get("rho", 0.0)
    sa = [math.sqrt(v + drift * drift) for v in p["va"]]
    sd = [math.sqrt(v + drift * drift) for v in p["vd"]]
    s_mu, s_eta = math.sqrt(p["va0"]), math.sqrt(p["vh0"] + p["va0"])
    pos = [[0] * n for _ in range(n)]
    ptsl = [[] for _ in range(n)]
    for _ in range(sims):
        mu = p["mu"] + rnd.gauss(0, s_mu)
        eta = p["eta"] + rnd.gauss(0, s_eta)
        a = [p["a"][t] + rnd.gauss(0, sa[t]) for t in range(n)]
        d = [p["d"][t] + rnd.gauss(0, sd[t]) for t in range(n)]
        pts, gd, gf = pts0[:], gd0[:], gf0[:]
        G = [row[:] for row in G0]
        for i, j in sched:
            x, y = dc_sample(math.exp(mu + eta + a[i] - d[j]), math.exp(mu + a[j] - d[i]), rho, rnd)
            G[i][j] = (x, y)
            gf[i] += x
            gf[j] += y
            gd[i] += x - y
            gd[j] += y - x
            if x > y:
                pts[i] += 3
            elif x < y:
                pts[j] += 3
            else:
                pts[i] += 1
                pts[j] += 1
        for r, t in enumerate(rank(n, pts, gd, gf, G, rnd, rule)):
            pos[t][r] += 1
            ptsl[t].append(pts[t])
    out = []
    for t in range(n):
        s = sorted(ptsl[t])
        q = lambda f: s[min(len(s) - 1, int(f * len(s)))]
        pr = [c / sims for c in pos[t]]
        out.append({"t": teams[t], "mean": sum(s) / sims, "p10": q(0.1), "p90": q(0.9), "pos": pr,
                    "ch": pr[0], "t4": sum(pr[:ntop]), "t6": sum(pr[:neu]), "rel": sum(pr[n - nrel:])})
    return out


# ----------------------------------------------------------------- evaluación
def ll(p, o):
    return -math.log(max(p[o], 1e-9))


def brier(p, o):
    return sum((p[k] - (1 if k == o else 0)) ** 2 for k in range(3))


def walk_forward_goals(played, teams, cfg=None, min_train=30, step=1):
    """Cada partido se predice con un modelo ajustado solo con los partidos de días anteriores (el modelo se
    reajusta cuando hay al menos `step` partidos nuevos, para acotar el tiempo de cálculo a final de temporada)."""
    out, p, last = [], None, -10 ** 9
    for d in sorted({m["date"] for m in played}):
        train = [m for m in played if m["date"] < d]
        if len(train) < min_train:
            continue
        if p is None or len(train) - last >= step:
            p = fit_goals(train, teams, cfg, ref=d)
            last = len(train)
        out += [(m, predict_goals(p, m["h"], m["a"])) for m in played if m["date"] == d]
    return out


def walk_forward_stats(played, teams, min_train=30, step=8):
    """Totales esperados de cada estadística, prediciendo cada partido solo con los anteriores.
    Los modelos se reajustan cada vez que hay al menos `step` partidos nuevos."""
    out, models, base, last = {}, None, None, -10 ** 9
    for d in sorted({m["date"] for m in played}):
        train = [m for m in played if m["date"] < d]
        if len(train) < min_train:
            continue
        if len(train) - last >= step:
            models = {k: fit_stat(train, teams, k) for k, _ in STATS}
            base = {k: mean(sum(m[k]) for m in train if m.get(k) is not None) for k, _ in STATS}
            last = len(train)
        for m in played:
            if m["date"] != d:
                continue
            i, j = teams.index(m["h"]), teams.index(m["a"])
            tt = {k: stat_total(p, i, j) for k, p in models.items() if p}
            out[mkey(m["h"], m["a"])] = {"pred": {k: t[0] for k, t in tt.items()}, "sd": {k: math.sqrt(t[1]) for k, t in tt.items()},
                                         "base": base}
    return out


def agg(rows):
    """Resumen de un conjunto de predicciones evaluadas (dicts con p, o y mk opcional)."""
    if not rows:
        return None
    res = {"n": len(rows), "acc": mean(1.0 if max(range(3), key=lambda k: r["p"][k]) == r["o"] else 0.0 for r in rows),
           "ll": mean(ll(r["p"], r["o"]) for r in rows), "br": mean(brier(r["p"], r["o"]) for r in rows)}
    wm = [r for r in rows if r.get("mk")]
    if wm:
        diffs = [ll(r["p"], r["o"]) - ll(r["mk"], r["o"]) for r in wm]
        dm = mean(diffs)
        se = math.sqrt(sum((x - dm) ** 2 for x in diffs) / (len(diffs) - 1) / len(diffs)) if len(diffs) > 1 else None
        blend = [[(a + b) / 2 for a, b in zip(r["p"], r["mk"])] for r in wm]
        res.update(nm=len(wm), llm=mean(ll(r["mk"], r["o"]) for r in wm),
                   brm=mean(brier(r["mk"], r["o"]) for r in wm),
                   accm=mean(1.0 if max(range(3), key=lambda k: r["mk"][k]) == r["o"] else 0.0 for r in wm),
                   llb=mean(ll(b, r["o"]) for b, r in zip(blend, wm)),
                   llmod=mean(ll(r["p"], r["o"]) for r in wm), dll=dm, dse=se)
    res["pd"] = mean(r["p"][1] for r in rows)
    res["fd"] = mean(1.0 if r["o"] == 1 else 0.0 for r in rows)
    return res


def calibration(rows, bins=5):
    acc = [[0.0, 0.0, 0] for _ in range(bins)]
    for r in rows:
        for k in range(3):
            b = min(bins - 1, int(r["p"][k] * bins))
            acc[b][0] += r["p"][k]
            acc[b][1] += 1.0 if r["o"] == k else 0.0
            acc[b][2] += 1
    return [{"lo": b / bins, "hi": (b + 1) / bins, "p": s / c, "f": h / c, "n": c} for b, (s, h, c) in enumerate(acc) if c]


def backtest_summary(wf):
    rows = []
    for m, pr in wf:
        o = outcome(m["hg"], m["ag"])
        mo = implied(m.get("ou"))
        rows.append({"p": pr["p"], "o": o, "mk": implied(m.get("odds")), "j": m.get("j"),
                     "ov": pr["ou"][2], "mov": mo[0] if mo else None, "tot": m["hg"] + m["ag"]})
    res = agg(rows) or {}
    ou = [r for r in rows if r["mov"] is not None]
    if ou:
        bl = lambda p, y: -math.log(max(p if y else 1 - p, 1e-9))
        res["ou"] = {"n": len(ou), "ll": mean(bl(r["ov"], r["tot"] > 2) for r in ou),
                     "llm": mean(bl(r["mov"], r["tot"] > 2) for r in ou)}
    res["calib"] = calibration(rows)
    res["by_j"] = []
    for j in sorted({r["j"] for r in rows if r["j"]}):
        a = agg([r for r in rows if r["j"] == j])
        a["j"] = j
        res["by_j"].append(a)
    return res


# ----------------------------------------------------------------- registro de predicciones
def entry_sd(pr, sd):
    """Desviación típica de un partido de cada total: la de las estadísticas y la de los goles."""
    out = {k: v for k, v in (sd or {}).items() if v is not None}
    if pr.get("V"):
        out["g"] = math.sqrt(pr["V"][2])
    return {k: round(v, 2) for k, v in out.items()}


def score_for(pr, p):
    """Marcador previsto: el más probable entre los que dan el resultado favorito de p."""
    fav = max(range(3), key=lambda k: p[k])
    c = next((c for c in pr.get("top", []) if outcome(c[0], c[1]) == fav), None)
    c = c or pr["fs"]
    return [c[0], c[1], round(c[2], 4)]


def make_entry(pr, st, base, j, d, made, bf, mk=None, mo=None, pc=None, ref=None, sd=None):
    r4 = lambda x: round(x, 4)
    return {"j": j, "date": d, "made": made, "bf": bf, "v": VERSION,
            "p": [r4(x) for x in pr["p"]], "e": [round(x, 3) for x in pr["e"]],
            "o25": r4(pr["ou"][2]), "bb": r4(pr["bb"]),
            "fs": [pr["fs"][0], pr["fs"][1], r4(pr["fs"][2])], "sd": entry_sd(pr, sd),
            "st": {k: round(v, 2) for k, v in (st or {}).items()},
            "sb": {k: round(v, 2) for k, v in (base or {}).items() if v is not None},
            "mk": [r4(x) for x in mk] if mk else None, "mo": r4(mo) if mo is not None else None,
            "pc": [r4(x) for x in pc] if pc else None, "ref": ref}


def update_log(log, played, pending, gm, sms, wf_goals, wf_stats, today, horizon=10, blend=None, reff=None):
    """Añade predicciones al registro sin tocar nunca las de partidos ya jugados.

    - Partidos jugados sin predicción guardada: se reconstruyen con la prueba retrospectiva (bf=True).
    - Partidos pendientes con fecha entre hoy y hoy+horizon: se actualizan en cada ejecución hasta el día
      del partido; después quedan congelados."""
    E = log.setdefault("entries", {})
    for m, pr in wf_goals:
        k = mkey(m["h"], m["a"])
        ws = wf_stats.get(k, {})
        if k not in E:
            E[k] = make_entry(pr, ws.get("pred"), ws.get("base"), m.get("j"), m["date"], m["date"], True, sd=ws.get("sd"))
        else:
            # entradas de versiones anteriores, sin rango ni marcador: se completan con la prueba retrospectiva,
            # que solo usa partidos anteriores; la media y las probabilidades guardadas no se tocan
            e = E[k]
            if "sd" not in e:
                e["sd"] = entry_sd(pr, ws.get("sd"))
            if "fs" not in e:
                e["fs"] = score_for(pr, e["p"])
    lim = (date.fromisoformat(today) + timedelta(days=horizon)).isoformat()
    base = {k: mean(sum(m[k]) for m in played if m.get(k) is not None) for k, _ in STATS}
    for f in pending:
        if not (today <= f["date"] <= lim):
            continue
        i, j = gm["ix"][f["h"]], gm["ix"][f["a"]]
        pr = predict_goals(gm, f["h"], f["a"])
        tt = {k: stat_total(p, i, j) for k, p in sms.items() if p}
        st = {k: t[0] for k, t in tt.items()}
        sd = {k: math.sqrt(t[1]) for k, t in tt.items()}
        rf = (reff or {}).get(mkey(f["h"], f["a"])) or {}
        for k, v in rf.items():
            if k in st:
                st[k] *= v
                sd[k] *= math.sqrt(v)  # el árbitro multiplica la media y la varianza
        mo = implied(f.get("ou"))
        mk = implied(f.get("odds"))
        pc = pool(pr["p"], mk, blend) if (mk and blend is not None) else None
        E[mkey(f["h"], f["a"])] = make_entry(pr, st, base, f["j"], f["date"], today, False, mk, mo[0] if mo else None,
                                             pc, f.get("ref"), sd)
    log["version"] = VERSION
    log["updated"] = today
    return log


RANGE_KEYS = ["g", "xg", "s", "st", "c", "f", "y", "r"]


def range_of(m, sd):
    """El rango que enseña la página: media ± una desviación típica de un partido, con un decimal."""
    return round(max(m - sd, 0.0), 1), round(m + sd, 1)


def _cdf(m, V, k):
    """P(X <= k) para un recuento con media m y varianza V: binomial negativa si varía más que un Poisson, normal si varía menos
    (salvo medias pequeñas) y Poisson en el resto. Igual que pOver en app.js."""
    if k < 0:
        return 0.0
    if V > m * 1.02:
        r = m * m / (V - m)
        q = m / (r + m)
        pk = (1 - q) ** r
        c = pk
        for i in range(1, k + 1):
            pk *= (i - 1 + r) / i * q
            c += pk
        return min(1.0, c)
    if V >= m * 0.98 or m < 5:  # con medias pequeñas (rojas) la normal se equivoca: Poisson
        pk = math.exp(-m)
        c = pk
        for i in range(1, k + 1):
            pk *= m / i
            c += pk
        return min(1.0, c)
    return 0.5 * (1 + math.erf((k + 0.5 - m) / math.sqrt(2 * V)))


def coverage(m, sd, lo, hi, cont=False):
    """Probabilidad, según el propio modelo, de que el total real caiga dentro de [lo, hi]."""
    V = max(sd * sd, 1e-9)
    if m <= 0:
        return 1.0 if lo <= 0 else 0.0
    if cont:  # xG: lognormal con esa media y varianza
        s2 = math.log(1 + V / (m * m))
        mu, s = math.log(m) - s2 / 2, math.sqrt(s2)
        F = lambda x: 0.0 if x <= 0 else 0.5 * (1 + math.erf((math.log(x) - mu) / (s * math.sqrt(2))))
        return max(0.0, F(hi) - F(lo))
    a, b = math.ceil(lo - 1e-9), math.floor(hi + 1e-9)
    return 0.0 if b < a else max(0.0, _cdf(m, V, b) - _cdf(m, V, a - 1))


def ranges_eval(e, m):
    """Para cada total del partido: [media, desde, hasta, real, probabilidad de caer dentro según el modelo]."""
    sd, means = e.get("sd") or {}, dict(e.get("st") or {})
    if e.get("e"):
        means["g"] = e["e"][0] + e["e"][1]
    out = {}
    for k in RANGE_KEYS:
        obs = m["hg"] + m["ag"] if k == "g" else (sum(m[k]) if m.get(k) is not None else None)
        if obs is None or k not in means or not sd.get(k):
            continue
        lo, hi = range_of(means[k], sd[k])
        out[k] = [round(means[k], 2), lo, hi, round(obs, 2), round(coverage(means[k], sd[k], lo, hi, k == "xg"), 3)]
    return out


def evaluate_log(log, played):
    E = log.get("entries", {})
    rows = []
    for m in played:
        e = E.get(mkey(m["h"], m["a"]))
        if not e:
            continue
        o = outcome(m["hg"], m["ag"])
        r = {"h": m["h"], "a": m["a"], "j": m.get("j"), "d": m["date"], "hg": m["hg"], "ag": m["ag"], "o": o,
             "p": e["p"], "mk": implied(m.get("odds")), "bf": e.get("bf", False), "made": e.get("made"),
             "o25": e.get("o25"), "tot": m["hg"] + m["ag"], "st": {}, "pc": e.get("pc"),
             "fs": e.get("fs"), "bbp": e.get("bb"), "rg": ranges_eval(e, m)}
        for k, v in (e.get("st") or {}).items():
            obs = m.get(k)
            if obs is not None:
                r["st"][k] = [v, sum(obs), (e.get("sb") or {}).get(k)]
        odds = m.get("odds")
        if odds:
            for key, pp in (("bet", e["p"]), ("betc", e.get("pc"))):
                if not pp:
                    continue
                edges = [pp[k] * odds[k] - 1 for k in range(3)]
                kb = max(range(3), key=lambda k: edges[k])
                if edges[kb] > 0.05:
                    r[key] = [kb, odds[kb], round(odds[kb] - 1 if kb == o else -1.0, 3)]
        rows.append(r)
    real = [r for r in rows if not r["bf"]]
    out = {"n": len(rows), "nreal": len(real), "all": agg(rows), "real": agg(real), "calib": calibration(rows),
           "by_j": [], "rows": sorted(rows, key=lambda r: r["d"], reverse=True)}
    for j in sorted({r["j"] for r in rows if r["j"]}):
        rj = [r for r in rows if r["j"] == j]
        a = agg(rj)
        a["j"] = j
        a["real"] = sum(1 for r in rj if not r["bf"])
        out["by_j"].append(a)
    for key, okey in (("bet", "bets"), ("betc", "betsc")):
        bets = [r[key] for r in rows if key in r]
        if bets:
            pr = [b[2] for b in bets]
            mp = mean(pr)
            sd = math.sqrt(sum((x - mp) ** 2 for x in pr) / (len(pr) - 1)) if len(pr) > 1 else 0.0
            out[okey] = {"n": len(pr), "won": sum(1 for x in pr if x > 0), "profit": sum(pr), "roi": mp,
                         "se": sd / math.sqrt(len(pr))}
    comb = [{"p": r["pc"], "o": r["o"], "mk": r["mk"]} for r in rows if r.get("pc")]
    out["comb"] = agg(comb)
    st = {}
    for k, _ in STATS:
        tr = [r["st"][k] for r in rows if k in r["st"]]
        if tr:
            st[k] = {"n": len(tr), "mae": mean(abs(p - o) for p, o, _ in tr),
                     "maeb": mean(abs(b - o) for p, o, b in tr if b is not None),
                     "bias": mean(p - o for p, o, _ in tr)}
    out["stats"] = st
    return out


# ----------------------------------------------------------------- tendencias
def p_over(m, V, L):
    """Probabilidad de superar L con media m y varianza V (binomial negativa o Poisson)."""
    k = math.floor(L)
    if k < 0:
        return 1.0
    if V > m * 1.02:
        r = m * m / (V - m)
        q = m / (r + m)
        pk = (1 - q) ** r
        c = pk
        for i in range(1, k + 1):
            pk *= (i - 1 + r) / i * q
            c += pk
    else:
        pk = math.exp(-m)
        c = pk
        for i in range(1, k + 1):
            pk *= m / i
            c += pk
    return min(1.0, max(0.0, 1 - c))


TREND_KEYS = ["s", "st", "c", "y", "f"]
TREND_WIN = 2  # rivales parecidos: a ±2 puestos en la clasificación


def _series(ms, t, k, total=False):
    """Valores de la estadística k del equipo t (o del total de sus partidos), en orden: (valor, en casa, rival)."""
    out = []
    for x in ms:
        if t not in (x["h"], x["a"]) or not x.get(k):
            continue
        s = 0 if x["h"] == t else 1
        out.append((x[k][0] + x[k][1] if total else x[k][s], s == 0, x["a"] if s == 0 else x["h"]))
    return out


def _near(pos, o, ex, win=TREND_WIN):
    return {u for u in pos if u not in (o, ex) and abs(pos[u] - pos[o]) <= win}


def _classify(series, cross, same, m, V, strict=True):
    """Tendencia clara o nada (strict=False es la definición flexible de referencia: la excepción puede ser
    cualquier partido y basta con que la racha llegue al nivel que espera el modelo).

    series: los últimos valores de cada serie, del más antiguo al más reciente (una serie para un equipo; dos para
    el total del partido, una por equipo).
    - 'muy': los 5 últimos partidos más allá de la línea; también todos contra rivales parecidos y en el mismo campo.
    - 'una': los 4 últimos seguidos (la excepción solo puede ser el más antiguo de los 5); todos contra rivales
      parecidos y como mucho una excepción en el mismo campo.
    En los dos casos la línea es la de la propia racha y el modelo tiene que darle un 50 % o menos: si el modelo ya
    la ve probable, no es una tendencia sino lo esperado. Rivales parecidos y mismo campo necesitan 2 partidos o más."""
    for tier, n_last, miss in (("muy", 5, 0), ("una", 4, 1)):
        for over in (True, False):
            if strict:
                vals = [v for s in series for v in s[-n_last:]]
                L = (min(vals) - 0.5) if over else (max(vals) + 0.5)
            else:
                vals = sorted(v for s in series for v in s[-5:])
                e = 5 - n_last
                L = (vals[e] - 0.5) if over else (vals[-1 - e] + 0.5)
                if (over and L + 0.5 < m) or (not over and L - 0.5 > m):
                    continue
            if L < 0.5:
                continue
            hit = (lambda L: lambda v: v > L)(L) if over else (lambda L: lambda v: v < L)(L)
            pm = p_over(m, V, L)
            pm = pm if over else 1 - pm
            if strict and pm > 0.5:
                continue
            if len(cross) < 2 or not all(hit(v) for v in cross):
                continue
            if len(same) < 2 or sum(1 for v in same if not hit(v)) > miss:
                continue
            return {"over": over, "tier": tier, "L": L, "pm": pm}
    return None


def trend_candidates(train, pos, models, h, a, strict=True, ref=None):
    """Tendencias claras de un partido h-a con los datos de train y la clasificación pos."""
    out = []
    for k in TREND_KEYS:
        p = models.get(k)
        if not p:
            continue
        ix = p["ix"]
        for side, t, o, home in (("H", h, a, True), ("A", a, h, False)):
            ser = _series(train, t, k)
            if len(ser) < 5:
                continue
            last = [v for v, _, _ in ser[-5:]]
            near = _near(pos, o, t)
            cross = [v for v, _, op in ser if op in near]
            same = [v for v, hm, _ in ser if hm == home][-3:]
            m, V, _ = stat_pred(p, ix[t], ix[o], 1 if home else 0)
            rf = (ref or {}).get(k)
            if rf:
                m, V = m * rf, V * rf
            c = _classify([last], cross, same, m, V, strict)
            if c:
                out.append(dict(side=side, k=k, m=m, V=V, rf=rf, last=last, series=[last], cross=cross, same=same, **c))
        sh, sa = _series(train, h, k, True), _series(train, a, k, True)
        if len(sh) >= 5 and len(sa) >= 5:
            series = [[v for v, _, _ in sh[-5:]], [v for v, _, _ in sa[-5:]]]
            last = series[0] + series[1]
            nh, na = _near(pos, a, h), _near(pos, h, a)
            cross = [v for v, _, op in sh if op in nh] + [v for v, _, op in sa if op in na]
            same = [v for v, hm, _ in sh if hm][-3:] + [v for v, hm, _ in sa if not hm][-3:]
            m, V, _ = stat_total(p, ix[h], ix[a])
            rf = (ref or {}).get(k)
            if rf:
                m, V = m * rf, V * rf
            c = _classify(series, cross, same, m, V, strict)
            if c:
                out.append(dict(side="T", k=k, m=m, V=V, rf=rf, last=last, series=series, cross=cross, same=same, **c))
    return out


def trend_backtest(played, teams, step=8, strict=True):
    """Cada tendencia que habría detectado el buscador esta temporada, con los datos anteriores a su fecha
    (clasificación de ese día incluida), y si se cumplió en el partido siguiente."""
    cases, models, last = [], None, -10 ** 9
    for d in sorted({m["date"] for m in played}):
        train = [m for m in played if m["date"] < d]
        if len(train) < 30:
            continue
        if len(train) - last >= step:
            models = {k: fit_stat(train, teams, k) for k in TREND_KEYS}
            last = len(train)
        pos = {r["t"]: r["pos"] for r in standings(train, teams)}
        for m in (x for x in played if x["date"] == d):
            for c in trend_candidates(train, pos, models, m["h"], m["a"], strict):
                ob = m.get(c["k"])
                if not ob:
                    continue
                obs = ob[0] + ob[1] if c["side"] == "T" else ob[0 if c["side"] == "H" else 1]
                pm = c["pm"]
                cases.append({"d": d, "h": m["h"], "a": m["a"], "side": c["side"], "k": c["k"], "over": c["over"],
                              "tier": c["tier"], "L": c["L"], "obs": obs, "hit": (obs > c["L"]) if c["over"] else (obs < c["L"]),
                              "pm": pm})
    summ = {}
    for c in cases:
        for key in (c["tier"] + ("+" if c["over"] else "-"), "all"):
            s = summ.setdefault(key, [0, 0, 0.0])
            s[0] += 1
            s[1] += c["hit"]
            s[2] += c["pm"]
    return {"summ": {k: {"n": n, "hit": h / n, "model": p / n} for k, (n, h, p) in summ.items()}, "cases": cases}


# ----------------------------------------------------------------- aprendizaje
def paired(a, b):
    """Media y error típico de la diferencia emparejada a - b."""
    d = [x - y for x, y in zip(a, b)]
    if len(d) < 2:
        return None, None
    m = sum(d) / len(d)
    return m, math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1) / len(d))


def select_config(played, teams, grid, prev=None, step=1):
    """Prueba cada configuración del modelo de goles con la prueba retrospectiva (cada partido predicho solo con
    los anteriores) y elige la de mejor log-loss. Para no cambiar por ruido, se mantiene la actual (la del día
    anterior o, si no hay, la primera) salvo que otra la mejore en más de un error típico en los mismos partidos."""
    res = {}
    for key, name, cfg in grid:
        wf = walk_forward_goals(played, teams, cfg, step=step)
        lls = [ll(pr["p"], outcome(m["hg"], m["ag"])) for m, pr in wf]
        res[key] = {"key": key, "name": name, "cfg": cfg, "wf": wf, "lls": lls, "ll": mean(lls)}
    keys = [k for k, _, _ in grid]
    cur = prev if prev in res else keys[0]
    ok = [k for k in keys if res[k]["ll"] is not None]
    if not ok:
        return cur, res, "Todavía no hay partidos suficientes para comparar configuraciones."
    best = min(ok, key=lambda k: res[k]["ll"])
    chosen, why = cur, "se mantiene"
    if best != cur and res[cur]["ll"] is not None:
        dm, se = paired(res[best]["lls"], res[cur]["lls"])
        if dm is not None and dm < -max(se, 0.002):
            chosen, why = best, "cambia"
    for k in ok:
        dm, se = paired(res[k]["lls"], res[chosen]["lls"])
        res[k]["d"], res[k]["se"] = dm, se
    return chosen, res, why


def pool(p, mk, a):
    """Combinación logarítmica de dos predicciones: p elevado a a por mk elevado a 1-a, normalizado."""
    q = [max(x, 1e-9) ** a * max(y, 1e-9) ** (1 - a) for x, y in zip(p, mk)]
    t = sum(q)
    return [x / t for x in q]


def learn_blend(wf):
    """Aprende cuánto pesa el modelo frente al mercado: el peso a que mejor predice, en la prueba retrospectiva,
    los partidos con cuotas de cierre (a=0 es solo el mercado; a=1, solo el modelo)."""
    rows = [(pr["p"], implied(m["odds"]), outcome(m["hg"], m["ag"])) for m, pr in wf if m.get("odds")]
    if len(rows) < 20:
        return {"a": 0.0 if rows else 1.0, "n": len(rows), "fit": False}
    grid = [i / 20 for i in range(21)]
    curve = {a: mean(ll(pool(p, mk, a), o) for p, mk, o in rows) for a in grid}
    a = min(grid, key=lambda x: curve[x])
    dm, se = paired([ll(pool(p, mk, a), o) for p, mk, o in rows], [ll(mk, o) for p, mk, o in rows])
    return {"a": a, "n": len(rows), "fit": True, "ll": curve[a], "llm": curve[0.0], "llmod": curve[1.0], "d": dm, "se": se,
            "curve": [[x, round(curve[x], 4)] for x in grid]}


REF_KEYS = ["y", "f"]


def referee_effects(played, E, key, phi, min_refs=5):
    """Cuánto se aparta cada árbitro de lo esperado en la estadística key (total del partido).
    Bayes empírico gamma-Poisson: el factor de cada árbitro se acerca a 1 según sus partidos y según cuánto
    se diferencian de verdad los árbitros entre sí. Si los datos no muestran diferencias reales, todos valen 1."""
    agg_ = {}
    for m, e in zip(played, E):
        r, v, ex = m.get("ref"), m.get(key), e.get(key)
        if not r or v is None or not ex:
            continue
        a = agg_.setdefault(r, [0.0, 0.0, 0])
        a[0] += v[0] + v[1]
        a[1] += ex[0] + ex[1]
        a[2] += 1
    if len(agg_) < min_refs:
        return None
    rs = [(o / e, e) for o, e, _ in agg_.values() if e > 0]
    W = sum(e for _, e in rs)
    mr = sum(r * e for r, e in rs) / W
    var = sum(e * (r - mr) ** 2 for r, e in rs) / W
    noise = phi * len(rs) / W
    tau2 = max(0.0, var - noise)
    alpha = 1 / tau2 if tau2 > 1e-6 else None
    refs = {r: {"f": ((alpha + o / phi) / (alpha + e / phi)) if alpha else 1.0, "n": n, "o": o, "e": e}
            for r, (o, e, n) in agg_.items()}
    return {"tau": math.sqrt(tau2), "refs": refs}


def referee_backtest(played, teams, min_train=40, step=8):
    """¿Mejora el árbitro la predicción? Para cada partido se estima el factor de su árbitro solo con partidos
    anteriores y se compara el error del total con y sin él."""
    out = {k: [] for k in REF_KEYS}
    models, facs, last = None, None, -10 ** 9
    for d in sorted({m["date"] for m in played}):
        train = [m for m in played if m["date"] < d]
        if len(train) < min_train:
            continue
        if len(train) - last >= step:
            models = {k: fit_stat(train, teams, k) for k in REF_KEYS}
            Et = [{k: [math.exp(lin(p, p["ix"][m["h"]], p["ix"][m["a"]], 1)[0]),
                       math.exp(lin(p, p["ix"][m["a"]], p["ix"][m["h"]], 0)[0])] for k, p in models.items() if p}
                  for m in train]
            facs = {k: referee_effects(train, Et, k, models[k]["phi"]) for k in REF_KEYS if models.get(k)}
            last = len(train)
        for m in (x for x in played if x["date"] == d):
            for k in REF_KEYS:
                p, fe = models.get(k), facs.get(k)
                if not p or not m.get(k) or not m.get("ref"):
                    continue
                base = stat_total(p, p["ix"][m["h"]], p["ix"][m["a"]])[0]
                f = fe["refs"].get(m["ref"], {"f": 1.0})["f"] if fe else 1.0
                obs = sum(m[k])
                out[k].append((abs(base - obs), abs(base * f - obs)))
    res = {}
    for k, v in out.items():
        if v:
            dm, se = paired([b for _, b in v], [a for a, _ in v])
            res[k] = {"n": len(v), "mae": mean(a for a, _ in v), "maer": mean(b for _, b in v), "d": dm, "se": se}
    return res


# ----------------------------------------------------------------- apuestas del usuario
# Cada apuesta tiene una o varias patas (una combinada tiene varias). Tipos de pata:
#   {"tipo": "mas" | "menos", "estadistica": "tiros", "equipo": "local" | "visitante" | "total", "linea": 13.5}
#   {"tipo": "ganador", "estadistica": "corners", "equipo": "local" | "visitante" | "empate"}   (quién tiene más)
#   {"tipo": "resultado", "equipo": "local" | "empate" | "visitante"}
BET_STATS = {"goles": "g", "tiros": "s", "tiros a puerta": "st", "corners": "c", "córners": "c", "faltas": "f",
             "amarillas": "y", "rojas": "r", "xg": "xg"}
_SIDE = {"local": 0, "empate": 1, "visitante": 2}


def _phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def leg_key(leg):
    return "g" if leg["tipo"] == "resultado" else BET_STATS[leg["estadistica"].strip().lower()]


def _pick(leg, v):
    return v[0] + v[1] if leg["equipo"] == "total" else v[0 if leg["equipo"] == "local" else 1]


def leg_outcome(leg, v):
    """'gana', 'pierde' o 'nula' con los valores reales [local, visitante] de su estadística.
    En «ganador» un empate en la estadística pierde (mercado de tres opciones), salvo que se apostara al empate."""
    t = leg["tipo"]
    if t in ("mas", "menos"):
        x, L = _pick(leg, v), leg["linea"]
        if x == L:
            return "nula"
        return "gana" if (x > L) == (t == "mas") else "pierde"
    d, w = v[0] - v[1], leg["equipo"]
    ok_ = d == 0 if w == "empate" else (d > 0 if w == "local" else d < 0)
    return "gana" if ok_ else "pierde"


def _leg_y(leg, v):
    """Cantidad que crece cuando la pata se acerca a cumplirse (None si no es monótona, como el empate)."""
    t, w = leg["tipo"], leg["equipo"]
    if t in ("mas", "menos"):
        x = _pick(leg, v)
        return x if t == "mas" else -x
    if w == "empate":
        return None
    return v[0] - v[1] if w == "local" else v[1] - v[0]


def leg_prob(leg, gm, sms, h, a):
    """Probabilidad de que la pata se cumpla según el modelo (sin contar la nula)."""
    ih, ia, k, t, w = gm["ix"][h], gm["ix"][a], leg_key(leg), leg["tipo"], leg["equipo"]
    if k == "g":
        M = score_matrix(gm, ih, ia)
        cells = [(x, y, q) for x, row in enumerate(M) for y, q in enumerate(row)]
        if t in ("mas", "menos"):
            L = leg["linea"]
            val = lambda x, y: x + y if w == "total" else (x if w == "local" else y)
            return sum(q for x, y, q in cells if (val(x, y) > L if t == "mas" else val(x, y) < L))
        return sum(q for x, y, q in cells if (x == y if w == "empate" else (x > y if w == "local" else x < y)))
    p = sms[k]
    mh, vh, _ = stat_pred(p, ih, ia, 1)
    ma, va, _ = stat_pred(p, ia, ih, 0)
    cov = p["rr"] * p["phi"] * math.sqrt(mh * ma)
    if t in ("mas", "menos"):
        m, V = (mh + ma, vh + va + 2 * cov) if w == "total" else ((mh, vh) if w == "local" else (ma, va))
        L = leg["linea"]
        up = p_over(m, V, L)
        if t == "mas":
            return up
        eq = p_over(m, V, L - 1) - up if float(L).is_integer() else 0.0
        return max(0.0, 1 - up - eq)
    mu, sd = mh - ma, math.sqrt(max(vh + va - 2 * cov, 1e-6))  # diferencia local − visitante, con corrección de continuidad
    if w == "local":
        return 1 - _phi((0.5 - mu) / sd)
    if w == "visitante":
        return _phi((-0.5 - mu) / sd)
    return _phi((0.5 - mu) / sd) - _phi((-0.5 - mu) / sd)


def _chol(R):
    n = len(R)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s_ = R[i][j] - sum(L[i][k] * L[j][k] for k in range(j))
            L[i][j] = math.sqrt(max(s_, 1e-9)) if i == j else s_ / L[j][j]
    return L


def joint_prob(ps, R, n=40000, seed=11):
    """Probabilidad de que se cumplan todas las patas: cada una con su probabilidad y unidas por una cópula normal
    con las correlaciones R (las patas de una combinada suelen ir juntas: quien saca más córners suele tirar más)."""
    if len(ps) == 1:
        return ps[0]
    from statistics import NormalDist
    nd = NormalDist()
    th = [nd.inv_cdf(min(max(1 - q, 1e-9), 1 - 1e-9)) for q in ps]
    L = _chol(R)
    rnd = random.Random(seed)
    hit = 0
    for _ in range(n):
        z = [rnd.gauss(0, 1) for _ in ps]
        if all(sum(L[i][j] * z[j] for j in range(i + 1)) > th[i] for i in range(len(ps))):
            hit += 1
    return hit / n


def leg_corr(legs, train, E):
    """Correlación entre las patas, con lo que se apartó cada partido anterior de lo que esperaba el modelo."""
    n = len(legs)
    R = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    res = []
    for leg in legs:
        k = leg_key(leg)
        r = []
        for m, e in zip(train, E):
            v = [m["hg"], m["ag"]] if k == "g" else m.get(k)
            if v is None or not e.get(k):
                r.append(None)
                continue
            yo, ye = _leg_y(leg, v), _leg_y(leg, e[k])
            r.append(None if yo is None or ye is None else yo - ye)
        res.append(r)
    for i in range(n):
        for j in range(i):
            pr = [(x, y) for x, y in zip(res[i], res[j]) if x is not None and y is not None]
            if len(pr) > 10:
                c = corr([x for x, _ in pr], [y for _, y in pr])
                R[i][j] = R[j][i] = max(-0.9, min(0.9, c))
    return R


def evaluate_bets(bets, played, pending, teams, cfg=None, gm_now=None, sms_now=None, blend=None):
    """Comprueba cada apuesta con el partido real y calcula lo que le daba el modelo antes del partido
    (ajustado solo con los partidos anteriores) o, si aún no se ha jugado, con el modelo de hoy. En el resultado (1X2)
    se usa lo aprendido frente al mercado (blend: peso del modelo; 0 es fiarse solo de las cuotas)."""
    byk = {(m["h"], m["a"]): m for m in played}
    pend = {(f["h"], f["a"]): f for f in pending}
    cache = {}
    out = []
    for n_, b in enumerate(bets):
        r = {"i": n_, "texto": b.get("texto", ""), "cuota": b["cuota"], "importe": b.get("importe", 15), "patas": [],
             "fecha": b.get("fecha")}
        try:
            h, a = [x.strip() for x in b["partido"].split("|")]
            if h not in teams or a not in teams:
                raise ValueError(f"equipo desconocido en «{b['partido']}»")
            r.update(h=h, a=a)
            m = byk.get((h, a))
            row = m or pend.get((h, a)) or {}
            legs = b["patas"]
            for leg in legs:
                leg_key(leg)  # valida la estadística
            if m:
                r.update(fecha=m["date"], j=m.get("j"))
                d = m["date"]
                if d not in cache:
                    train = [x for x in played if x["date"] < d]
                    g_ = fit_goals(train, teams, cfg, ref=d)
                    s_ = {k: fit_stat(train, teams, k) for k in ("s", "st", "c", "f", "y", "r", "xg")}
                    cache[d] = (train, g_, s_, expectations(train, g_, s_))
                train, g_, s_, E = cache[d]
                r["modelo"] = "antes"
            else:
                f = pend.get((h, a))
                if not f:
                    raise ValueError(f"no encuentro el partido {h}-{a}")
                r.update(fecha=f["date"], j=f.get("j"))
                if "hoy" not in cache:
                    cache["hoy"] = (played, gm_now, sms_now, expectations(played, gm_now, sms_now))
                train, g_, s_, E = cache["hoy"]
                r["modelo"] = "hoy"
            ps = []
            for leg in legs:
                k = leg_key(leg)
                q = {**leg, "k": k, "p": round(leg_prob(leg, g_, s_, h, a), 4)}
                mk = implied(row.get("odds")) if leg["tipo"] == "resultado" and blend is not None else None
                if mk:
                    q["pm"] = q["p"]
                    q["p"] = round(pool(predict_goals(g_, h, a)["p"], mk, blend)[_SIDE[leg["equipo"]]], 4)
                    q["src"] = "mercado" if blend == 0 else "combinada"
                if m:
                    v = [m["hg"], m["ag"]] if k == "g" else m.get(k)
                    q["obs"] = [round(x, 2) for x in v] if v else None
                    q["res"] = leg_outcome(leg, v) if v else None
                ps.append(q["p"])
                r["patas"].append(q)
            R = leg_corr(legs, train, E) if len(legs) > 1 else [[1.0]]
            r["p"] = round(joint_prob(ps, R), 4)
            r["pind"] = round(math.prod(ps), 4)
            r["rho"] = [round(R[i][j], 2) for i in range(len(legs)) for j in range(i)]
            if m:
                rs = [q.get("res") for q in r["patas"]]
                if None in rs:
                    r["estado"] = "sin datos"
                elif "pierde" in rs:
                    r["estado"] = "perdida"
                elif "nula" in rs:
                    r["estado"] = "nula"
                else:
                    r["estado"] = "ganada"
            else:
                r["estado"] = "pendiente"
            st = r["importe"]
            r["devuelto"] = {"ganada": st * r["cuota"], "perdida": 0.0, "nula": st}.get(r["estado"])
            if r["devuelto"] is not None:
                r["devuelto"] = round(r["devuelto"], 2)
                r["beneficio"] = round(r["devuelto"] - st, 2)
            r["ev"] = round(st * (r["p"] * r["cuota"] - 1), 2)
        except (KeyError, ValueError, TypeError) as e:
            r["estado"], r["error"] = "error", str(e)
        out.append(r)
    return out
