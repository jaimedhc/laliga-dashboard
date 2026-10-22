"""Genera el dashboard de LaLiga: descarga los datos, ejecuta los modelos y escribe index.html.

Uso normal (GitHub Actions): python build.py
Pruebas con archivos locales: CSV_PATH, FIXTURES_PATH, TODAY (AAAA-MM-DD), OUT_HTML, LOG_PATH, SIMS.
"""
import csv
import io
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import model  # noqa: E402

ENV = os.environ.get
CSV_SRC = ENV("CSV_PATH") or ENV("CSV_URL") or "https://www.football-data.co.uk/mmz4281/2627/SP1.csv"
FIX_SRC = ENV("FIXTURES_PATH") or ENV("FIXTURES_URL") or "https://www.football-data.co.uk/fixtures.csv"
TODAY = ENV("TODAY") or datetime.now(timezone.utc).date().isoformat()
OUT_HTML = ENV("OUT_HTML") or os.path.join(ROOT, "index.html")
LOG_PATH = ENV("LOG_PATH") or os.path.join(ROOT, "predictions.json")
SIMS = int(ENV("SIMS") or 5000)

NAMES = {"Alaves": "Alavés", "Ath Bilbao": "Athletic", "Ath Madrid": "Atlético", "Barcelona": "Barcelona",
         "Betis": "Betis", "Celta": "Celta", "Elche": "Elche", "Espanol": "Espanyol", "Getafe": "Getafe",
         "La Coruna": "Deportivo", "Levante": "Levante", "Malaga": "Málaga", "Osasuna": "Osasuna",
         "Real Madrid": "Real Madrid", "Santander": "Racing", "Sevilla": "Sevilla", "Sociedad": "Real Sociedad",
         "Valencia": "Valencia", "Vallecano": "Rayo Vallecano", "Villarreal": "Villarreal"}
SHORT = {"Alaves": "ALA", "Ath Bilbao": "ATH", "Ath Madrid": "ATM", "Barcelona": "BAR", "Betis": "BET",
         "Celta": "CEL", "Elche": "ELC", "Espanol": "ESP", "Getafe": "GET", "La Coruna": "DEP", "Levante": "LEV",
         "Malaga": "MAL", "Osasuna": "OSA", "Real Madrid": "RMA", "Santander": "RAC", "Sevilla": "SEV",
         "Sociedad": "RSO", "Valencia": "VAL", "Vallecano": "RAY", "Villarreal": "VIL"}
STAT_COLS = [("g1", "HTHG", "HTAG", int), ("xg", "HxG", "AxG", float), ("s", "HS", "AS", int),
             ("st", "HST", "AST", int), ("c", "HC", "AC", int), ("f", "HF", "AF", int),
             ("y", "HY", "AY", int), ("r", "HR", "AR", int)]
VARIANTS = [("Modelo actual", {}), ("Solo goles (sin xG)", {"w": 1.0}), ("Más peso al xG (75 %)", {"w": 0.25}),
            ("Sin corrección de empates", {"dc": False}), ("Más peso a lo reciente (vida media 45 días)", {"half_life": 45})]


# ----------------------------------------------------------------- lectura
def read(src, required=True):
    try:
        if src.startswith("http"):
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 (dashboard LaLiga)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8-sig", errors="replace")
        with open(src, encoding="utf-8-sig") as f:
            return f.read()
    except Exception as e:  # noqa: BLE001
        if required:
            raise
        print("Aviso: no se pudo leer", src, "->", e)
        return None


def jload(path, default):
    p = path if os.path.isabs(path) else os.path.join(ROOT, path)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return default


def pdate(s):
    s = (s or "").strip()
    for f in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, f).date().isoformat()
        except ValueError:
            pass
    return None


def fnum(r, k):
    try:
        return float((r.get(k) or "").strip())
    except ValueError:
        return None


def pair(r, a, b, cast):
    x, y = fnum(r, a), fnum(r, b)
    return None if x is None or y is None else [cast(x), cast(y)]


def odds3(r, prefixes):
    for p in prefixes:
        o = [fnum(r, p + s) for s in "HDA"]
        if all(x is not None and x > 1 for x in o):
            return o
    return None


def odds2(r, prefixes):
    for p in prefixes:
        o = [fnum(r, p + ">2.5"), fnum(r, p + "<2.5")]
        if all(x is not None and x > 1 for x in o):
            return o
    return None


