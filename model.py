"""Modelo de Poisson con datos solo de esta temporada: ataque/defensa por equipo, ventaja de local,
backtest contra las cuotas y simulación del resto de la liga."""
import bisect, math, random
from datetime import date

def fit(ms, teams, reg, w, cycles=40):
    ix = {t: i for i, t in enumerate(teams)}; n = len(teams); obs = []
    for h, a, gh, ga, xh, xa in ms:  # objetivo = mezcla de goles reales y xG
        obs.append((ix[h], ix[a], 1, w*gh + (1-w)*xh)); obs.append((ix[a], ix[h], 0, w*ga + (1-w)*xa))
    ao = [[] for _ in range(n)]; do = [[] for _ in range(n)]
    for o in obs: ao[o[0]].append(o); do[o[1]].append(o)
    p = {"mu": 0.2, "hm": 0.2, "att": [0.0]*n, "df": [0.0]*n, "ix": ix}
    lam = lambda o: math.exp(p["mu"] + p["hm"]*o[2] + p["att"][o[0]] - p["df"][o[1]])
    for _ in range(cycles):
        L = [lam(o) for o in obs]; p["mu"] += sum(o[3]-l for o, l in zip(obs, L)) / sum(L)
        hs = [(o, lam(o)) for o in obs if o[2]]
        p["hm"] += sum(o[3]-l for o, l in hs) / sum(l for _, l in hs)
        for i in range(n):
            ls = [(o, lam(o)) for o in ao[i]]
            p["att"][i] += (sum(o[3]-l for o, l in ls) - reg*p["att"][i]) / (sum(l for _, l in ls) + reg)
            ls = [(o, lam(o)) for o in do[i]]
            p["df"][i] += (-sum(o[3]-l for o, l in ls) - reg*p["df"][i]) / (sum(l for _, l in ls) + reg)
    p["sa"] = [1/math.sqrt(sum(lam(o) for o in ao[i]) + reg) for i in range(n)]
    p["sd"] = [1/math.sqrt(sum(lam(o) for o in do[i]) + reg) for i in range(n)]
    return p

def pois(l, r):
    u = r.random(); k = 0; q = math.exp(-l); c = q
    while u > c and k < 15:
        k += 1; q *= l/k; c += q
    return k

def pm(l, K=10):
    o = [math.exp(-l)]
    for k in range(1, K+1): o.append(o[-1]*l/k)
    return o

def predict(p, h, a):
    i, j = p["ix"][h], p["ix"][a]
    lh = math.exp(p["mu"]+p["hm"]+p["att"][i]-p["df"][j]); la = math.exp(p["mu"]+p["att"][j]-p["df"][i])
    ph, pa = pm(lh), pm(la); H = D = A = 0.0; best = (0, 0, 0)
    for x, u in enumerate(ph):
        for y, v in enumerate(pa):
            q = u*v
            if x > y: H += q
            elif x == y: D += q
            else: A += q
            if q > best[0]: best = (q, x, y)
    s = H+D+A
    return H/s, D/s, A/s, lh, la, f"{best[1]}-{best[2]}", ph, pa

def outcome(gh, ga): return 0 if gh > ga else (1 if gh == ga else 2)

def mkt(oh, od, oa):
    if not (oh and od and oa): return None
    s = 1/oh + 1/od + 1/oa
    return (1/oh/s, 1/od/s, 1/oa/s)

def score(rows):
    ll = br = 0.0
    for pr, o in rows:
        ll -= math.log(max(pr[o], 1e-9)); br += sum((pr[k]-(1 if k == o else 0))**2 for k in range(3))
    return {"ll": ll/len(rows), "br": br/len(rows)}

def backtest(ms, teams, reg, w, start=30, step=5):
    out = []; p = None
    for k in range(start, len(ms)):
        if (k-start) % step == 0: p = fit([m[:6] for m in ms[:k]], teams, reg, w)
        m = ms[k]; out.append((predict(p, m[0], m[1])[:3], outcome(m[2], m[3]), mkt(*m[6:9])))
    return out

