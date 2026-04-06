# Nova School Server Service-Leitfaden

## Zweck dieses Dokuments

Dieses Dokument richtet sich an Servicetechniker, Systemhaeuser und IT-Abteilungen, die den **Nova School Server** so vorbereiten sollen, dass eine Schule danach ein vollstaendiges System uebernimmt, das im Alltag nur noch gestartet oder automatisch beim Booten gestartet werden muss.

Zielbild:

- ein zentraler Schulserver fuer `60-90` Schueler
- produktiver Betrieb mit `LiteRT-LM` als primaerem lokalen KI-Stack
- isolierte Runner fuer `Python`, `JavaScript`, `Node.js`, `C++`, `Java`, `Rust` und `HTML`
- HTTPS/TLS ueber Reverse Proxy
- Autostart ueber `systemd`
- vorinstallierte Laufzeit, vorgezogene Container-Images, vorab bereitgestelltes Modell

Dieses Dokument beschreibt bewusst den **empfohlenen Produktionspfad auf Linux**. Windows bleibt fuer Tests, Pilotinstallationen oder kleine Einzelsysteme moeglich, ist fuer `60-90` Schueler aber nicht die bevorzugte Zielarchitektur.

## 1. Betriebsannahmen fuer die Hardwareplanung

Die nachfolgenden Angaben sind keine Marketing-Zahlen, sondern auf die aktuelle Implementierung dieses Projekts abgestimmt.

Relevante Codebasis-Parameter:

- Default `run_timeout_seconds`: `20`
- Default `live_run_timeout_seconds`: `300`
- Default Runner-Backend: `container`
- Default Container-Limits pro Lauf:
  - RAM: `512m`
  - CPU: `1.5`
  - PIDs: `128`
- Default Scheduler:
  - global: `4`
  - student: `1`
  - teacher: `2`
  - admin: `3`

Fuer einen echten Schulbetrieb mit `60-90` Schuelern ist ein konservativeres Produktionsprofil sinnvoll:

- `60 Schueler`: global `8` gleichzeitige Containerlaeufe
- `90 Schueler`: global `12` gleichzeitige Containerlaeufe
- `student`: `1`
- `teacher`: `2`
- `admin`: `3`
- `container_memory_limit`: `512m`
- `container_cpu_limit`: `1.5`
- KI-Provider: `LiteRT-LM`
- LiteRT-LM-Backend: `cpu`

Diese Planung geht davon aus:

- es arbeiten ein bis zwei Klassen parallel
- nicht alle Schueler starten gleichzeitig rechenintensive Builds
- die KI wird primaer durch Lehrkraefte genutzt, nicht durch `90` Schueler gleichzeitig
- der Runner arbeitet kontrolliert ueber Scheduler und Containerlimits

Wenn die Schule sehr viel gleichzeitige KI-Nutzung, mehrere parallele Labore oder hoehere Runner-Grenzen plant, muss die Hardware entsprechend groesser ausfallen oder durch weitere Linux-Worker ergaenzt werden.

## 2. Mindesthardware fuer 60-90 Schueler

## 2.1 Mindestprofil und Empfehlung

| Komponente | 60 Schueler Mindestprofil | 60 Schueler Empfehlung | 90 Schueler Mindestprofil | 90 Schueler Empfehlung |
|---|---|---|---|---|
| CPU | `12` physische Kerne / `24` Threads | `16` physische Kerne / `32` Threads | `16` physische Kerne / `32` Threads | `24` physische Kerne / `48` Threads |
| RAM | `64 GB` ECC | `64-96 GB` ECC | `96 GB` ECC | `128 GB` ECC |
| System-/Datenlaufwerk | `2 x 960 GB SSD/NVMe` im RAID1 | `2 x 1.92 TB NVMe` im RAID1 | `2 x 1.92 TB NVMe` im RAID1 | `2 x 3.84 TB NVMe` im RAID1 |
| Netzwerk | `1 Gbit/s` | `2.5 Gbit/s` | `2.5 Gbit/s` | `2.5-10 Gbit/s` |
| KI | keine dedizierte GPU erforderlich | keine dedizierte GPU erforderlich | keine dedizierte GPU erforderlich | optional GPU nur bei spaeterem Spezialausbau |
| Strom | Online- oder Line-Interactive-USV | USV mit sauberem Shutdown | USV mit sauberem Shutdown | USV mit sauberem Shutdown |
| Formfaktor | dedizierter Tower- oder Rack-Server | Rack-Server mit ECC und Hot-Swap | Rack-Server mit ECC und Hot-Swap | Rack-Server mit ECC und Redundanz |

