# Nova School Server auf Linux

## Ziel

Diese Anleitung beschreibt den Linux-Betrieb auf Ubuntu oder vergleichbaren Distributionen.

Empfohlener Zielpfad:

```text
/opt/nova-school
```

Der Linux-spezifische Laufzeitordner in diesem Repository ist:

```text
Linux/
```

Dort kann auch ein vollstaendiges, eigenstaendiges Linux-Projekt materialisiert werden:

```sh
cd /opt/nova-school
python3 Linux/materialize_linux_project.py
```

Danach liegt das eigenstaendige Linux-Projekt unter:

```text
/opt/nova-school/Linux/project
```

Wenn im gemeinsamen Projekt bereits `LIT/lit.linux_x86_64` vorhanden ist, wird diese Binary beim Materialisieren automatisch nach `Linux/project/LIT/lit.linux_x86_64` uebernommen.

## Voraussetzungen

- Ubuntu 24.04 LTS oder vergleichbare Linux-Distribution
- Python 3.12
- Docker oder Podman fuer isolierte Runner
- optional `lit` in `LIT/`
- optional `llama-server` fuer `.gguf`

## Pakete installieren

```sh
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl docker.io
```

Optional fuer Podman statt Docker:

```sh
sudo apt install -y podman
```

## Python-Abhaengigkeiten

Im gemeinsamen Projekt:

```sh
cd /opt/nova-school
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Oder im materialisierten Linux-Projekt:

```sh
cd /opt/nova-school/Linux/project
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## LiteRT-LM und Modelle

Empfohlene Linux-Ablage:

```text
/opt/nova-school/LIT/lit.linux_x86_64
/opt/nova-school/LIT/gemma-3n-E4B-it-int4.litertlm
/opt/nova-school/Model/dein-modell.gguf
```

Automatisch geprueft werden unter Linux insbesondere:

- `LIT/lit.linux_x86_64`
- `LIT/lit`
- `LIT/lit.exe`
- `LIT/lit.windows_x86_64.exe`
- `lit` auf `PATH`
- `Model/*.gguf`
- `LIT/*.litertlm`

## Serverstart

Direkt aus dem Linux-Startordner:

```sh
cd /opt/nova-school/Linux
cp server_config.json.example server_config.json
./start_server.sh
```

Oder aus dem materialisierten Linux-Projekt:

```sh
cd /opt/nova-school/Linux/project
cp server_config.json.example server_config.json
./start_server.sh
```

Danach ist die Weboberflaeche standardmaessig unter folgendem Pfad erreichbar:

```text
http://127.0.0.1:8877
```

## Datenpfade

Wenn aus `Linux/` gestartet wird:

- Basis: `/opt/nova-school/Linux`
- Daten: `/opt/nova-school/Linux/data`
- Datenbank: `/opt/nova-school/Linux/data/school.db`

Wenn aus `Linux/project` gestartet wird:

- Basis: `/opt/nova-school/Linux/project`
- Daten: `/opt/nova-school/Linux/project/data`
- Datenbank: `/opt/nova-school/Linux/project/data/school.db`

Die statischen Webdateien und der Paketcode werden plattformneutral aufgeloest. Dadurch funktionieren HTML-Vorschau und `static/index.html` jetzt auch dann, wenn kein Windows-Pfad wie `C:\...` existiert.