def ah3(r):
    """Hándicap asiático del local y cuotas medias (local, visitante)."""
    for line, h, a in (("AHh", "AvgAHH", "AvgAHA"), ("AHh", "B365AHH", "B365AHA")):
        v = [fnum(r, line), fnum(r, h), fnum(r, a)]
        if v[0] is not None and all(x is not None and x > 1 for x in v[1:]):
            return v
    return None


def es_time(t):
    """football-data da la hora británica; en la España peninsular es siempre una hora más."""
    try:
        h, mi = (t or "").strip().split(":")
        return f"{(int(h) + 1) % 24:02d}:{mi}"
    except ValueError:
        return ""


def load_matches(text, jmap):
    out = {}
    for r in csv.DictReader(io.StringIO(text)):
        d, h, a = pdate(r.get("Date")), (r.get("HomeTeam") or "").strip(), (r.get("AwayTeam") or "").strip()
        hg, ag = fnum(r, "FTHG"), fnum(r, "FTAG")
        if not d or not h or not a or hg is None or ag is None:
            continue  # partido sin jugar o fila vacía
        m = {"date": d, "time": es_time(r.get("Time")), "h": h, "a": a, "hg": int(hg), "ag": int(ag),
             "j": jmap.get((h, a)), "odds": odds3(r, ("AvgC", "Avg", "B365C", "B365")),
             "ou": odds2(r, ("AvgC", "Avg", "B365C", "B365"))}
        for k, hc, ac, cast in STAT_COLS:
            m[k] = pair(r, hc, ac, cast)  # None si falta: nunca se cuenta como cero
        out[(h, a)] = m
    return sorted(out.values(), key=lambda m: (m["date"], m["time"], m["h"]))


def load_fixtures(text):
    fx = {}
    for r in csv.DictReader(io.StringIO(text or "")):
        if (r.get("Div") or "").strip() != "SP1":
            continue
        d, h, a = pdate(r.get("Date")), (r.get("HomeTeam") or "").strip(), (r.get("AwayTeam") or "").strip()
        if d and h and a:
            fx[(h, a)] = {"date": d, "time": es_time(r.get("Time")), "odds": odds3(r, ("Avg", "B365", "Max")),
                          "ou": odds2(r, ("Avg", "B365", "Max")), "ah": ah3(r)}
    return fx


def pending_list(cal, played_keys, fx, over):
    """Partidos pendientes. La fecha sale de fixtures.csv si está, si no de fechas.json y si no del calendario."""
    out = []
    for j, d, h, a in cal:
        if (h, a) in played_keys:
            continue
        f = fx.get((h, a)) or {}
        o = over.get(model.mkey(h, a))
        date_, tm, src = d, "", 0
        if o:
            date_, src = o, 1
        if f:
            date_, tm, src = f["date"], f["time"], 2
        out.append({"j": j, "date": date_, "cal": d, "time": tm, "h": h, "a": a, "src": src,
                    "odds": f.get("odds"), "ou": f.get("ou"), "ah": f.get("ah")})
    return sorted(out, key=lambda f: (f["date"], f["time"], f["j"], f["h"]))


# ----------------------------------------------------------------- exportación
def rnd(x, n=3):
    return None if x is None else round(x, n)


def export_glm(p, extra=()):
    out = {k: round(p[k], 5) for k in ["mu", "eta", "vh0", "va0", "phi", "sa", "sd", *extra]}
    for k in ("a", "d", "va", "vd"):
        out[k] = [round(x, 5) for x in p[k]]
    return out


def agg_round(a):
    if not a:
        return a
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in a.items()}