## 2.2 Nicht empfohlen

Folgende Plattformen sind fuer den Zielbereich `60-90` Schueler nicht als Hauptserver geeignet:

- Lehrer-Laptop
- Mini-PC ohne ECC-RAM
- USB-/Einzeldatentraeger ohne RAID
- Windows Desktop mit Docker Desktop als dauerhaftem Hauptserver
- virtuelle Maschinen ohne fest reservierte CPU- und RAM-Ressourcen

## 2.3 Warum diese Werte sinnvoll sind

Die Hardware muss nicht nur den Python-HTTP-Server tragen, sondern gleichzeitig:

- SQLite, Workspaces und Dateioperationen bedienen
- mehrere isolierte Containerlaeufe parallel starten
- Container-Images lokal halten
- das LiteRT-LM-Modell und dessen lokalen Cache tragen
- Reverse Proxy, TLS und Schulnetzverkehr stabil verarbeiten

Wichtige Groessenordnungen:

- das empfohlene Modell `gemma-3n-E4B-it-int4.litertlm` ist mehrere Gigabyte gross
- LiteRT-LM legt zusaetzlich lokalen Cache an
- Container-Images fuer `python`, `node`, `gcc`, `java` und `rust` benoetigen ebenfalls lokalen Speicher
- Workspaces, Reviews, Exporte und Snapshots wachsen ueber das Schuljahr

Deshalb ist ein gespiegelt aufgebautes SSD-/NVMe-System fuer Produktivbetrieb Pflicht.

## 3. Zielarchitektur fuer den Servicetechniker

Empfohlene Produktionsarchitektur:

1. Ein dedizierter Ubuntu-Server `24.04 LTS`
2. Das Repo liegt unter `/srv/nova_school_server`
3. Der Laufzeitdatenpfad liegt unter `/srv/data`
4. Die Runtime-Konfiguration liegt unter `/srv/server_config.json`
5. LiteRT-LM liegt unter `/srv/nova_school_server/LIT`
6. Docker Engine stellt die isolierten Runner
7. Caddy oder Nginx terminiert HTTPS auf `443`
8. Der Nova School Server selbst lauscht nur intern auf `127.0.0.1:8877`
9. `systemd` startet Docker, Caddy und Nova School automatisch beim Booten

Das Ergebnis nach Abschluss dieser Anleitung:

- Server startet automatisch
- Zertifikate oder TLS-Offload sind aktiv
- Container-Images sind bereits lokal gepullt
- LiteRT-LM-Binary und Modell sind bereits lokal vorhanden
- Basisfunktion ist getestet
- die Schule muss das System spaeter nur noch betreiben, nicht mehr technisch aufbauen

## 4. Infrastruktur-Voraussetzungen vor der Installation

Vor Beginn muessen folgende Punkte geklaert sein:

- fester Hostname, z. B. `nova.schule.local`
- feste IP-Adresse oder DHCP-Reservierung
- DNS-Eintrag fuer den kuenftigen HTTPS-Namen
- Entscheidung fuer TLS:
  - internes Zertifikat der Schul-/Traeger-PKI
  - oder Caddy mit oeffentlich erreichbarem DNS und offenen Ports `80/443`
- Backup-Ziel fuer `/srv/data`
- USV-Anbindung
- Administrationszugang per SSH

Empfohlene Freigaben:

- extern/Schul-LAN: nur `443/tcp`
- optional `80/tcp` waehrend ACME-/Caddy-Zertifikatsbezug
- kein direkter externer Zugriff auf `8877/tcp`

## 5. Vollstaendige Installation auf Ubuntu Server 24.04 LTS

## 5.1 Ubuntu installieren

Empfohlene Basis:

- `Ubuntu Server 24.04 LTS`
- lokale SSD-/NVMe-Spiegelung bereits auf RAID-Controller oder per Software-RAID eingerichtet
- SSH-Server direkt bei der OS-Installation aktivieren

Empfohlene Partitionsidee:

- OS und Anwendung auf dem RAID1-Systemvolume
- ausreichend freier Platz fuer `/srv`
- kein Betrieb auf einem einzelnen USB- oder Consumer-SATA-Laufwerk

Nach dem ersten Login:

```bash
sudo apt update
sudo apt upgrade -y
sudo timedatectl set-timezone Europe/Berlin
sudo apt install -y python3 python3-venv python3-pip git curl unzip ca-certificates gnupg lsb-release caddy
```

## 5.2 Technischen Dienstnutzer und Verzeichnisse anlegen

```bash
sudo useradd --system --create-home --home-dir /srv/nova --shell /bin/bash nova
sudo mkdir -p /srv
sudo mkdir -p /srv/data
sudo mkdir -p /srv/nova_school_server
sudo chown -R nova:nova /srv/data /srv/nova_school_server
```

## 5.3 Projekt nach `/srv/nova_school_server` kopieren

Moegliche Wege:

- Git-Clone
- GitHub-Release-ZIP entpacken
- internes Distributionspaket aus dem Schultraeger

Beispiel mit Git:

```bash
cd /srv
sudo -u nova git clone https://github.com/kruemmel-python/NOVA-SCHOOL.git nova_school_server
```

Wenn mit ZIP geliefert:

```bash
cd /srv
sudo -u nova unzip NOVA-SCHOOL-linux-package.zip -d nova_school_server
```

## 5.4 Python-Umgebung im Projekt vorbereiten

```bash
cd /srv/nova_school_server
sudo -u nova python3 -m venv .venv
sudo -u nova ./.venv/bin/python -m pip install --upgrade pip
sudo -u nova ./.venv/bin/python -m pip install -r requirements.txt
```

## 5.5 Docker Engine installieren

Empfohlen ist die offizielle Docker-Engine fuer Ubuntu, nicht ein ungeprueftes Alt-Paket.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo \"${UBUNTU_CODENAME:-$VERSION_CODENAME}\") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker nova
sudo systemctl enable --now docker
sudo docker info
```

Wenn die Schule statt Docker Podman standardisiert, muss die Container-Runtime spaeter in den Servereinstellungen entsprechend gesetzt werden. Fuer die hier beschriebene Referenzinstallation wird Docker verwendet.

## 5.6 Container-Images vorab laden

Damit die Schule spaeter nicht erst waehrend des Unterrichts Images nachlaedt:

```bash
sudo docker pull python:3.12-slim
sudo docker pull node:20-bookworm-slim
sudo docker pull gcc:14
sudo docker pull eclipse-temurin:21
sudo docker pull rust:1.81
```

## 5.7 LiteRT-LM vorbereiten

Der primaere KI-Pfad dieses Projekts ist `LiteRT-LM`.

Offizielle Herkunft der Binary:

- LiteRT-LM Repository: [google-ai-edge/LiteRT-LM](https://github.com/google-ai-edge/LiteRT-LM)

Empfohlenes Servermodell:

- Hugging Face: [google/gemma-3n-E4B-it-litert-lm](https://huggingface.co/google/gemma-3n-E4B-it-litert-lm/tree/main)
- bevorzugte Datei: `gemma-3n-E4B-it-int4.litertlm`

Wichtig:

- das Modell-Repository ist gated
- vor dem Download muessen Anmeldung und Gemma-Lizenzfreigabe erfolgt sein

Verzeichnis vorbereiten:

```bash
sudo -u nova mkdir -p /srv/nova_school_server/LIT
```

Dateien ablegen:

```text
/srv/nova_school_server/LIT/lit
/srv/nova_school_server/LIT/gemma-3n-E4B-it-int4.litertlm
```

Binary ausfuehrbar machen:

```bash
sudo chmod 0755 /srv/nova_school_server/LIT/lit
sudo chown -R nova:nova /srv/nova_school_server/LIT
```

Hinweis:

- der Server erkennt `LIT/` automatisch
- eine zusaetzliche externe `Nova-shell`-Installation ist nicht mehr erforderlich

## 5.8 Runtime-Konfiguration anlegen

Datei:

```text
/srv/server_config.json
```

Beispiel:

```json
{
  "host": "127.0.0.1",
  "port": 8877,
  "session_ttl_seconds": 43200,
  "run_timeout_seconds": 20,
  "live_run_timeout_seconds": 300,
  "tenant_id": "nova-school",
  "school_name": "Nova School Server"
}
```

Eigentuemer setzen:

```bash
sudo chown nova:nova /srv/server_config.json
```

## 5.9 systemd-Service fuer Nova School anlegen

Datei:

```text
/etc/systemd/system/nova-school.service
```

Inhalt:

```ini
[Unit]
Description=Nova School Server
After=network-online.target docker.service
Wants=network-online.target docker.service

