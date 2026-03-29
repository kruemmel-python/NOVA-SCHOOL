# Nova School Server Installation

## Zweck dieses Dokuments

Diese Anleitung beschreibt die vollstaendige Installation des **Nova School Server** in der aktuell vorliegenden Codebasis. Sie ist auf einen stabilen Betrieb in Schulnetzen ausgerichtet und bildet die reale Implementierung des Projekts ab.

Wichtige Einordnung:

- Der Server ist ein lokaler Schulserver fuer Projektarbeit, lokale KI-Unterstuetzung, Material-Studio, Peer Review, Exporte, Freigaben und einen verteilten Playground.
- Der Einstiegspunkt ist `python -m nova_school_server`.
- Die Laufzeitdaten liegen **nicht** im Repo-Ordner, sondern im `data`-Verzeichnis neben dem Paketordner.
- Die Standard-Konfiguration ist fuer lokale Testsysteme geeignet. Fuer produktive Schulumgebungen sind zusaetzliche Haertungsmassnahmen erforderlich. Diese stehen in [Secure.md](Secure.md).

## 1. Zielarchitektur

Empfohlene Basisarchitektur fuer produktive Umgebungen:

1. Ein dedizierter Server oder eine dedizierte VM fuer den Nova School Server.
2. Python `3.12` als Serverlaufzeit.
3. Docker oder Podman fuer den isolierten Runner-Betrieb.
4. Ein lokaler KI-Provider:
   `LiteRT-LM` mit `.litertlm`-Modell oder `llama.cpp` mit `.gguf`-Modell.
5. Ein Reverse Proxy mit TLS vor dem HTTP-Server.
6. Ein eingeschraenktes Netzsegment fuer Lehr-/Schulbetrieb.

Fuer reine Entwicklung oder Laptop-Tests reicht auch:

- Windows 10/11
- Python `3.12`
- optional Docker Desktop
- optional `LiteRT-LM` in `D:\LIT`

## 2. Technische Voraussetzungen

## 2.1 Pflichtkomponenten

- Python `3.12`
- Zugriff auf dieses Repository
- Zugriff auf die **Nova-shell**-Laufzeit

Der Server laedt zur Laufzeit folgende Klassen aus Nova-shell:

- `nova.runtime.security.SecurityPlane`
- `nova.agents.sandbox.ToolSandbox`
- `nova_shell.NovaAIProviderRuntime`

Das bedeutet:

- Entweder sind `nova` und `nova_shell` bereits im aktiven Python-Interpreter installiert.
- Oder `NOVA_SHELL_PATH` zeigt auf ein ausgechecktes Nova-shell-Repository.

## 2.2 Empfohlene Pflichtkomponenten fuer produktiven Betrieb

- Docker Desktop oder Podman
- Genuegend lokaler Speicher fuer Modelle, Container-Images und Schulprojekte
- Reverse Proxy mit TLS

## 2.3 Optionale KI-Komponenten

### LiteRT-LM

Empfohlen, wenn eine schnelle lokale Inferenz mit `.litertlm`-Modellen genutzt werden soll.

Benoetigt:

- `lit.windows_x86_64.exe` oder kompatible `lit`-Binary
- eine `.litertlm`-Modelldatei
- ein schreibbares Cache-/Home-Verzeichnis

Vom Server automatisch erkannte Standardorte:

- `D:\LIT\lit.windows_x86_64.exe`
- `D:\LIT\lit.exe`
- `.litertlm`-Dateien im Ordner `Model`
- `.litertlm`-Dateien in `D:\LIT`

### llama.cpp

Empfohlen, wenn ein `.gguf`-Modell verwendet werden soll.

Benoetigt:

- eine `.gguf`-Datei im Ordner `Model` oder ein gesetzter `llamacpp_model_path`
- optional `llama-server.exe`

Hinweis:

- Wenn keine passende `llama-server`-Binary gefunden wird, kann der Server sie bei Bedarf aus dem aktuellen Release nachladen.