def build_payload(played, teams, pend, fx, table, gm, sms, E, cross, sim, bt, variants, ev, warn, trends_bt=None, trends_now=None, trends_flex=None):
    ti = {t: k for k, t in enumerate(teams)}
    M = []
    for m in played:
        row = [m["date"], m["time"], m["j"], ti[m["h"]], ti[m["a"]], m["hg"], m["ag"]]
        for k, *_ in STAT_COLS:
            v = m.get(k)
            row += [None, None] if v is None else [rnd(x, 2) for x in v]
        row += (m["odds"] or [None] * 3) + (m["ou"] or [None] * 2)
        M.append(row)
    keys = ["g", "g1", "xg", "s", "st", "c", "f", "y", "r"]
    EX = [[rnd(x) for k in keys for x in (e.get(k) or [None, None])] for e in E]
    FX = [[f["j"], f["date"], f["time"], ti[f["h"]], ti[f["a"]], f["src"]] + (f["odds"] or [None] * 3)
          + (f["ou"] or [None] * 2) + (f.get("ah") or [None] * 3) for f in pend]
    CXQ = ("tf", "ta", "s2", "pf", "pa")
    SM = {k: dict(export_glm(p, ("rr",)), **{q: rnd(cross[k].get(q), 5) for q in CXQ}) for k, p in sms.items() if p}
    GM = dict(export_glm(gm, ("rho", "w")), cx={k: {q: rnd(cross[k].get(q), 5) for q in CXQ} for k in ("g", "g2")})
    SIM = [[rnd(s["mean"], 2), s["p10"], s["p90"], rnd(s["ch"], 4), rnd(s["t4"], 4), rnd(s["t6"], 4),
            rnd(s["rel"], 4), [rnd(x, 4) for x in s["pos"]]] for s in sim]
    TB = [{**{k: r[k] for k in ("pos", "pj", "w", "d", "l", "gf", "ga", "pts", "xn", "form")},
           "t": ti[r["t"]], "xpts": round(r["xpts"], 2)} for r in table]
    rows = [{**{k: r[k] for k in ("j", "d", "hg", "ag", "o", "bf", "made", "o25", "tot", "st")},
             "h": ti[r["h"]], "a": ti[r["a"]], "p": r["p"], "mk": [round(x, 4) for x in r["mk"]] if r["mk"] else None,
             "bet": r.get("bet")} for r in ev["rows"]]
    LOG = {"n": ev["n"], "nreal": ev["nreal"], "all": agg_round(ev["all"]), "real": agg_round(ev["real"]),
           "calib": ev["calib"], "by_j": [agg_round(a) for a in ev["by_j"]], "bets": ev.get("bets"),
           "stats": ev["stats"], "rows": rows}
    T2 = lambda c: {"side": c["side"], "k": c["k"], "over": c["over"], "tier": c["tier"], "L": c["L"]}
    TB_TR = None
    if trends_bt:
        TB_TR = {"summ": {k: {q: rnd(v, 4) if isinstance(v, float) else v for q, v in s.items()} for k, s in trends_bt["summ"].items()},
                 "cases": [{**T2(c), "d": c["d"], "h": ti[c["h"]], "a": ti[c["a"]], "obs": c["obs"], "hit": c["hit"], "pm": rnd(c["pm"], 4)}
                           for c in sorted(trends_bt["cases"], key=lambda c: c["d"], reverse=True)]}
    TR = [{**T2(c), "j": f["j"], "d": f["date"], "h": ti[f["h"]], "a": ti[f["a"]], "m": rnd(c["m"], 3), "V": rnd(c["V"], 3),
           "pm": rnd(c["pm"], 4), "series": c["series"], "cross": c["cross"], "same": c["same"]} for f, c in (trends_now or [])]
    return {
        "meta": {"gen": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "today": TODAY,
                 "last": played[-1]["date"], "n": len(played), "ver": model.VERSION, "fx": len(fx),
                 "pend": len(pend), "sims": len(sim) and SIMS, "warn": warn},
        "teams": teams, "names": [NAMES.get(t, t) for t in teams], "short": [SHORT.get(t, t[:3].upper()) for t in teams],
        "M": M, "E": EX, "fx": FX, "table": TB, "gm": GM, "sm": SM, "sim": SIM,
        "bt": {**agg_round({k: v for k, v in bt.items() if k not in ("calib", "by_j", "ou")}),
               "calib": bt.get("calib"), "by_j": [agg_round(a) for a in bt.get("by_j", [])], "ou": bt.get("ou")},
        "var": variants, "log": LOG, "tb": TB_TR, "tr": TR,
        "tbf": {k: {q: rnd(v, 4) if isinstance(v, float) else v for q, v in s.items()} for k, s in (trends_flex or {}).items()}, "pl": jload("players.json", {}).get("teams", {}),
    }


def trends_live(played, pend, pos, sms):
    """Tendencias claras de los partidos que se muestran en la página (los de fecha pasada sin resultado y las dos
    próximas jornadas), con todos los partidos jugados y la clasificación actual."""
    up = [f for f in pend if f["date"] >= TODAY]
    js = []
    for f in up:
        if f["j"] not in js:
            js.append(f["j"])
    js = js[:2]
    first = up[0]["date"] if up else None
    show = [f for f in pend if f["date"] < TODAY] + [f for f in up if f["j"] in js or f["date"] == first]
    out = []
    for f in show:
        out += [(f, c) for c in model.trend_candidates(played, pos, sms, f["h"], f["a"])]
    return out