def run(data, cal, sims=4000, w=0.5, reg=16.0):
    ms = [(r[2], r[3], r[4], r[5], r[8], r[9], r[22], r[23], r[24]) for r in data]
    teams = sorted({m[0] for m in ms} | {m[1] for m in ms}); out = {"n": len(ms), "w": w, "reg": reg, "sims": sims}
    if len(ms) >= 40:
        bt = [x for x in backtest(ms, teams, reg, w) if x[2]]
        out["bt"] = {"n": len(bt), "model": score([(a, b) for a, b, _ in bt]), "market": score([(c, b) for _, b, c in bt]),
                     "blend": score([(tuple((x+y)/2 for x, y in zip(a, c)), b) for a, b, c in bt]),
                     "uniform": score([((1/3, 1/3, 1/3), b) for _, b, _ in bt])}
        sens = []  # sensibilidad a los parámetros (no se usa para elegir)
        for w2 in (0.0, 0.5, 1.0):
            for r2 in (8, 16, 32):
                b2 = [x for x in backtest(ms, teams, r2, w2) if x[2]]
                sens.append(score([(a, b) for a, b, _ in b2])["ll"])
        out["sens"] = [min(sens), max(sens)]
    p = fit([m[:6] for m in ms], teams, reg, w); ix = p["ix"]; n = len(teams)
    out["hm"] = math.exp(p["hm"]) - 1
    played = {(m[0], m[1]) for m in ms}; pend = [c for c in cal if (c[2], c[3]) not in played]; out["pend"] = len(pend)
    today = date.today().isoformat(); fut = [c for c in pend if c[1] >= today]; jn = min((c[0] for c in fut), default=None)
    show = [c for c in pend if c[1] < today or (jn and c[0] in (jn, jn+1))]; out["next"] = []
    for j, d, h, a in sorted(show, key=lambda c: (c[1], c[0])):
        H, D, A, lh, la, sc, _, _ = predict(p, h, a)
        out["next"].append({"j": j, "d": d[8:]+"/"+d[5:7], "h": h, "a": a, "ph": H, "pd": D, "pa": A, "xh": lh, "xa": la, "sc": sc, "pp": d < today})
    bp = [0]*n; bd = [0]*n; bg = [0]*n; pj = [0]*n
    for h, a, gh, ga, *_ in ms:
        i, j = ix[h], ix[a]; bg[i] += gh; bg[j] += ga; bd[i] += gh-ga; bd[j] += ga-gh; pj[i] += 1; pj[j] += 1
        if gh > ga: bp[i] += 3
        elif gh < ga: bp[j] += 3
        else: bp[i] += 1; bp[j] += 1
    sched = [(ix[h], ix[a]) for j, d, h, a in pend]; rnd = random.Random(7)
    ch = [0]*n; t4 = [0]*n; rl = [0]*n; sp = [0]*n
    for _ in range(sims):
        ea = [p["att"][t] + rnd.gauss(0, p["sa"][t]) for t in range(n)]; ed = [p["df"][t] + rnd.gauss(0, p["sd"][t]) for t in range(n)]
        pt = bp[:]; gd = bd[:]; gf = bg[:]
        for i, j in sched:
            x = pois(math.exp(p["mu"]+p["hm"]+ea[i]-ed[j]), rnd); y = pois(math.exp(p["mu"]+ea[j]-ed[i]), rnd)
            gf[i] += x; gf[j] += y; gd[i] += x-y; gd[j] += y-x
            if x > y: pt[i] += 3
            elif x < y: pt[j] += 3
            else: pt[i] += 1; pt[j] += 1
        for r, t in enumerate(sorted(range(n), key=lambda t: (-pt[t], -gd[t], -gf[t], rnd.random()))):
            sp[t] += pt[t]
            if r == 0: ch[t] += 1
            if r < 4: t4[t] += 1
            if r >= n-3: rl[t] += 1
    out["teams"] = [{"t": t, "att": math.exp(p["att"][i]), "df": math.exp(-p["df"][i]), "pj": pj[i], "pts": bp[i],
                     "exp": sp[i]/sims, "ch": ch[i]/sims, "t4": t4[i]/sims, "rl": rl[i]/sims} for i, t in enumerate(teams)]
    return out
