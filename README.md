# Dashboard de LaLiga y la Premier League 2026-27

Páginas que se actualizan solas con los datos de football-data.co.uk: clasificación, ficha de cada equipo,
análisis de cada partido (con el cruce contra rivales parecidos), predicciones comparadas con el mercado,
tendencias claras, simulación del resto de la liga, historial de predicciones y lo que el modelo aprende
cada jornada. Solo usa datos de esta temporada.

- LaLiga: https://jaimedhc.github.io/laliga-dashboard/
- Premier League: https://jaimedhc.github.io/laliga-dashboard/premier.html

## Archivos

| Archivo | Qué es |
|---|---|
| `leagues.py` | Configuración de cada liga: fuentes, nombres, plazas europeas, desempates. Para añadir otra liga se copia un bloque. |
| `build.py` | Descarga los datos, ejecuta los modelos y genera la página y el registro de cada liga. |
| `model.py` | Los modelos estadísticos (goles, estadísticas, simulación, pruebas, aprendizaje, árbitros, tendencias y registro). |
| `template.html`, `style.css`, `app.js` | La página: estructura, estilos y lógica. `build.py` los une en cada página. |
| `calendario.json` | Calendario de LaLiga de la RFEF (base y respaldo). |
| `fechas.json`, `fechas_premier.json` | Fechas corregidas a mano de partidos movidos (opcional). |
| `players.py` | Jugadores de LaLiga desde API-Football (solo funciona con un plan de pago; si no, no hace nada). |
| `.github/workflows/update.yml` | La tarea automática. |
| `index.html`, `premier.html` | Las páginas generadas. **No las edites**: se reescriben en cada actualización. |
| `predictions.json`, `predictions_premier.json` | Registros de predicciones y del aprendizaje. **No los borres**: son el historial congelado. |
| `calendario_of_laliga.json`, `calendario_premier.json` | Última copia buena del calendario abierto de openfootball (se reescriben solos). |
| `estado.json` | Resultado de la última actualización de cada liga. |

## Cómo se actualiza

- Dos veces al día (mañana y tarde) y cada vez que subes alguno de los archivos de la tabla.
- A mano: pestaña **Actions > Actualizar dashboard > Run workflow**.
- Si una liga falla, las demás se actualizan igual y la que falla conserva su página anterior; la ejecución
  sale en rojo en Actions para que se vea.
- football-data publica los resultados uno o dos días después de cada jornada, y las cuotas (y en Inglaterra
  los árbitros) de los próximos partidos unos días antes.

## Qué aprende el modelo

En cada actualización repite la prueba retrospectiva (cada partido predicho solo con los anteriores) y:

1. Elige entre varias versiones del modelo de goles la que mejor ha predicho; solo cambia si la mejora supera el error.
2. Aprende cuánto pesar frente a las cuotas del mercado (la mezcla de modelo y mercado con mejor log-loss).
3. Si el CSV trae el árbitro (Premier), estima su efecto en tarjetas y faltas y lo aplica si no empeora la prueba.
4. Corrige la probabilidad de las tendencias con lo que se han cumplido las anteriores.

Todo se ve en la pestaña **Aprendizaje** y queda guardado en el registro de cada liga.

## Corregir una fecha

Si un partido se aplaza o cambia de día y football-data todavía no lo refleja, añade una línea a
`fechas.json` (LaLiga) o `fechas_premier.json` (Premier) con el formato `"Local|Visitante": "AAAA-MM-DD"`,
usando los nombres de equipo del CSV (por ejemplo `"Levante|Ath Bilbao": "2026-10-21"`).

## Probar en local

```
CSV_LALIGA=SP1.csv CSV_PREMIER=E0.csv FIXTURES_PATH=fixtures.csv TODAY=2026-10-25 OUT_DIR=prueba python build.py
```

`LEAGUES=premier` genera solo una liga.