## 2.4 Optionale Host-Toolchains

Nur relevant, wenn der **unsichere Host-Prozess-Runner** explizit aktiviert wird. Standardmaessig ist dieser Modus deaktiviert.

Dann koennen lokal benoetigt werden:

- `python`
- `node`
- `npm`
- `g++` oder `clang++`
- `javac` und `java`
- `rustc` oder `cargo`

Fuer den empfohlenen Container-Betrieb sind diese Toolchains auf dem Host **nicht** erforderlich.

## 3. Verzeichnislayout und Pfadlogik

Der Einstiegspunkt `__main__.py` bestimmt den `base_path` als **Elternordner des Paketverzeichnisses**.

Beispiel:

- Paketordner: `H:\nova_school_server`
- Start aus `H:\`
- effektiver `base_path`: `H:\`

Dann verwendet der Server standardmaessig:

| Bereich | Pfad |
|---|---|
| Paketcode | `H:\nova_school_server` |
| Laufzeitdaten | `H:\data` |
| SQLite-Datenbank | `H:\data\school.db` |
| Nutzer-Workspaces | `H:\data\workspaces\users` |
| Gruppen-Workspaces | `H:\data\workspaces\groups` |
| interne Dokumente | `H:\data\docs` |
| Repo-Dokumentation | `H:\nova_school_server\Docs` |
| Modelle | `H:\nova_school_server\Model` oder `H:\Model` |
| Konfigurationsdatei | `H:\server_config.json` |

Wichtig:

- Der Ordner `Docs` in diesem Repository ist **Entwickler-/Repo-Dokumentation**.
- Die interne Dokumentationsbibliothek der Anwendung liegt separat unter `data/docs`.

## 4. Installation Schritt fuer Schritt

## 4.1 Repository bereitstellen

Empfohlene Struktur auf Windows:

```text
H:\
  nova_school_server\
  Nova-shell-main\
  data\          (wird beim ersten Start erzeugt)
  server_config.json   (optional)
