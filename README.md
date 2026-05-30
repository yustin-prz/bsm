# Bedrock Server Manager

Aplicación de escritorio (PyQt6) para administrar un servidor dedicado de
Minecraft Bedrock: consola en vivo, monitor de recursos, constructor de
comandos, edición de `server.properties`, allowlist, gestión de packs/addons
(con reordenamiento de prioridad y subpacks) y un editor de `level.dat` (NBT).

## Estructura del proyecto

```
main.py                  Punto de entrada (orquestador)
requirements.txt         Dependencias
bsm/                     Paquete principal
├── window.py            Ventana principal (une todas las pestañas)
├── theme.py             Colores y estilos
├── server.py            Hilo que ejecuta bedrock_server.exe
├── packs.py             Instalador de packs + utilidades de manifest
├── nbt.py               Lector/escritor NBT little-endian (level.dat)
├── commands_data.py     Catálogos y definiciones de comandos
├── widgets.py           Widgets reutilizables (tarjetas, buscadores)
└── tabs/                Una pestaña por archivo
    ├── console.py       Consola
    ├── monitor.py       Monitor de CPU/RAM/jugadores
    ├── commands.py      Constructor de comandos
    ├── properties.py    Editor de server.properties
    ├── allowlist.py     Allowlist
    ├── packs.py         Packs / addons (orden + subpacks)
    ├── rawjson.py       Editor de los world_*_packs.json
    └── leveldat.py      Editor de level.dat
```

## Ejecutar en desarrollo

```bash
pip install -r requirements.txt
python main.py
```

Requiere Python 3.10+ (probado en 3.12).

## Crear el .exe a mano (Windows)

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --name BedrockManager --collect-all PyQt6 main.py
```

El ejecutable queda en `dist/BedrockManager.exe`. Para que abra más rápido,
puedes usar `--onedir` en lugar de `--onefile`.

## Generar el .exe automáticamente con GitHub Actions

Este repositorio incluye `.github/workflows/build.yml`, que compila el `.exe`
en Windows automáticamente:

- En cada **push a `main`/`master`** → genera el `.exe` como *artifact*
  (descárgalo desde la pestaña **Actions** del repositorio, dentro de la
  ejecución correspondiente).
- Al ejecutarlo **manualmente** desde la pestaña **Actions** (botón
  *Run workflow*).
- Al subir un **tag de versión** (`v1.0.0`, etc.) → además crea un *Release*
  con el `.exe` adjunto:

  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```

## Subir el proyecto a GitHub (primera vez)

```bash
git init
git add .
git commit -m "Primer commit: Bedrock Server Manager"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

Tras el push, abre la pestaña **Actions** y verás cómo se compila el `.exe`.
