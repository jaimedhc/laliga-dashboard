# Dashboard de LaLiga 2026-27

Página que se actualiza sola con los datos de football-data.co.uk: clasificación, ficha de cada equipo,
análisis de cada partido (con el cruce contra rivales parecidos), predicciones comparadas con el mercado,
simulación del resto de la liga e historial de predicciones. Solo usa datos de esta temporada.

## Archivos

| Archivo | Qué es |
|---|---|
| `build.py` | Descarga los datos, ejecuta los modelos y genera `index.html` y `predictions.json`. |
| `model.py` | Los modelos estadísticos (goles, estadísticas, simulación, pruebas y registro). |
| `template.html`, `style.css`, `app.js` | La página: estructura, estilos y lógica. `build.py` los une en `index.html`. |
| `calendario.json` | Calendario completo de la RFEF. |
| `fechas.json` | Fechas corregidas a mano de partidos movidos (opcional). |
| `players.py` | Jugadores desde API-Football (solo funciona con un plan de pago; si no, no hace nada). |
| `.github/workflows/update.yml` | La tarea automática. |
| `index.html` | La página generada. **No la edites**: se reescribe en cada actualización. |
| `predictions.json` | Registro de predicciones. **No lo borres**: es el historial congelado. |

## Cómo se actualiza

- Dos veces al día (mañana y tarde) y cada vez que subes alguno de los archivos de la tabla.
- A mano: pestaña **Actions > Actualizar dashboard > Run workflow**.
- Si la descarga falla, la página anterior se queda como estaba.
- football-data publica los resultados uno o dos días después de cada jornada, y las cuotas de los
  próximos partidos unos días antes.

## Corregir una fecha

Si un partido se aplaza o cambia de día y football-data todavía no lo refleja, añade una línea a
`fechas.json` con el formato `"Local|Visitante": "AAAA-MM-DD"`, usando los nombres de equipo del CSV
(por ejemplo `"Levante|Ath Bilbao": "2026-10-21"`).

## Probar en local

```
CSV_PATH=SP1.csv FIXTURES_PATH=fixtures.csv TODAY=2026-10-21 python build.py
```