def render(payload):
    def rd(name):
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            return f.read()
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    html = rd("template.html")
    for ph, content in (("/*__CSS__*/", rd("style.css")), ("/*__APP__*/", rd("app.js")),
                        ("/*__DATA__*/", "window.DATA=" + data + ";")):
        if ph not in html:
            raise SystemExit("La plantilla no tiene el marcador " + ph)
        html = html.replace(ph, content, 1)
    return html  # fragmento: el título, los estilos y el contenido, sin <html>/<head>/<body>


def full_document(fragment):
    """GitHub Pages necesita un documento completo; el navegador coloca solo cada parte en su sitio."""
    return ('<!doctype html>\n<html lang="es">\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + fragment + "\n</html>\n")


def write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


# ----------------------------------------------------------------- principal
def main():
    t0 = time.time()
    cal = jload("calendario.json", [])
    jmap = {(c[2], c[3]): c[0] for c in cal}
    played = load_matches(read(CSV_SRC), jmap)
    if not played:
        raise SystemExit("El CSV no tiene partidos jugados; no se toca la página.")
    cal_teams = {c[2] for c in cal} | {c[3] for c in cal}
    teams = sorted({m["h"] for m in played} | {m["a"] for m in played} | cal_teams)
    warn = []
    unknown = sorted(t for t in teams if cal_teams and t not in cal_teams)
    if unknown:
        warn.append("Equipos del CSV que no están en el calendario: " + ", ".join(unknown))
    miss = sum(1 for m in played if m["xg"] is None or m["c"] is None)
    if miss:
        warn.append(f"{miss} partidos sin xG o sin estadísticas completas (se usan solo los datos disponibles)")
    fx = load_fixtures(read(FIX_SRC, required=False))
    over = {k: v for k, v in jload("fechas.json", {}).items() if not k.startswith("_")}
    pend = pending_list(cal, {(m["h"], m["a"]) for m in played}, fx, over)

    gm = model.fit_goals(played, teams, ref=TODAY)
    sms = {k: model.fit_stat(played, teams, k) for k, _ in model.STATS}
    table = model.standings(played, teams)
    pos = {r["t"]: r["pos"] for r in table}
    E = model.expectations(played, gm, sms)
    cross = {k: model.cross_tau_tested(played, E, k, pos) for k in model.CROSS_KEYS}
    t1 = time.time()
    sim = model.simulate(gm, teams, played, pend, sims=SIMS)
    t2 = time.time()
    wf = model.walk_forward_goals(played, teams)
    bt = model.backtest_summary(wf)
    variants = []
    for name, cfg in VARIANTS:
        s = bt if not cfg else model.backtest_summary(model.walk_forward_goals(played, teams, cfg))
        variants.append({"name": name, **{k: rnd(s.get(k), 4) for k in ("n", "ll", "llm", "dll", "dse", "acc", "pd", "fd")}})
    wfs = model.walk_forward_stats(played, teams)
    trends_bt = model.trend_backtest(played, teams)
    trends_flex = model.trend_backtest(played, teams, strict=False)["summ"]
    t3 = time.time()

    log = model.update_log(jload(LOG_PATH, {}), played, pend, gm, sms, wf, wfs, TODAY)
    write(LOG_PATH, json.dumps(log, ensure_ascii=False, indent=1, sort_keys=True))
    ev = model.evaluate_log(log, played)

    payload = build_payload(played, teams, pend, fx, table, gm, sms, E, cross, sim, bt, variants, ev, warn, trends_bt,
                            trends_live(played, pend, pos, sms), trends_flex)
    fragment = render(payload)
    write(OUT_HTML, full_document(fragment))
    if ENV("ARTIFACT_OUT"):
        write(ENV("ARTIFACT_OUT"), fragment)
    print(f"OK: {len(played)} partidos hasta {played[-1]['date']}, {len(pend)} pendientes, "
          f"{len(fx)} con cuotas de fixtures.csv, registro con {len(log['entries'])} predicciones. "
          f"Tiempos: modelos {t1 - t0:.1f}s, simulación {t2 - t1:.1f}s, pruebas {t3 - t2:.1f}s, total {time.time() - t0:.1f}s")
    for w in warn:
        print("Aviso:", w)


if __name__ == "__main__":
    main()
