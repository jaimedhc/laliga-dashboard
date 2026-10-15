"""Descarga estadísticas por jugador de API-Football y las guarda en players.json.
Si no hay clave o la API devuelve un error, conserva el players.json anterior."""
import json, os, sys, time, urllib.request

KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()
LEAGUE = int(os.environ.get("AF_LEAGUE", "140"))   # 140 = La Liga
SEASON = os.environ.get("AF_SEASON", "2026")       # temporada 2026-27
OUT = "players.json"

def parse_item(item, teams):
    p = item.get("player", {})
    for s in item.get("statistics", []):
        if (s.get("league") or {}).get("id") != LEAGUE:
            continue
        g, c = s.get("games") or {}, s.get("cards") or {}
        gl = s.get("goals") or {}
        teams.setdefault((s.get("team") or {}).get("name", "?"), []).append({
            "n": p.get("name", "?"), "pos": g.get("position") or "",
            "pj": g.get("appearences") or g.get("appearances") or 0,
            "min": g.get("minutes") or 0, "g": gl.get("total") or 0,
            "a": gl.get("assists") or 0, "y": c.get("yellow") or 0, "r": c.get("red") or 0})

def call(page):
    url = f"https://v3.football.api-sports.io/players?league={LEAGUE}&season={SEASON}&page={page}"
    req = urllib.request.Request(url, headers={"x-apisports-key": KEY})
    return json.load(urllib.request.urlopen(req, timeout=60))

def main():
    if not os.path.exists(OUT):
        json.dump({"teams": {}}, open(OUT, "w"))
    if not KEY:
        print("Sin API_FOOTBALL_KEY: se omiten los jugadores.")
        return
    teams, page, total = {}, 1, 1
    while page <= total:
        d = call(page)
        if d.get("errors"):
            print("La API devolvió un error, se conservan los datos anteriores:", d["errors"])
            return
        total = (d.get("paging") or {}).get("total", 1)
        for it in d.get("response", []):
            parse_item(it, teams)
        page += 1
        time.sleep(0.4)
    if teams:
        json.dump({"teams": teams}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print(f"OK: {sum(map(len, teams.values()))} jugadores en {len(teams)} equipos, {total} páginas")
    else:
        print("La API no devolvió jugadores; se conservan los datos anteriores.")

if __name__ == "__main__":
    main()