```

Wenn das Repo bereits unter `H:\nova_school_server` liegt, ist keine weitere Umstrukturierung noetig.

## 4.2 Python pruefen

```powershell
python --version
```

Empfohlen:

```text
Python 3.12.x
```

## 4.3 Nova-shell verfuegbar machen

### Variante A: Nova-shell per Umgebungsvariable anbinden

```powershell
$env:NOVA_SHELL_PATH = 'H:\Nova-shell-main'
```

### Variante B: Nova-shell im aktiven Interpreter installiert

Dann ist keine zusaetzliche Pfadangabe noetig.

Praktischer Hinweis:

- Wenn der Server beim Start meldet, dass `Nova-shell classes could not be loaded`, fehlt entweder `NOVA_SHELL_PATH` oder die Nova-shell-Pakete sind im Interpreter nicht vorhanden.

## 4.4 Container-Runtime installieren

Empfohlen:

- Docker Desktop auf Windows
- alternativ Podman

Nach der Installation pruefen:

```powershell
docker info
```

oder

```powershell
podman info
```

Der Server verwendet standardmaessig:

- Backend: `container`
- Runtime: `docker`

## 4.5 KI-Backend installieren

### Variante A: LiteRT-LM

1. Binary herunterladen und ablegen, z. B.:

```text
D:\LIT\lit.windows_x86_64.exe
```

2. Modell ablegen, z. B.:

```text
D:\LIT\gemma-3n-E4B-it-int4.litertlm
```

oder

```text
H:\nova_school_server\Model\gemma-3n-E4B-it-int4.litertlm
```

3. Optional einen Cache-/Home-Pfad vorsehen:

```text
D:\LIT
```

### Variante B: llama.cpp

1. `.gguf`-Modell in den Modellordner legen:

```text
H:\nova_school_server\Model\dein-modell.gguf
```

2. Optional `llama-server.exe` konfigurieren.

3. Wenn keine Binary vorhanden ist, kann der Server sie bei passendem Backend nachladen.

## 4.6 Optionale Konfigurationsdatei anlegen

Datei:

```text
H:\server_config.json
```

Beispiel:

```json
{
  "host": "0.0.0.0",
  "port": 8877,
  "session_ttl_seconds": 43200,
  "run_timeout_seconds": 20,
  "live_run_timeout_seconds": 300,
  "tenant_id": "nova-school",
  "nova_shell_path": "H:\\Nova-shell-main"
}
```

Diese Datei steuert nur die Runtime-Dateikonfiguration. Weitere Servereinstellungen werden in der Datenbank gespeichert und ueber die Anwendung verwaltet.

## 4.7 Alternative Konfiguration per Umgebungsvariablen

Unterstuetzte Variablen:

| Variable | Bedeutung |
|---|---|
| `NOVA_SCHOOL_HOST` | Bind-Adresse |
| `NOVA_SCHOOL_PORT` | HTTP-Port |
| `NOVA_SCHOOL_SESSION_TTL` | Session-TTL in Sekunden |
| `NOVA_SCHOOL_RUN_TIMEOUT` | Timeout fuer Direktlaeufe |
| `NOVA_SCHOOL_LIVE_RUN_TIMEOUT` | Timeout fuer Live-Laeufe |
| `NOVA_SCHOOL_TENANT` | Tenant-ID |
| `NOVA_SCHOOL_NAME` | Schulname |
| `NOVA_SHELL_PATH` | Pfad zur Nova-shell-Laufzeit |

## 4.8 Server starten

Wichtiger Punkt:

- Der Modulstart muss aus dem **Elternordner** des Paketverzeichnisses erfolgen.

Empfohlener Start:

```powershell
Set-Location H:\
python -m nova_school_server
```

Alternative, wenn man im Repo-Ordner bleiben will:

```powershell
$env:PYTHONPATH = 'H:\'
python -m nova_school_server
```

## 4.9 Erwartete Startausgabe

Bei erfolgreichem Start meldet der Server in etwa:

```text
Nova School Server lauscht auf 0.0.0.0:8877
Lokal: http://127.0.0.1:8877
Im LAN: http://<server-ip>:8877
Seed-Benutzer: admin/NovaSchool!admin, teacher/NovaSchool!teacher, student/NovaSchool!student
```

## 4.10 Erster Login

Standard-Seed-Benutzer:

| Benutzer | Passwort | Rolle |
|---|---|---|
| `admin` | `NovaSchool!admin` | Administration |
| `teacher` | `NovaSchool!teacher` | Lehrkraft |
| `student` | `NovaSchool!student` | Demo-Schueler |

Wichtiger Sicherheitshinweis:

- Diese Kennwoerter muessen in produktiven Umgebungen sofort geaendert werden.

## 5. Erste Basiskonfiguration nach dem Start

Nach dem ersten Login sollte mindestens Folgendes gesetzt werden:

1. Demo-Kennwoerter aendern.
2. Schulname setzen.
3. Oeffentlichen Hostnamen setzen, falls Zertifikatslinks oder externe Freigaben genutzt werden.
4. KI-Provider festlegen:
   `auto`, `litert-lm` oder `llama.cpp`
5. Modellpfade pruefen.
6. Container-Runtime und Container-Images pruefen.
7. Web-Proxy setzen, falls Schuelerlaeufe nur ueber Proxy ins Netz duerfen.

## 6. Standardwerte der wichtigsten Betriebsparameter

| Bereich | Standardwert |
|---|---|
| Host | `0.0.0.0` |
| Port | `8877` |
| Session-TTL | `43200` Sekunden |
| Direktlauf-Timeout | `20` Sekunden |
| Live-Timeout | `300` Sekunden |
| Runner-Backend | `container` |
| Container-Runtime | `docker` |
| Python-Image | `python:3.12-slim` |
| Node-Image | `node:20-bookworm-slim` |
| C++-Image | `gcc:14` |
| Java-Image | `eclipse-temurin:21` |
| Rust-Image | `rust:1.81` |
| Container RAM | `512m` |
| Container CPU | `1.5` |
| Container PIDs | `128` |
| Container tmpfs | `64m` |
| Seccomp | aktiviert |
| LiteRT-LM Backend | `cpu` |
| LiteRT-LM Idle | `45` Sekunden |
| llama.cpp Backend | `vulkan` |
| llama.cpp Kontext | `4096` |
| llama.cpp GPU-Layer | `99` |

## 7. Empfohlener KI-Setup fuer Schule und Laptop-Test

### Empfohlener Test-Setup mit LiteRT-LM

- Binary:
  `D:\LIT\lit.windows_x86_64.exe`
- Modell:
  `D:\LIT\gemma-3n-E4B-it-int4.litertlm`
- Provider:
  `litert-lm`
- Backend:
  `cpu`

### Empfohlener produktiver Setup

- lokaler KI-Server ohne Cloud-Zwang
- pregeladene Modelle im internen Speicherpfad
- kein Modell-Download waehrend des Unterrichts
- ggf. dedizierter Server mit schneller CPU/GPU

## 8. Betriebsverifikation

Nach erfolgreicher Installation sollten diese Punkte funktionieren:

1. Login unter `http://127.0.0.1:8877`
2. Projektliste sichtbar
3. Datei-Lauf in einem Demo-Projekt
4. Material-Studio fuer Lehrkraft
5. Direkte KI-Hilfe
6. Speichern von Servereinstellungen

