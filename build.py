"""Descarga el CSV de La Liga de football-data.co.uk y genera index.html."""
import csv, io, json, os, urllib.request
from datetime import datetime

URL = os.environ.get("CSV_URL", "https://www.football-data.co.uk/mmz4281/2627/SP1.csv")
SRC = os.environ.get("CSV_PATH")  # solo para pruebas con un archivo local

def load():
    if SRC:
        return open(SRC, encoding="utf-8-sig", newline="").read()
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8-sig")

def pdate(s):
    for f in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s.strip(), f)
        except ValueError:
            pass
    raise ValueError("Fecha no válida: " + s)

def num(r, k, cast=int):
    try:
        return cast(float(r[k]))
    except (KeyError, ValueError, TypeError):
        return cast(0)

def first(r, keys, cast=float):
    for k in keys:
        try:
            v = cast(float(r[k]))
            if v:
                return v
        except (KeyError, ValueError, TypeError):
            pass
    return cast(0)

rows = []
for r in csv.DictReader(io.StringIO(load())):
    if not (r.get("FTHG") or "").strip() or not (r.get("Date") or "").strip():
        continue  # partido sin jugar o fila vacía
    d = pdate(r["Date"])
    tm = (r.get("Time") or "").strip()
    rows.append(((d, tm), [
        d.strftime("%d/%m"), tm, r["HomeTeam"], r["AwayTeam"],
        num(r, "FTHG"), num(r, "FTAG"), num(r, "HTHG"), num(r, "HTAG"),
        num(r, "HxG", float), num(r, "AxG", float),
        num(r, "HS"), num(r, "AS"), num(r, "HST"), num(r, "AST"),
        num(r, "HF"), num(r, "AF"), num(r, "HC"), num(r, "AC"),
        num(r, "HY"), num(r, "AY"), num(r, "HR"), num(r, "AR"),
        first(r, ["AvgCH", "AvgH"]), first(r, ["AvgCD", "AvgD"]), first(r, ["AvgCA", "AvgA"]),
        first(r, ["AvgC>2.5", "Avg>2.5"]), first(r, ["AvgC<2.5", "Avg<2.5"]),
        first(r, ["AHCh", "AHh"]),
    ]))

if not rows:
    raise SystemExit("El CSV no contiene partidos jugados; no se actualiza la página.")

rows.sort(key=lambda x: x[0])
data = json.dumps([x[1] for x in rows], ensure_ascii=False, separators=(",", ":"))
pl = "{}"
if os.path.exists("players.json"):
    pl = json.dumps(json.load(open("players.json", encoding="utf-8")).get("teams", {}), ensure_ascii=False, separators=(",", ":"))
html = open("template.html", encoding="utf-8").read().replace("__DATA__", data).replace("__PLAYERS__", pl)
open("index.html", "w", encoding="utf-8").write(html)
print(f"OK: {len(rows)} partidos")
