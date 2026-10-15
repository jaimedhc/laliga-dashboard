# Dashboard de La Liga que se actualiza solo

Cada día, GitHub descarga el CSV de football-data.co.uk, regenera la página y la publica.
Tú no tienes que subir nada más después de la configuración (unos 10 minutos, una sola vez).

## Archivos
- `build.py`: descarga el CSV y genera `index.html`.
- `template.html`: el diseño del dashboard.
- `.github/workflows/update.yml`: la tarea diaria (contenido más abajo).

## Pasos (una sola vez)

1. **Cuenta y repositorio.** Entra en github.com (crea una cuenta gratis si no tienes).
   Pulsa **New repository**, ponle de nombre `laliga-dashboard`, márcalo como **Public** y créalo.
   (El repositorio debe ser público para publicar la página gratis.)

2. **Sube dos archivos.** En el repositorio: **Add file > Upload files**, arrastra
   `build.py` y `template.html` y pulsa **Commit changes**.

3. **Crea la tarea diaria.** **Add file > Create new file**. En el nombre escribe exactamente
   `.github/workflows/update.yml` (al escribir las barras se crean las carpetas).
   Pega el contenido de abajo y pulsa **Commit changes**.

4. **Permisos.** **Settings > Actions > General > Workflow permissions** > marca
   **Read and write permissions** > **Save**.

5. **Primera ejecución.** Pestaña **Actions** > **Actualizar dashboard** > **Run workflow**.
   Tarda un minuto y crea el archivo `index.html`.

6. **Publica la página.** **Settings > Pages**. En *Source* elige **Deploy from a branch**,
   rama `main`, carpeta `/ (root)` y **Save**. A los pocos minutos tu dashboard estará en
   `https://TU_USUARIO.github.io/laliga-dashboard/`

## Cómo funciona después
- Se ejecuta solo cada día a las 07:00 UTC. Solo guarda cambios si hay partidos nuevos.
- Para forzar una actualización: pestaña **Actions > Actualizar dashboard > Run workflow**.
- Si el CSV no se puede descargar o viene vacío, la tarea falla y la página anterior se queda como estaba.
- football-data.co.uk suele publicar los resultados uno o dos días después de cada jornada.
- GitHub puede pausar las tareas programadas de repositorios sin actividad durante mucho tiempo;
  si pasa, se reactiva con un clic en la pestaña Actions.

## Contenido de `.github/workflows/update.yml`

```yaml
name: Actualizar dashboard

on:
  schedule:
    - cron: "0 7 * * *"   # cada día a las 07:00 UTC
  workflow_dispatch:       # botón para ejecutarlo a mano

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Generar página
        run: python build.py
      - name: Guardar cambios
        run: |
          git config user.name "github-actions"
          git config user.email "actions@users.noreply.github.com"
          git add index.html
          git diff --cached --quiet || (git commit -m "Actualizar datos" && git push)
```

## Jugadores (goles, asistencias, amarillas...)

Los datos por jugador salen de API-Football (plan gratuito: 100 peticiones al día; este proyecto usa unas 30).

1. Regístrate gratis en api-football.com y copia tu clave de API.
2. En tu repositorio de GitHub: **Settings > Secrets and variables > Actions > New repository secret**.
   Nombre: `API_FOOTBALL_KEY`. Valor: tu clave. Guarda.
3. Sube `players.py`, `build.py` y `template.html` (sustituyen a los anteriores).
4. Edita `.github/workflows/update.yml` (icono del lápiz) y sustituye todo su contenido por el del archivo `update.yml` de este paquete.
5. Ejecuta **Actions > Actualizar dashboard > Run workflow** y abre el paso **Descargar jugadores** para ver el resultado.

Si el plan gratuito no cubre la temporada actual, ese paso mostrará el aviso de la API y la página seguirá funcionando sin plantillas.
