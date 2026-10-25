"""Genera las páginas del dashboard (una por liga): descarga los datos, ejecuta los modelos y escribe el HTML.

Uso normal (GitHub Actions): python build.py
Pruebas con archivos locales: CSV_<LIGA> (p. ej. CSV_LALIGA), OF_<LIGA> (calendario abierto), FIXTURES_PATH,
TODAY (AAAA-MM-DD), OUT_DIR, ARTIFACT_DIR, SIMS, LEAGUES (lista separada por comas).
"""
import csv
import io
import json
import os
import re
import sys
import time
import traceback
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import model  # noqa: E402
from leagues import LEAGUES, SITE  # noqa: E402

ENV = os.environ.get
FIX_SRC = ENV("FIXTURES_PATH") or "https://www.football-data.co.uk/fixtures.csv"
TODAY = ENV("TODAY") or datetime.now(timezone.utc).date().isoformat()
OUT_DIR = ENV("OUT_DIR") or ROOT
ART_DIR = ENV("ARTIFACT_DIR")
SIMS = int(ENV("SIMS") or 5000)
ONLY = [x.strip() for x in (ENV("LEAGUES") or "").split(",") if x.strip()]

STAT_COLS = [("g1", "HTHG", "HTAG", int), ("xg", "HxG", "AxG", float), ("s", "HS", "AS", int),
             ("st", "HST", "AST", int), ("c", "HC", "AC", int), ("f", "HF", "AF", int),
             ("y", "HY", "AY", int), ("r", "HR", "AR", int)]
# Configuraciones del modelo de goles entre las que elige solo. La primera es la de partida.
GRID = [("base", "Goles y xG al 50 %", {}),
        ("goles", "Solo goles", {"w": 1.0}),
        ("goles75", "Más peso a los goles (75 %)", {"w": 0.75}),
        ("xg75", "Más peso al xG (75 %)", {"w": 0.25}),
        ("reciente", "Más peso a lo reciente (vida media 90 días)", {"half_life": 90}),
        ("sin_dc", "Sin corrección de empates", {"dc": False})]
MONTHS = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def p_in(name):
    return os.path.join(ROOT, name)


def p_out(name):
    return os.path.join(OUT_DIR, name)


# ----------------------------------------------------------------- lectura
def read(src, required=True):
    try:
        if src.startswith("http"):
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 (dashboard futbol)"})
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
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


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


def es_time(t, off=1):
    """football-data da la hora británica; en la España peninsular es siempre una hora más."""
    try:
        h, mi = (t or "").strip().split(":")
        return f"{(int(h) + off) % 24:02d}:{mi}"
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
             "ou": odds2(r, ("AvgC", "Avg", "B365C", "B365")), "ref": (r.get("Referee") or "").strip() or None}
        for k, hc, ac, cast in STAT_COLS:
            m[k] = pair(r, hc, ac, cast)  # None si falta: nunca se cuenta como cero
        out[(h, a)] = m
    return sorted(out.values(), key=lambda m: (m["date"], m["time"], m["h"]))


def load_fixtures(text, div):
    fx = {}
    for r in csv.DictReader(io.StringIO(text or "")):
        if (r.get("Div") or "").strip() != div:
            continue
        d, h, a = pdate(r.get("Date")), (r.get("HomeTeam") or "").strip(), (r.get("AwayTeam") or "").strip()
        if d and h and a:
            fx[(h, a)] = {"date": d, "time": es_time(r.get("Time")), "odds": odds3(r, ("Avg", "B365", "Max")),
                          "ou": odds2(r, ("Avg", "B365", "Max")), "ah": ah3(r),
                          "ref": (r.get("Referee") or "").strip() or None}
    return fx


