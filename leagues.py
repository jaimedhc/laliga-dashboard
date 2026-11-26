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
        "sources": "football-data.co.uk (resultados, estadísticas, xG y cuotas), calendario de la RFEF, fechas y horas "
                   "anunciadas de TheSportsDB, calendario abierto de openfootball, bajas de Biwenger y titulares de Google News",
        "tsdb_id": "4335",  # TheSportsDB: fechas y horas en cuanto se anuncian
        # bajas y dudas (Biwenger; sus nombres de equipo coinciden con los nombres visibles), lo que ha jugado cada jugador
        # (las actas de cada jornada de Biwenger) y titulares (Google News)
        "avail": {"src": "biwenger", "name": "Biwenger",
                  "url": "https://cf.biwenger.com/api/v2/competitions/la-liga/data?lang=es&score=5",
                  "rounds": "https://cf.biwenger.com/api/v2/rounds/la-liga/{}?score=5&lang=es"},
        "news_lang": "es",
        "news_q": {"Alaves": "Alavés", "Ath Bilbao": "Athletic Club", "Ath Madrid": "Atlético de Madrid",
                   "Barcelona": "FC Barcelona", "Betis": "Real Betis", "Celta": "Celta de Vigo", "Elche": "Elche CF",
                   "Espanol": "Espanyol", "Getafe": "Getafe CF", "La Coruna": "Deportivo de La Coruña",
                   "Levante": "Levante UD", "Malaga": "Málaga CF", "Osasuna": "Osasuna", "Real Madrid": "Real Madrid",
                   "Santander": "Racing de Santander", "Sevilla": "Sevilla FC", "Sociedad": "Real Sociedad",
                   "Valencia": "Valencia CF", "Vallecano": "Rayo Vallecano", "Villarreal": "Villarreal CF"},
        "tsdb_names": {"Deportivo Alavés": "Alaves", "Athletic Bilbao": "Ath Bilbao", "Atlético Madrid": "Ath Madrid",
                       "Barcelona": "Barcelona", "Real Betis": "Betis", "Celta Vigo": "Celta", "Elche": "Elche",
                       "Espanyol": "Espanol", "Getafe": "Getafe", "Deportivo de A Coruña": "La Coruna", "Levante": "Levante",
                       "Málaga": "Malaga", "Osasuna": "Osasuna", "Real Madrid": "Real Madrid",
                       "Racing de Santander": "Santander", "Sevilla": "Sevilla", "Real Sociedad": "Sociedad",
                       "Valencia": "Valencia", "Rayo Vallecano": "Vallecano", "Villarreal": "Villarreal"},
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
        "sources": "football-data.co.uk (resultados, estadísticas, xG, árbitros y cuotas), fechas y horas anunciadas de "
                   "TheSportsDB, calendario abierto de openfootball, bajas del Fantasy Premier League y titulares de Google News",
        "tsdb_id": "4328",
        "avail": {"src": "fpl", "name": "Fantasy Premier League", "url": "https://fantasy.premierleague.com/api/bootstrap-static/",
                  "live": "https://fantasy.premierleague.com/api/event/{}/live/"},  # minutos de cada jugador en una jornada
        "avail_names": {"Coventry City": "Coventry", "Hull City": "Hull", "Ipswich Town": "Ipswich", "Man Utd": "Man United",
                        "Spurs": "Tottenham", "Leeds": "Leeds", "Newcastle": "Newcastle"},
        "news_lang": "en",
        "news_q": {"Arsenal": "Arsenal", "Aston Villa": "Aston Villa", "Bournemouth": "Bournemouth", "Brentford": "Brentford",
                   "Brighton": "Brighton", "Chelsea": "Chelsea", "Coventry": "Coventry City", "Crystal Palace": "Crystal Palace",
                   "Everton": "Everton", "Fulham": "Fulham", "Hull": "Hull City", "Ipswich": "Ipswich Town",
                   "Leeds": "Leeds United", "Liverpool": "Liverpool", "Man City": "Manchester City",
                   "Man United": "Manchester United", "Newcastle": "Newcastle United", "Nott'm Forest": "Nottingham Forest",
                   "Sunderland": "Sunderland", "Tottenham": "Tottenham"},
        "tsdb_names": {"Arsenal": "Arsenal", "Aston Villa": "Aston Villa", "Bournemouth": "Bournemouth", "Brentford": "Brentford",
                       "Brighton and Hove Albion": "Brighton", "Chelsea": "Chelsea", "Coventry City": "Coventry",
                       "Crystal Palace": "Crystal Palace", "Everton": "Everton", "Fulham": "Fulham", "Hull City": "Hull",
                       "Ipswich Town": "Ipswich", "Leeds United": "Leeds", "Liverpool": "Liverpool", "Manchester City": "Man City",
                       "Manchester United": "Man United", "Newcastle United": "Newcastle", "Nottingham Forest": "Nott'm Forest",
                       "Sunderland": "Sunderland", "Tottenham Hotspur": "Tottenham"},
        "cal_label": "Fecha del calendario abierto",
        "cal_fallback": "el calendario abierto de openfootball",
        "of_time_offset": 1,  # el calendario abierto inglés da la hora británica
        "cards_note": "En Inglaterra, la segunda amarilla de un expulsado no se cuenta como amarilla.",
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
    "champions": {
        # Fase liga de la Champions (36 equipos, 8 partidos cada uno). football-data no la tiene: los partidos, sus
        # estadísticas y las cuotas de DraftKings salen de ESPN. Las eliminatorias (desde febrero) aún no se modelan.
        "name": "Champions League",
        "title": "Champions League 2026-27",
        "season": "2026-27",
        "source": "espn",
        "espn": "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions",
        # días de cada jornada de la fase liga (hora española); ESPN no da el número de jornada
        "md_dates": {"2026-09-08": 1, "2026-09-09": 1, "2026-09-10": 1, "2026-10-13": 2, "2026-10-14": 2,
                     "2026-10-20": 3, "2026-10-21": 3, "2026-11-03": 4, "2026-11-04": 4, "2026-11-24": 5,
                     "2026-11-25": 5, "2026-12-08": 6, "2026-12-09": 6, "2027-01-19": 7, "2027-01-20": 7,
                     "2027-01-27": 8},
        "xg": False,      # ESPN no da el xG de la Champions: el modelo de goles usa solo los goles
        "mstats": True,   # con tan pocos partidos por equipo, las cuotas ayudan a estimar las estadísticas
        "dates": "fechas_champions.json",
        "out": "champions.html",
        "log": "predictions_champions.json",
        "players": None,
        "tiebreak": "ucl",
        "tiebreak_text": "los empates a puntos se resuelven como en el art. 18 del reglamento de la UEFA: diferencia de goles, "
                         "goles a favor, goles fuera, victorias, victorias fuera y, después, los puntos, la diferencia de goles y "
                         "los goles de los rivales de cada uno (los dos últimos criterios, juego limpio y coeficiente, se sustituyen "
                         "por un sorteo)",
        # los 8 primeros pasan a octavos, del 9.º al 24.º juegan la ronda previa y los 12 últimos quedan eliminados
        "zones": {"ucl": 8, "uel": 16, "rel": 12},
        "zone_names": {"ucl": "Octavos", "uel": "Ronda previa", "rel": "Eliminado", "champ": "1.º de la fase liga",
                       "top": "Octavos directos", "mid": "Top 24", "low": "Eliminado"},
        "sources": "ESPN (resultados, estadísticas y cuotas de DraftKings), bajas de Biwenger y del Fantasy Premier League "
                   "para los equipos españoles e ingleses y titulares de Google News",
        "data_note": "Los resultados, las estadísticas de cada partido (tiros, córners, faltas, amarillas), las fechas y horas y "
                     "las cuotas de DraftKings (1X2 y goles) salen de ESPN; football-data no cubre la Champions y ESPN no da "
                     "el xG, así que el modelo de goles usa solo los goles. Con tan pocos partidos por equipo, las cuotas "
                     "ayudan a estimar las estadísticas: el modelo aprende cuánto pesar las cuotas, su propia predicción y la "
                     "media de la competición (pestaña Aprendizaje). Las bajas, dudas y sanciones solo están para los equipos "
                     "de LaLiga y la Premier (Biwenger y el Fantasy oficial); para el resto hay titulares de Google News. "
                     "GitHub descarga todo cada dos horas y regenera esta página. Solo se usan datos de esta temporada. Las "
                     "horas están en horario peninsular español. De momento solo se modela la fase liga; las eliminatorias "
                     "llegarán en febrero.",
        "cal_label": "Fecha de ESPN",
        "cal_fallback": "las fechas de ESPN",
        # bajas: las de LaLiga y la Premier ya descargadas para sus páginas (nombre en su liga → nombre en la Champions)
        "avail": {"src": "reuse", "name": "Biwenger (equipos españoles) y Fantasy Premier League (ingleses)",
                  "from": {"laliga": {"Real Madrid": "Real Madrid", "Barcelona": "Barcelona", "Ath Madrid": "Atlético Madrid",
                                      "Villarreal": "Villarreal", "Betis": "Real Betis"},
                           "premier": {"Arsenal": "Arsenal", "Aston Villa": "Aston Villa", "Liverpool": "Liverpool",
                                       "Man City": "Manchester City", "Man United": "Manchester United"}}},
        "news_lang": "es",
        "news_q": {"AEK Athens": "AEK Atenas", "AS Roma": "AS Roma", "Arsenal": "Arsenal", "Aston Villa": "Aston Villa",
                   "Atlético Madrid": "Atlético de Madrid", "Barcelona": "FC Barcelona", "Bayern Munich": "Bayern de Múnich",
                   "Bodo/Glimt": "Bodø/Glimt", "Borussia Dortmund": "Borussia Dortmund", "Club Brugge": "Brujas",
                   "Como": "Como 1907", "FC Porto": "Oporto", "Fenerbahce": "Fenerbahçe", "Feyenoord Rotterdam": "Feyenoord",
                   "Galatasaray": "Galatasaray", "Internazionale": "Inter de Milán", "LASK Linz": "LASK Linz", "Lens": "RC Lens",
                   "Lille": "Lille", "Liverpool": "Liverpool", "Manchester City": "Manchester City",
                   "Manchester United": "Manchester United", "Napoli": "Nápoles", "PSV Eindhoven": "PSV Eindhoven",
                   "Paris Saint-Germain": "PSG", "RB Leipzig": "RB Leipzig", "Real Betis": "Real Betis",
                   "Real Madrid": "Real Madrid", "Sabah FK": "Sabah", "Shakhtar Donetsk": "Shakhtar Donetsk",
                   "Slavia Prague": "Slavia de Praga", "Slovan Bratislava": "Slovan Bratislava", "Sporting CP": "Sporting de Portugal",
                   "VfB Stuttgart": "Stuttgart", "Viking FK": "Viking FK", "Villarreal": "Villarreal CF"},
        "names": {"AEK Athens": "AEK Atenas", "AS Roma": "Roma", "Arsenal": "Arsenal", "Aston Villa": "Aston Villa",
                  "Atlético Madrid": "Atlético", "Barcelona": "Barcelona", "Bayern Munich": "Bayern", "Bodo/Glimt": "Bodø/Glimt",
                  "Borussia Dortmund": "Dortmund", "Club Brugge": "Brujas", "Como": "Como", "FC Porto": "Oporto",
                  "Fenerbahce": "Fenerbahçe", "Feyenoord Rotterdam": "Feyenoord", "Galatasaray": "Galatasaray",
                  "Internazionale": "Inter", "LASK Linz": "LASK", "Lens": "Lens", "Lille": "Lille", "Liverpool": "Liverpool",
                  "Manchester City": "Manchester City", "Manchester United": "Manchester United", "Napoli": "Nápoles",
                  "PSV Eindhoven": "PSV", "Paris Saint-Germain": "PSG", "RB Leipzig": "Leipzig", "Real Betis": "Betis",
                  "Real Madrid": "Real Madrid", "Sabah FK": "Sabah", "Shakhtar Donetsk": "Shakhtar",
                  "Slavia Prague": "Slavia Praga", "Slovan Bratislava": "Slovan Bratislava", "Sporting CP": "Sporting",
                  "VfB Stuttgart": "Stuttgart", "Viking FK": "Viking", "Villarreal": "Villarreal"},
        "short": {"AEK Athens": "AEK", "AS Roma": "ROM", "Arsenal": "ARS", "Aston Villa": "AVL", "Atlético Madrid": "ATM",
                  "Barcelona": "BAR", "Bayern Munich": "BAY", "Bodo/Glimt": "BOD", "Borussia Dortmund": "BVB",
                  "Club Brugge": "BRU", "Como": "COM", "FC Porto": "POR", "Fenerbahce": "FEN", "Feyenoord Rotterdam": "FEY",
                  "Galatasaray": "GAL", "Internazionale": "INT", "LASK Linz": "LAS", "Lens": "LEN", "Lille": "LIL",
                  "Liverpool": "LIV", "Manchester City": "MCI", "Manchester United": "MUN", "Napoli": "NAP",
                  "PSV Eindhoven": "PSV", "Paris Saint-Germain": "PSG", "RB Leipzig": "RBL", "Real Betis": "BET",
                  "Real Madrid": "RMA", "Sabah FK": "SAB", "Shakhtar Donetsk": "SHA", "Slavia Prague": "SLA",
                  "Slovan Bratislava": "SLO", "Sporting CP": "SCP", "VfB Stuttgart": "STU", "Viking FK": "VIK",
                  "Villarreal": "VIL"},
    },
}

# Enlaces entre las páginas (absolutos para que funcionen también en las copias publicadas fuera de GitHub).
SITE = "https://jaimedhc.github.io/laliga-dashboard/"
