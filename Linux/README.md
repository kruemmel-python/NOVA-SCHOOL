# Nova School Linux

Dieser Ordner ist der Linux-Startpunkt fuer Ubuntu und vergleichbare Distributionen.

Wichtig:
- Im Stammprojekt bleibt der eigentliche Quellcode im uebergeordneten Projektordner.
- `Linux/` ist dort die Linux-Laufzeitwurzel.
- Konfiguration, `.venv` und Laufzeitdaten koennen hier Linux-spezifisch liegen.
- Wenn `Linux/materialize_linux_project.py` ausgefuehrt wird, entsteht unter `Linux/project` zusaetzlich ein vollstaendiges eigenstaendiges Linux-Projekt.

## Zweck

Die Linux-Launcher in diesem Ordner starten Nova School mit:
- Linux-tauglichem `base_path` innerhalb von `Linux/`
- paketneutraler Pfadauflösung fuer `static/`, `wiki/`, `Docs/`, `LIT/` und `Model/`
- Linux-Shellskripten statt PowerShell

Es gibt damit zwei Betriebsarten:

- Launcher-Modus: `Linux/` startet den gemeinsamen Quellcode aus dem uebergeordneten Projekt.
- Standalone-Modus: `Linux/project` ist ein vollstaendig materialisiertes Linux-Projekt.

## Empfohlene Struktur

```text
nova_school_server/
├─ Linux/
│  ├─ start_server.sh
│  ├─ start_worker.sh
│  ├─ nova_linux_launch.py
│  ├─ nova_linux_worker_launch.py
│  └─ server_config.json.example
├─ static/
├─ wiki/
├─ Docs/
├─ LIT/
├─ Model/
└─ ...
```

## Server starten

```sh
cd /opt/nova-school/Linux
cp server_config.json.example server_config.json
./start_server.sh
```

## Worker starten

```sh
cd /opt/nova-school/Linux
./start_worker.sh --server http://127.0.0.1:8877 --worker-id ubuntu-worker-01 --token DEIN_TOKEN
```

## Ubuntu-Vorbereitung

```sh
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl
cd /opt/nova-school/Linux
python3 -m venv .venv
. .venv/bin/activate
pip install -r ../requirements.txt
```

## Modelle und lokale KI

Bevorzugte Linux-Pfade:
- LiteRT-LM: `/opt/nova-school/LIT`
- GGUF-Modelle: `/opt/nova-school/Model`
- optionaler `llama-server`: `/usr/local/bin/llama-server`

Die Laufzeit prueft sowohl Linux-spezifische Pfade aus `Linux/` als auch den gemeinsamen Projektordner.
Fuer LiteRT-LM werden unter Linux insbesondere `lit.linux_x86_64`, `lit` und danach die Windows-Dateinamen geprueft.
Wenn im Stammprojekt unter `LIT/` bereits eine Datei `lit.linux_x86_64` liegt, wird sie beim Materialisieren zusaetzlich nach `Linux/project/LIT/` uebernommen.