# ----------------------------------------------------------------- calendario
def parse_openfootball(text, L):
    """Calendario completo de openfootball: [jornada, fecha, local, visitante, hora española]."""
    y0 = int(L["season"][:4])
    names, off = L["of_names"], L.get("of_time_offset", 0)
    out, j, d, tm = [], None, None, ""
    for line in text.splitlines():
        m = re.match(r"\s*▪\s*Matchday\s+(\d+)", line)
        if m:
            j = int(m[1])
            continue
        m = re.match(r"^\s+([A-Z][a-z]{2})\s+([A-Z][a-z]{2})\s+(\d{1,2})(?:\s+(\d{4}))?\s*$", line)
        if m and m[2] in MONTHS:
            mo = MONTHS[m[2]]
            yy = int(m[4]) if m[4] else (y0 if mo >= 7 else y0 + 1)
            d, tm = f"{yy:04d}-{mo:02d}-{int(m[3]):02d}", ""
            continue
        m = re.match(r"^\s+(?:(\d{1,2})[:.](\d\d)\s+)?(\S.*?)\s+v\s+(\S.*?)(?:\s+\d+-\d+(?:\s*\(\d+-\d+\))?)?(?:\s+\[.*\])?\s*$", line)
        if m and j and d:
            h, a = m[3].strip(), m[4].strip()
            if h not in names or a not in names:
                raise ValueError(f"equipo desconocido en el calendario abierto: «{h}» o «{a}»")
            if m[1]:
                tm = f"{(int(m[1]) + off) % 24:02d}:{m[2]}"
            out.append([j, d, names[h], names[a], tm])
    teams = {x[2] for x in out} | {x[3] for x in out}
    n = len(teams)
    pairs = {(x[2], x[3]) for x in out}
    if len(out) != n * (n - 1) or len(pairs) != len(out):
        raise ValueError(f"calendario abierto incompleto: {len(out)} partidos para {n} equipos")
    return out


def get_calendar(key, L, warn):
    """Calendario base [jornada, fecha, local, visitante] y fechas del calendario abierto {(local, visitante): (fecha, hora)}."""
    of, txt = None, read(ENV("OF_" + key.upper()) or L["openfootball"], required=False)
    if txt:
        try:
            of = parse_openfootball(txt, L)
        except Exception as e:  # noqa: BLE001
            warn.append(f"No se pudo usar el calendario abierto ({e}); se usa la última copia buena.")
    cache = p_out(L["calendar_of"])
    if of:
        new = json.dumps(of, ensure_ascii=False, separators=(",", ":"))
        if not os.path.exists(cache) or open(cache, encoding="utf-8").read() != new:
            write(cache, new)
    else:
        of = jload(cache, None) or jload(p_in(L["calendar_of"]), None)
    if L["calendar"] != L["calendar_of"]:
        base = jload(p_in(L["calendar"]), [])
        if of and {(x[2], x[3]) for x in of} != {(x[2], x[3]) for x in base}:
            warn.append("El calendario abierto no coincide con el oficial; se usan solo las fechas oficiales.")
            of = None
    else:
        if not of:
            raise SystemExit("No hay calendario para esta liga.")
        base = [x[:4] for x in of]
    ofmap = {(x[2], x[3]): (x[1], x[4] if len(x) > 4 else "") for x in (of or [])}
    return base, ofmap


def pending_list(cal, played_keys, fx, over, ofmap):
    """Partidos pendientes y de dónde sale su fecha: 3 = football-data (con cuotas), 2 = corregida a mano,
    1 = calendario abierto, 0 = calendario oficial de la jornada."""
    out = []
    for j, d, h, a in cal:
        if (h, a) in played_keys:
            continue
        f = fx.get((h, a)) or {}
        date_, tm, src = d, "", 0
        if (h, a) in ofmap:
            date_, tm = ofmap[(h, a)]
            src = 1
        o = over.get(model.mkey(h, a))
        if o:
            date_, tm, src = o, "", 2
        if f:
            date_, tm, src = f["date"], f["time"], 3
        out.append({"j": j, "date": date_, "cal": d, "time": tm, "h": h, "a": a, "src": src,
                    "odds": f.get("odds"), "ou": f.get("ou"), "ah": f.get("ah"), "ref": f.get("ref")})
    return sorted(out, key=lambda f: (f["date"], f["time"], f["j"], f["h"]))


# ----------------------------------------------------------------- exportación
def rnd(x, n=3):
    return None if x is None else round(x, n)


def rdict(d, n=4):
    return {k: (round(v, n) if isinstance(v, float) else v) for k, v in (d or {}).items()} if d else d


def export_glm(p, extra=()):
    out = {k: round(p[k], 5) for k in ["mu", "eta", "vh0", "va0", "phi", "sa", "sd", *extra]}
    for k in ("a", "d", "va", "vd"):
        out[k] = [round(x, 5) for x in p[k]]
    return out


def trends_live(played, pend, pos, sms, reff):
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
        out += [(f, c) for c in model.trend_candidates(played, pos, sms, f["h"], f["a"],
                                                        ref=reff.get(model.mkey(f["h"], f["a"])))]
    return out


def render(payload, L):
    def rd(name):
        with open(p_in(name), encoding="utf-8") as f:
            return f.read()
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    html = rd("template.html")
    for ph, content in (("/*__CSS__*/", rd("style.css")), ("/*__APP__*/", rd("app.js")),
                        ("/*__DATA__*/", "window.DATA=" + data + ";")):
        if ph not in html:
            raise SystemExit("La plantilla no tiene el marcador " + ph)
        html = html.replace(ph, content, 1)
    return html.replace("__TITLE__", L["title"]).replace("__LEAGUE__", L["name"])


