"""Configuración de cada liga. Para añadir otra liga basta con copiar un bloque y adaptar nombres y fuentes."""

LEAGUES = {
    "laliga": {
        "name": "LaLiga",
        "title": "LaLiga 2026-27",
        "season": "2026-27",
        "div": "SP1",  # código de football-data
        "csv": "https://www.football-data.co.uk/mmz4281/2627/SP1.csv",
        "openfootball": "https://raw.githubusercontent.com/openfootball/espana/master/2026-27/1-liga.txt",
        "calendar": "calendario.json",          # calendario de la RFEF (base y respaldo)
        "calendar_of": "calendario_of_laliga.json",  # última copia buena del calendario abierto
        "dates": "fechas.json",                 # correcciones manuales de fechas
        "out": "index.html",
        "log": "predictions.json",
        "players": "players.json",
        "tiebreak": "h2h",
        "tiebreak_text": "los empates a puntos se resuelven como en el art. 10 de las normas de competición de la RFEF: "
                         "entre dos equipos, la diferencia de goles en sus partidos; entre más de dos, los puntos y luego la "
                         "diferencia de goles en los partidos entre ellos; después, la diferencia de goles general y los goles a "
                         "favor (el juego limpio se sustituye por un sorteo)",
        "zones": {"ucl": 4, "uel": 2, "rel": 3},
        "sources": "football-data.co.uk (resultados, estadísticas, xG y cuotas), calendario de la RFEF y calendario "
                   "abierto de openfootball (fechas y horas)",
        "cal_label": "Fecha del calendario de la RFEF",
        "cal_fallback": "el calendario abierto de openfootball y, si falta, el de la RFEF",
        "of_time_offset": 0,  # el calendario abierto de LaLiga ya da la hora española
        "names": {"Alaves": "Alavés", "Ath Bilbao": "Athletic", "Ath Madrid": "Atlético", "Barcelona": "Barcelona",
                  "Betis": "Betis", "Celta": "Celta", "Elche": "Elche", "Espanol": "Espanyol", "Getafe": "Getafe",
                  "La Coruna": "Deportivo", "Levante": "Levante", "Malaga": "Málaga", "Osasuna": "Osasuna",
                  "Real Madrid": "Real Madrid", "Santander": "Racing", "Sevilla": "Sevilla", "Sociedad": "Real Sociedad",
                  "Valencia": "Valencia", "Vallecano": "Rayo Vallecano", "Villarreal": "Villarreal"},
        "short": {"Alaves": "ALA", "Ath Bilbao": "ATH", "Ath Madrid": "ATM", "Barcelona": "BAR", "Betis": "BET",
                  "Celta": "CEL", "Elche": "ELC", "Espanol": "ESP", "Getafe": "GET", "La Coruna": "DEP", "Levante": "LEV",
                  "Malaga": "MAL", "Osasuna": "OSA", "Real Madrid": "RMA", "Santander": "RAC", "Sevilla": "SEV",
                  "Sociedad": "RSO", "Valencia": "VAL", "Vallecano": "RAY", "Villarreal": "VIL"},
        "of_names": {"Athletic Club": "Ath Bilbao", "CA Osasuna": "Osasuna", "Club Atlético de Madrid": "Ath Madrid",
                     "Deportivo Alavés": "Alaves", "Elche CF": "Elche", "FC Barcelona": "Barcelona", "Getafe CF": "Getafe",
                     "Levante UD": "Levante", "Málaga CF": "Malaga", "RC Celta de Vigo": "Celta",
                     "RC Deportivo La Coruña": "La Coruna", "RCD Espanyol de Barcelona": "Espanol",
                     "Rayo Vallecano de Madrid": "Vallecano", "Real Betis Balompié": "Betis", "Real Madrid CF": "Real Madrid",
                     "Real Racing Club de Santander": "Santander", "Real Sociedad de Fútbol": "Sociedad",
                     "Sevilla FC": "Sevilla", "Valencia CF": "Valencia", "Villarreal CF": "Villarreal"},
    },
    "premier": {
        "name": "Premier League",
        "title": "Premier League 2026-27",
        "season": "2026-27",
        "div": "E0",
        "csv": "https://www.football-data.co.uk/mmz4281/2627/E0.csv",
        "openfootball": "https://raw.githubusercontent.com/openfootball/england/master/2026-27/1-premierleague.txt",
        "calendar": "calendario_premier.json",
        "calendar_of": "calendario_premier.json",
        "dates": "fechas_premier.json",
        "out": "premier.html",
        "log": "predictions_premier.json",
        "players": None,
        "tiebreak": "gd",
        "tiebreak_text": "los empates a puntos se resuelven como en el reglamento de la Premier League: diferencia de goles, "
                         "goles a favor y, después, los puntos y los goles fuera de casa en los partidos entre ellos (el partido "
                         "de desempate se sustituye por un sorteo)",
        "zones": {"ucl": 4, "uel": 1, "rel": 3},
        "sources": "football-data.co.uk (resultados, estadísticas, xG, árbitros y cuotas) y calendario abierto de "
                   "openfootball (fechas y horas)",
        "cal_label": "Fecha del calendario abierto",
        "cal_fallback": "el calendario abierto de openfootball",
        "of_time_offset": 1,  # el calendario abierto inglés da la hora británica
        "cards_note": "En Inglaterra, una doble amarilla cuenta solo como roja.",
        "names": {"Arsenal": "Arsenal", "Aston Villa": "Aston Villa", "Bournemouth": "Bournemouth", "Brentford": "Brentford",
                  "Brighton": "Brighton", "Chelsea": "Chelsea", "Coventry": "Coventry", "Crystal Palace": "Crystal Palace",
                  "Everton": "Everton", "Fulham": "Fulham", "Hull": "Hull", "Ipswich": "Ipswich", "Leeds": "Leeds",
                  "Liverpool": "Liverpool", "Man City": "Manchester City", "Man United": "Manchester United",
                  "Newcastle": "Newcastle", "Nott'm Forest": "Nottingham Forest", "Sunderland": "Sunderland",
                  "Tottenham": "Tottenham"},
        "short": {"Arsenal": "ARS", "Aston Villa": "AVL", "Bournemouth": "BOU", "Brentford": "BRE", "Brighton": "BHA",
                  "Chelsea": "CHE", "Coventry": "COV", "Crystal Palace": "CRY", "Everton": "EVE", "Fulham": "FUL",
                  "Hull": "HUL", "Ipswich": "IPS", "Leeds": "LEE", "Liverpool": "LIV", "Man City": "MCI",
                  "Man United": "MUN", "Newcastle": "NEW", "Nott'm Forest": "NFO", "Sunderland": "SUN", "Tottenham": "TOT"},
        "of_names": {"AFC Bournemouth": "Bournemouth", "Arsenal FC": "Arsenal", "Aston Villa FC": "Aston Villa",
                     "Brentford FC": "Brentford", "Brighton & Hove Albion FC": "Brighton", "Chelsea FC": "Chelsea",
                     "Coventry City FC": "Coventry", "Crystal Palace FC": "Crystal Palace", "Everton FC": "Everton",
                     "Fulham FC": "Fulham", "Hull City AFC": "Hull", "Ipswich Town FC": "Ipswich", "Leeds United FC": "Leeds",
                     "Liverpool FC": "Liverpool", "Manchester City FC": "Man City", "Manchester United FC": "Man United",
                     "Newcastle United FC": "Newcastle", "Nottingham Forest FC": "Nott'm Forest",
                     "Sunderland AFC": "Sunderland", "Tottenham Hotspur FC": "Tottenham"},
    },
}

# Enlaces entre las páginas (absolutos para que funcionen también en las copias publicadas fuera de GitHub).
SITE = "https://jaimedhc.github.io/laliga-dashboard/"