[Service]
Type=simple
User=nova
Group=nova
WorkingDirectory=/srv/nova_school_server
ExecStart=/srv/nova_school_server/start_server.sh
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
```

Service aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nova-school.service
```

## 5.10 Reverse Proxy und TLS einrichten

Im Repository liegen Vorlagen:

- `deploy/reverse-proxy/Caddyfile`
- `deploy/reverse-proxy/nginx.conf`

Empfohlene Variante fuer eine einfache Schulinstallation:

- Caddy vor den internen Server schalten
- Nova School nur auf `127.0.0.1:8877` betreiben
- nur `443/tcp` fuer Clients freigeben

Minimaler Caddy-Block:

```caddyfile
nova.schule.local {
    encode zstd gzip
    reverse_proxy 127.0.0.1:8877 {
        header_up Host {host}
        header_up X-Forwarded-Host {host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

Aktivieren:

```bash
sudo cp /srv/nova_school_server/deploy/reverse-proxy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl enable --now caddy
sudo systemctl reload caddy
```

Wenn die Schule keine oeffentlich erreichbare DNS-/ACME-Strecke nutzt, muss ein intern vertrautes Zertifikat oder eine interne PKI verwendet werden.

## 5.11 Nova School erstmals starten

```bash
sudo systemctl start nova-school.service
sudo systemctl status nova-school.service
```

Logs pruefen:

```bash
journalctl -u nova-school.service -f
```

## 6. Erstkommissionierung durch den Servicetechniker

Die nachfolgenden Schritte gehoeren zur technischen Bereitstellung, damit die Schule spaeter nur noch mit dem fertigen System arbeitet.

## 6.1 Erstlogin

Im Browser:

```text
https://nova.schule.local
```

Seed-Zugaenge:

| Benutzer | Passwort | Rolle |
|---|---|---|
| `admin` | `NovaSchool!admin` | Administration |
| `teacher` | `NovaSchool!teacher` | Lehrkraft |
| `student` | `NovaSchool!student` | Demo-Schueler |

Pflicht nach dem Erstlogin:

- `admin`-Kennwort aendern
- `teacher`-Kennwort aendern
- `student`-Demokonto fuer Produktivbetrieb deaktivieren oder ersetzen

## 6.2 Servereinstellungen fuer 60-90 Schueler setzen

Als `admin` in `Servereinstellungen` mindestens setzen:

| Einstellung | 60 Schueler | 90 Schueler |
|---|---|---|
| `school_name` | Schulname | Schulname |
| `server_public_host` | `https://nova.schule.local` | `https://nova.schule.local` |
| `ai_provider` | `litert-lm` | `litert-lm` |
| `litertlm_backend` | `cpu` | `cpu` |
| `runner_backend` | `container` | `container` |
| `container_runtime` | `docker` | `docker` |
| `container_memory_limit` | `512m` | `512m` |
| `container_cpu_limit` | `1.5` | `1.5` |
| `scheduler_max_concurrent_global` | `8` | `12` |
| `scheduler_max_concurrent_student` | `1` | `1` |
| `scheduler_max_concurrent_teacher` | `2` | `2` |
| `scheduler_max_concurrent_admin` | `3` | `3` |
| `ondevice_max_tokens` | `1024` | `1024` |

## 6.3 Basisfunktion testen

### LiteRT-LM testen

Als `teacher` oder `admin` in `Lokale KI-Codehilfe`:

- Modus `Direkte Hilfe`
- Prompt: `Antworte nur mit OK!`

Erwartung:

- Antwort `OK`

### Python-Runner testen

```python
print("Hallo Nova School")
```

Erwartung:

- sichtbare Ausgabe
- bei `teacher` oder `admin` zusaetzliche Runner-Hinweise
- bei `student` keine sensiblen Betriebsdetails

### C++-Runner testen

```cpp
#include <iostream>

int main() {
    std::cout << "Hallo C++" << std::endl;
    return 0;
}
```

Erwartung:

- erfolgreiche Kompilierung
- sichtbare Ausgabe `Hallo C++`

## 6.4 Modell und Images vorwaermen

Damit die Schule beim ersten echten Einsatz keine Kaltstarts erlebt:

1. mindestens eine KI-Anfrage erfolgreich ausfuehren
2. mindestens je einen Testlauf fuer `Python` und `C++` ausfuehren
3. optional auch `Node.js`, `Java` und `Rust` einmal starten

So sind Modell-Cache, Docker-Images und grundlegende Laufzeitpfade bereits vorbereitet.

## 7. Abnahmecheckliste fuer den Servicetechniker

Vor der Uebergabe muessen folgende Punkte abgehakt sein:

- Serverhardware installiert und dokumentiert
- RAID1 aktiv
- USV aktiv
- Ubuntu `24.04 LTS` installiert und aktualisiert
- SSH-Zugang dokumentiert
- Docker Engine laeuft fehlerfrei
- `docker info` funktioniert ohne Fehler
- alle benoetigten Container-Images lokal vorhanden
- `LIT/` enthaelt Binary und Modell
- Nova School startet ueber `systemd`
- Caddy oder Nginx terminiert HTTPS
- `server_public_host` korrekt gesetzt
- Seed-Passwoerter ersetzt
- Test fuer KI erfolgreich
- Test fuer Python-Runner erfolgreich
- Test fuer C++-Runner erfolgreich
- Backup fuer `/srv/data` eingerichtet
- technisches Betriebsprotokoll an die Schule uebergeben

## 8. Backup- und Wartungsempfehlungen

Mindestens sichern:

- `/srv/data`
- `/srv/server_config.json`
- optional die lokalen `LIT/`-Artefakte, wenn die Schule keine erneuten Downloads wuenscht

Wartungsrhythmus:

- monatliche OS-Sicherheitsupdates
- regelmaessige Docker- und Caddy-Updates
- pruefen, ob LiteRT-LM-Binary oder Modell bewusst aktualisiert werden sollen
- nach jedem Update kurzer Funktionstest fuer KI und Runner

## 9. Skalierungsgrenzen und Ausbaustufen

Dieses Dokument deckt einen einzelnen Hauptserver fuer `60-90` Schueler ab.

Ein Ausbau ist sinnvoll, wenn:

- mehr als zwei Klassen gleichzeitig intensiv arbeiten
- mehrere Lehrkraefte parallel Material-Studio mit langen KI-Laeufen verwenden
- deutlich hoehere Scheduler-Grenzen als `8` oder `12` benoetigt werden
- viele zusaetzliche Exporte, Reviews oder Gruppenprojekte anfallen

Dann sind sinnvolle naechste Schritte:

- mehr CPU-Kerne und mehr RAM
- groessere NVMe-Spiegelung
- zusaetzliche Linux-Worker fuer Playground/Runner
- organisatorische Trennung von Hauptserver und Worker-Hosts

## 10. Offizielle Bezugsquellen

- Docker Engine fuer Ubuntu: [Docker Engine installation on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- Caddy Automatic HTTPS: [Automatic HTTPS - Caddy Documentation](https://caddyserver.com/docs/automatic-https)
- LiteRT-LM Projekt: [google-ai-edge/LiteRT-LM](https://github.com/google-ai-edge/LiteRT-LM)
- Empfohlenes LiteRT-LM-Modell: [google/gemma-3n-E4B-it-litert-lm](https://huggingface.co/google/gemma-3n-E4B-it-litert-lm/tree/main)

## 11. Verwandte Dokumente

- [Installation.md](Installation.md)
- [Secure.md](Secure.md)
- [Readme.md](Readme.md)