## 9. Typische Fehlerbilder und Behebung

### Fehler: `No module named nova_school_server`

Ursache:

- Start aus dem Paketordner statt aus dem Elternordner.

Loesung:

```powershell
Set-Location H:\
python -m nova_school_server
```

### Fehler: `Nova-shell classes could not be loaded`

Ursache:

- Nova-shell ist weder installiert noch ueber `NOVA_SHELL_PATH` erreichbar.

Loesung:

- `NOVA_SHELL_PATH` korrekt setzen
- oder Nova-shell in denselben Interpreter installieren

### Fehler: `Kein LiteRT-LM-Modell gefunden`

Loesung:

- `.litertlm` in `Model` oder `D:\LIT` ablegen
- oder `litertlm_model_path` setzen

### Fehler: `LiteRT-LM-Binary nicht gefunden`

Loesung:

- `lit.windows_x86_64.exe` nach `D:\LIT` legen
- oder `litertlm_binary_path` setzen

### Fehler: `Kein GGUF-Modell gefunden`

Loesung:

- `.gguf` in `Model` ablegen
- oder `llamacpp_model_path` setzen

### Fehler: Container startet nicht

Loesung:

1. `docker info` oder `podman info` pruefen
2. Runtime neu starten
3. fehlende Images automatisch ziehen lassen oder vorab manuell laden

## 10. Backup- und Betriebsdaten

Fuer Backups mindestens sichern:

- `data/school.db`
- `data/workspaces`
- `data/public_shares`
- `data/exports`
- `data/worker_dispatch`
- `server_config.json`

Empfehlung:

- taegliches Dateisystem-Backup
- zusaetzliche Versionierung fuer Konfiguration und Schulvorlagen

## 11. Empfohlene Schritte vor Inbetriebnahme in Lehranstalten

1. TLS per Reverse Proxy aktivieren.
2. Demo-Benutzerkennwoerter aendern oder Demo-Konten entfernen.
3. Rollen und Berechtigungen pruefen.
4. `deploy.use` deaktivieren, wenn keine oeffentlichen Shares erlaubt sind.
5. `unsafe_process_backend_enabled` deaktiviert lassen.
6. Containerbetrieb als Standard festschreiben.
7. Webzugriff nur bei Bedarf und moeglichst ueber Proxy freigeben.
8. Betriebs- und Datenschutzdokumentation mit [Secure.md](Secure.md) abstimmen.