def full_document(fragment):
    """GitHub Pages necesita un documento completo; el navegador coloca solo cada parte en su sitio."""
    return ('<!doctype html>\n<html lang="es">\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + fragment + "\n</html>\n")


# ----------------------------------------------------------------- una liga
def build_league(key, L, fixtures_text):
    t0 = time.time()
    warn = []
    cal, ofmap = get_calendar(key, L, warn)
    jmap = {(c[2], c[3]): c[0] for c in cal}
    played = load_matches(read(ENV("CSV_" + key.upper()) or L["csv"]), jmap)
    if not played:
        raise SystemExit("El CSV no tiene partidos jugados; no se toca la página.")
    cal_teams = {c[2] for c in cal} | {c[3] for c in cal}
    teams = sorted({m["h"] for m in played} | {m["a"] for m in played} | cal_teams)
    unknown = sorted(t for t in teams if cal_teams and t not in cal_teams)
    if unknown:
        warn.append("Equipos del CSV que no están en el calendario: " + ", ".join(unknown))
    miss = sum(1 for m in played if m["xg"] is None or m["c"] is None)
    if miss:
        warn.append(f"{miss} partidos sin xG o sin estadísticas completas (se usan solo los datos disponibles)")
    fx = load_fixtures(fixtures_text, L["div"])
    over = {k: v for k, v in jload(p_in(L["dates"]), {}).items() if not k.startswith("_")}
    pend = pending_list(cal, {(m["h"], m["a"]) for m in played}, fx, over, ofmap)
    log = jload(p_out(L["log"]), {})
    prev_cfg = (log.get("learning") or [{}])[-1].get("cfg")

    # 1) el modelo elige su configuración con la prueba retrospectiva
    step = max(1, len(played) // 60)
    chosen, res, why = model.select_config(played, teams, GRID, prev_cfg, step=step)
    cfg = res[chosen]["cfg"]
    wf = res[chosen]["wf"]
    gm = model.fit_goals(played, teams, cfg, ref=TODAY)
    sms = {k: model.fit_stat(played, teams, k) for k, _ in model.STATS}
    table = model.standings(played, teams, L["tiebreak"])
    pos = {r["t"]: r["pos"] for r in table}
    E = model.expectations(played, gm, sms)
    cross = {k: model.cross_tau_tested(played, E, k, pos) for k in model.CROSS_KEYS}
    # 2) cuánto pesa el modelo frente al mercado
    blend = model.learn_blend(wf)
    # 3) árbitros (solo si el CSV los trae)
    refx = {k: model.referee_effects(played, E, k, sms[k]["phi"]) for k in model.REF_KEYS if sms.get(k)}
    refx = {k: v for k, v in refx.items() if v}
    ref_bt = model.referee_backtest(played, teams) if refx else {}
    # el árbitro solo se aplica si en la prueba retrospectiva no empeora la predicción
    ref_on = {k for k in refx if (ref_bt.get(k) or {}).get("d", 0.0) <= 0}
    reff = {}
    for f in pend:
        if f.get("ref") and refx:
            reff[model.mkey(f["h"], f["a"])] = {k: (v["refs"].get(f["ref"], {"f": 1.0})["f"] if k in ref_on else 1.0)
                                                for k, v in refx.items()}
    t1 = time.time()
    zones = L["zones"]
    sim = model.simulate(gm, teams, played, pend, sims=SIMS, rule=L["tiebreak"], ntop=zones["ucl"], nrel=zones["rel"],
                         neu=zones["ucl"] + zones["uel"])
    t2 = time.time()
    bt = model.backtest_summary(wf)
    variants = []
    for k, name, _ in GRID:
        s = model.backtest_summary(res[k]["wf"]) if res[k]["wf"] else {}
        variants.append({"key": k, "name": name, "chosen": k == chosen, "d": rnd(res[k].get("d"), 4), "se": rnd(res[k].get("se"), 4),
                         **{q: rnd(s.get(q), 4) for q in ("n", "ll", "llm", "dll", "dse", "acc", "pd", "fd")}})
    wfs = model.walk_forward_stats(played, teams)
    trends_bt = model.trend_backtest(played, teams)
    trends_flex = model.trend_backtest(played, teams, strict=False)["summ"]
    t3 = time.time()

    log = model.update_log(log, played, pend, gm, sms, wf, wfs, TODAY, blend=blend["a"] if blend.get("fit") else None, reff=reff)
    hist = [h for h in log.get("learning", []) if h.get("date") != TODAY]
    hist.append({"date": TODAY, "n": len(played), "cfg": chosen, "a": blend["a"], "fit": blend.get("fit", False),
                 "ll": rnd(res[chosen]["ll"], 4), "llm": rnd(blend.get("llm"), 4), "llb": rnd(blend.get("ll"), 4)})
    log["learning"] = hist[-400:]
    write(p_out(L["log"]), json.dumps(log, ensure_ascii=False, indent=1, sort_keys=True))
    ev = model.evaluate_log(log, played)

    payload = build_payload(key, L, played, teams, pend, fx, table, gm, sms, E, cross, sim, bt, variants, ev, warn,
                            trends_bt, trends_live(played, pend, pos, sms, reff), trends_flex,
                            {"chosen": chosen, "why": why, "blend": blend, "hist": log["learning"], "refx": refx,
                             "ref_bt": ref_bt, "ref_on": ref_on, "reff": reff})
    fragment = render(payload, L)
    write(p_out(L["out"]), full_document(fragment))
    if ART_DIR:
        write(os.path.join(ART_DIR, key + ".html"), fragment)
    print(f"OK {key}: {len(played)} partidos hasta {played[-1]['date']}, {len(pend)} pendientes, {len(fx)} con cuotas, "
          f"configuración «{chosen}» ({why}), peso del modelo frente al mercado {blend['a']:.2f}, "
          f"árbitros: {', '.join(k + ('' if k in ref_on else ' (sin aplicar)') for k in refx) or 'sin datos'}, "
          f"registro con {len(log['entries'])} predicciones. "
          f"Tiempos: modelos {t1 - t0:.1f}s, simulación {t2 - t1:.1f}s, pruebas {t3 - t2:.1f}s, total {time.time() - t0:.1f}s")
    for w in warn:
        print(f"Aviso {key}:", w)
    return {"ok": True, "n": len(played), "last": played[-1]["date"], "warn": warn}


def build_payload(key, L, played, teams, pend, fx, table, gm, sms, E, cross, sim, bt, variants, ev, warn,
                  trends_bt, trends_now, trends_flex, learn):
    ti = {t: k for k, t in enumerate(teams)}
    M = []
    for m in played:
        row = [m["date"], m["time"], m["j"], ti[m["h"]], ti[m["a"]], m["hg"], m["ag"]]
        for k, *_ in STAT_COLS:
            v = m.get(k)
            row += [None, None] if v is None else [rnd(x, 2) for x in v]
        row += (m["odds"] or [None] * 3) + (m["ou"] or [None] * 2) + [m.get("ref")]
        M.append(row)
    keys = ["g", "g1", "xg", "s", "st", "c", "f", "y", "r"]
    EX = [[rnd(x) for k in keys for x in (e.get(k) or [None, None])] for e in E]
    reff = learn["reff"]
    FX = []
    for f in pend:
        rf = reff.get(model.mkey(f["h"], f["a"])) or {}
        FX.append([f["j"], f["date"], f["time"], ti[f["h"]], ti[f["a"]], f["src"]] + (f["odds"] or [None] * 3)
                  + (f["ou"] or [None] * 2) + (f.get("ah") or [None] * 3) + [f.get("ref"), rnd(rf.get("y"), 4), rnd(rf.get("f"), 4)])
    CXQ = ("tf", "ta", "s2", "pf", "pa")
    SM = {k: dict(export_glm(p, ("rr",)), **{q: rnd(cross[k].get(q), 5) for q in CXQ}) for k, p in sms.items() if p}
    GM = dict(export_glm(gm, ("rho", "w")), cx={k: {q: rnd(cross[k].get(q), 5) for q in CXQ} for k in ("g", "g2")})
    SIM = [[rnd(s["mean"], 2), s["p10"], s["p90"], rnd(s["ch"], 4), rnd(s["t4"], 4), rnd(s["t6"], 4),
            rnd(s["rel"], 4), [rnd(x, 4) for x in s["pos"]]] for s in sim]
    TB = [{**{k: r[k] for k in ("pos", "pj", "w", "d", "l", "gf", "ga", "pts", "xn", "form")},
           "t": ti[r["t"]], "xpts": round(r["xpts"], 2)} for r in table]
    rows = [{**{k: r[k] for k in ("j", "d", "hg", "ag", "o", "bf", "made", "o25", "tot", "st")},
             "h": ti[r["h"]], "a": ti[r["a"]], "p": r["p"], "pc": r.get("pc"),
             "mk": [round(x, 4) for x in r["mk"]] if r["mk"] else None,
             "bet": r.get("bet"), "betc": r.get("betc")} for r in ev["rows"]]
    LOG = {"n": ev["n"], "nreal": ev["nreal"], "all": rdict(ev["all"]), "real": rdict(ev["real"]), "comb": rdict(ev.get("comb")),
           "calib": ev["calib"], "by_j": [rdict(a) for a in ev["by_j"]], "bets": ev.get("bets"), "betsc": ev.get("betsc"),
           "stats": ev["stats"], "rows": rows}
    T2 = lambda c: {"side": c["side"], "k": c["k"], "over": c["over"], "tier": c["tier"], "L": c["L"]}
    TB_TR = None
    if trends_bt:
        TB_TR = {"summ": {k: rdict(s) for k, s in trends_bt["summ"].items()},
                 "cases": [{**T2(c), "d": c["d"], "h": ti[c["h"]], "a": ti[c["a"]], "obs": c["obs"], "hit": c["hit"], "pm": rnd(c["pm"], 4)}
                           for c in sorted(trends_bt["cases"], key=lambda c: c["d"], reverse=True)]}
    TR = [{**T2(c), "j": f["j"], "d": f["date"], "h": ti[f["h"]], "a": ti[f["a"]], "m": rnd(c["m"], 3), "V": rnd(c["V"], 3),
           "pm": rnd(c["pm"], 4), "rf": rnd(c.get("rf"), 4), "ref": f.get("ref") if c.get("rf") else None,
           "series": c["series"], "cross": c["cross"], "same": c["same"]} for f, c in trends_now]
    b = learn["blend"]
    REF = {k: {"tau": rnd(v["tau"], 4), "bt": rdict(learn["ref_bt"].get(k)), "on": k in learn["ref_on"],
               "refs": sorted([[r, rnd(x["f"], 3), x["n"], rnd(x["o"], 1), rnd(x["e"], 1)] for r, x in v["refs"].items()],
                              key=lambda z: -z[1])} for k, v in learn["refx"].items()}
    others = [{"key": k, "name": x["name"], "url": SITE + ("" if x["out"] == "index.html" else x["out"])} for k, x in LEAGUES.items()]
    return {
        "meta": {"gen": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "today": TODAY,
                 "last": played[-1]["date"], "n": len(played), "ver": model.VERSION, "fx": len(fx),
                 "pend": len(pend), "sims": len(sim) and SIMS, "warn": warn,
                 "league": key, "name": L["name"], "title": L["title"], "zones": L["zones"],
                 "tiebreak": L["tiebreak_text"], "cards_note": L.get("cards_note"), "leagues": others,
                 "sources": L["sources"], "cal_label": L["cal_label"], "cal_fallback": L["cal_fallback"],
                 "refs": bool(learn["refx"])},
        "teams": teams, "names": [L["names"].get(t, t) for t in teams], "short": [L["short"].get(t, t[:3].upper()) for t in teams],
        "M": M, "E": EX, "fx": FX, "table": TB, "gm": GM, "sm": SM, "sim": SIM,
        "bt": {**rdict({k: v for k, v in bt.items() if k not in ("calib", "by_j", "ou")}),
               "calib": bt.get("calib"), "by_j": [rdict(a) for a in bt.get("by_j", [])], "ou": bt.get("ou")},
        "var": variants, "log": LOG, "tb": TB_TR, "tr": TR,
        "tbf": {k: rdict(s) for k, s in (trends_flex or {}).items()},
        "learn": {"chosen": learn["chosen"], "why": learn["why"],
                  "blend": {**rdict({q: v for q, v in b.items() if q != "curve"}), "curve": b.get("curve")},
                  "hist": [rdict(h) for h in learn["hist"][-120:]], "ref": REF},
        "pl": jload(p_in(L["players"]), {}).get("teams", {}) if L.get("players") else {},
    }


# ----------------------------------------------------------------- principal
def main():
    fixtures_text = read(FIX_SRC, required=False)
    status = jload(p_out("estado.json"), {})
    ok_any = False
    for key, L in LEAGUES.items():
        if ONLY and key not in ONLY:
            continue
        try:
            st = build_league(key, L, fixtures_text)
            ok_any = True
        except BaseException as e:  # noqa: BLE001  (una liga que falla no debe tumbar a las demás)
            traceback.print_exc()
            st = {"ok": False, "error": f"{type(e).__name__}: {e}"}
            print(f"ERROR {key}: {st['error']}")
        status[key] = {**st, "gen": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    write(p_out("estado.json"), json.dumps(status, ensure_ascii=False, indent=1))
    if not ok_any:
        raise SystemExit("No se pudo generar ninguna liga.")


if __name__ == "__main__":
    main()
