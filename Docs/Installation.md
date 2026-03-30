# Nova School Server Installation

## Zweck dieses Dokuments

Diese Anleitung beschreibt die vollstaendige Installation des **Nova School Server** in der aktuell vorliegenden Codebasis. Sie ist auf einen stabilen Betrieb in Schulnetzen ausgerichtet und bildet die reale Implementierung des Projekts ab.

Linux-Hinweis:

- Fuer den Linux-spezifischen Startordner und den materialisierten Linux-Standalone siehe [Installation_Linux.md](Installation_Linux.md).

Wichtige Einordnung:

- Der Server ist ein lokaler Schulserver fuer Projektarbeit, lokale KI-Unterstuetzung, Material-Studio, Peer Review, Exporte, Freigaben und einen verteilten Playground.
- Der Einstiegspunkt ist `python -m nova_school_server`.
- Die Laufzeitdaten liegen **nicht** im Repo-Ordner, sondern im `data`-Verzeichnis neben dem Paketordner.
- Der primäre KI-Pfad ist **LiteRT-LM** im projektlokalen Ordner `LIT/`.
- `llama.cpp` bleibt als alternativer Fallback erhalten, ist aber nicht mehr der Standard in dieser Dokumentation.

## 1. Zielarchitektur

Empfohlene Basisarchitektur fuer produktive Umgebungen:

1. Ein dedizierter Server oder eine dedizierte VM fuer den Nova School Server.
2. Python `3.12` als Serverlaufzeit.
3. Docker oder Podman fuer den isolierten Runner-Betrieb.
4. Ein lokaler KI-Provider:
   `LiteRT-LM` mit `.litertlm`-Modell im Ordner `LIT/`.
5. Ein Reverse Proxy mit TLS vor dem HTTP-Server.
6. Ein eingeschraenktes Netzsegment fuer Lehr-/Schulbetrieb.

Fuer Entwicklung oder Laptop-Tests reicht auch:

- Windows 10/11
- Python `3.12`
- Docker Desktop
- `LiteRT-LM` direkt in `C:\nova_school_server\LIT`

## 2. Technische Voraussetzungen

## 2.1 Pflichtkomponenten

- Python `3.12`
- Zugriff auf dieses Repository

Der Server bringt die benoetigten Laufzeitbausteine inzwischen direkt im Projekt mit:

- eine eingebaute `SecurityPlane`-kompatible Schicht
- eine eingebaute `ToolSandbox`
- eine eingebaute `NovaAIProviderRuntime`-kompatible Platzhalterklasse

Das bedeutet:

- fuer den Standardbetrieb ist **keine** externe `Nova-shell`-Installation mehr noetig

## 2.2 Pflichtkomponenten fuer den empfohlenen Betrieb

- Docker Desktop oder Podman
- Genuegend lokaler Speicher fuer Modelle, Container-Images und Schulprojekte
- Reverse Proxy mit TLS
- Ein `LIT/`-Ordner mit LiteRT-Binary und Modell

Die Repository-Templates fuer den TLS-Pfad liegen unter:

- `deploy/reverse-proxy/Caddyfile`
- `deploy/reverse-proxy/nginx.conf`
- `deploy/reverse-proxy/README.md`

## 2.3 Primaerer KI-Stack: LiteRT-LM

Benoetigt:

- `lit.windows_x86_64.exe` oder eine native `lit`-Binary
- eine `.litertlm`-Modelldatei
- ein schreibbares Cache-/Home-Verzeichnis

Automatisch erkannte Standardorte:

- `C:\nova_school_server\LIT\lit.windows_x86_64.exe`
- `C:\nova_school_server\LIT\gemma-3n-E4B-it-int4.litertlm`
- allgemein `LIT/` im Projektordner
- explizit gesetzte Servereinstellungen
- danach erst aeltere Legacy-Pfade wie `D:\LIT`

## 2.4 Alternativer KI-Stack: llama.cpp

Unterstuetzt fuer `.gguf`-Modelle.

Benoetigt:

- eine `.gguf`-Datei im Ordner `Model` oder ein gesetzter `llamacpp_model_path`
- optional `llama-server.exe`

Hinweis:

- Wenn keine passende `llama-server`-Binary gefunden wird, kann der Server sie bei Bedarf aus dem aktuellen Release nachladen.

## 2.5 Optionale Host-Toolchains

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

Beispiel auf Windows:

- Paketordner: `C:\nova_school_server`
- Start aus `C:\`
- effektiver `base_path`: `C:\`

Dann verwendet der Server standardmaessig:

| Bereich | Pfad |
|---|---|
| Paketcode | `C:\nova_school_server` |
| Laufzeitdaten | `C:\data` |
| SQLite-Datenbank | `C:\data\school.db` |
| Nutzer-Workspaces | `C:\data\workspaces\users` |
| Gruppen-Workspaces | `C:\data\workspaces\groups` |
| interne Dokumente | `C:\data\docs` |
| Repo-Dokumentation | `C:\nova_school_server\Docs` |
| LiteRT-LM | `C:\nova_school_server\LIT` |
| alternative GGUF-Modelle | `C:\nova_school_server\Model` oder `C:\Model` |
| Konfigurationsdatei | `C:\server_config.json` |

Wichtig:

- Der Ordner `Docs` in diesem Repository ist **Entwickler-/Repo-Dokumentation**.
- Die interne Dokumentationsbibliothek der Anwendung liegt separat unter `data/docs`.

## 4. Installation Schritt fuer Schritt

## 4.1 Repository bereitstellen

Empfohlene Struktur auf Windows:

```text
C:\
  nova_school_server\
    LIT\
  data\                (wird beim ersten Start erzeugt)
  server_config.json   (optional)
```

Auf Linux entsprechend:

```text
/srv/
  nova_school_server/
    LIT/
  data/
```

## 4.2 Python pruefen

```powershell
python --version
```

Empfohlen:

```text
Python 3.12.x
```

## 4.3 Python-Abhaengigkeiten installieren

```powershell
python -m pip install -r requirements.txt
```

## 4.4 Eingebaute Laufzeitbausteine

Standard:

- keine zusaetzliche Security-/Sandbox-Installation notwendig
- der Server nutzt die eingebauten lokalen Laufzeitbausteine aus dem Repo

## 4.5 Container-Runtime installieren

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

## 4.6 LiteRT-LM in `LIT/` bereitstellen

Offizielle Herkunft der `lit`-Binary:

- LiteRT-LM Repository: `https://github.com/google-ai-edge/LiteRT-LM`
- die Windows-Binary `lit.windows_x86_64.exe` sollte aus dem offiziellen LiteRT-LM-Projekt oder dessen veroeffentlichten Desktop-Artefakten stammen

### Windows

Empfohlene Ablage:

```text
C:\nova_school_server\LIT\lit.windows_x86_64.exe
C:\nova_school_server\LIT\gemma-3n-E4B-it-int4.litertlm
```

### Linux

Empfohlene Ablage:

```text
/srv/nova_school_server/LIT/lit
/srv/nova_school_server/LIT/gemma-3n-E4B-it-int4.litertlm
```

Wichtig:

- Der Server bevorzugt `LIT/` automatisch.
- Du musst in den Servereinstellungen nichts eintragen, wenn Binary und Modell dort liegen.
- Das Cache-/Home-Verzeichnis wird ebenfalls automatisch aus `LIT/` abgeleitet, solange kein expliziter `litertlm_home_path` gesetzt ist.

Externer Modell-Download:

- Hugging Face: `https://huggingface.co/google/gemma-3n-E4B-it-litert-lm/tree/main`
- bevorzugte Datei fuer den Serverbetrieb: `gemma-3n-E4B-it-int4.litertlm`

Wichtig:

- das Repository ist gated
- vor dem Download muss sich die Institution oder Lehrkraft bei Hugging Face anmelden und Googles Gemma-Nutzungsbedingungen akzeptieren
- die `.litertlm`-Datei wird danach lokal nach `LIT/` kopiert und nicht in Git eingecheckt

## 4.7 Optionale Konfigurationsdatei anlegen

Datei:

```text
C:\server_config.json
```

Beispiel:

```json
{
  "host": "0.0.0.0",
  "port": 8877,
  "session_ttl_seconds": 43200,
  "run_timeout_seconds": 20,
  "live_run_timeout_seconds": 300,
  "tenant_id": "nova-school"
}
```

## 5. Server starten

### Windows

Empfohlen:

```powershell
Set-Location C:\
python -m nova_school_server
```

Alternativ:

```powershell
Set-Location C:\nova_school_server
.\start_server.ps1
```

### Linux

```bash
cd /srv/nova_school_server
./start_server.sh
```

Danach im Browser:

```text
http://127.0.0.1:8877
```

Fuer Produktivbetrieb gilt stattdessen:

- internen Server nur auf `127.0.0.1:8877` oder im internen Servernetz binden
- oeffentlich nur den TLS-Reverse-Proxy bereitstellen
- `server_public_host` auf die externe HTTPS-URL setzen, z. B. `https://nova.schule.local`

## 5.1 Beispiel fuer TLS mit Caddy

1. `deploy/reverse-proxy/Caddyfile` auf den echten Hostnamen anpassen
2. Caddy auf dem Server installieren
3. NOVA SCHOOL lokal auf `127.0.0.1:8877` starten
4. Caddy mit dieser Konfiguration starten

Der Proxy uebergibt:

- `Host`
- `X-Forwarded-Host`
- `X-Forwarded-Proto`

Damit setzt NOVA SCHOOL bei HTTPS automatisch `Secure` am Session-Cookie.

## 5.2 Beispiel fuer TLS mit Nginx

1. `deploy/reverse-proxy/nginx.conf` auf Domain und Zertifikatspfade anpassen
2. die Konfiguration in die Nginx-Site-Definition uebernehmen
3. NOVA SCHOOL intern auf `127.0.0.1:8877` betreiben
4. nur `443/tcp` nach aussen freigeben

## 6. Erststart pruefen

## 6.1 Demo-Accounts

| Benutzer | Passwort | Rolle |
|---|---|---|
| `admin` | `NovaSchool!admin` | Administration |
| `teacher` | `NovaSchool!teacher` | Lehrkraft |
| `student` | `NovaSchool!student` | Demo-Schueler |

Diese Passwoerter muessen in jeder echten Schulumgebung sofort ersetzt werden.

## 6.2 Serverstatus

Nach dem Login als `teacher` oder `admin`:

1. `Servereinstellungen` oeffnen
2. `Lokaler KI-Provider` pruefen
3. erwartet:
   - `Provider: LiteRT-LM`
   - Modellpfad in `LIT/`
   - Binary-Pfad in `LIT/`

## 6.3 Funktionstest fuer die lokale KI

In `Lokale KI-Codehilfe`:

- Modus: `Direkte Hilfe`
- Prompt: `Antworte nur mit OK!`

Erwartung:

- Antwort: `OK`

## 6.4 Funktionstest fuer Runner

In einem Python-Projekt:

```python
print("Hallo Nova School")
```

Dann:

- `Datei ausfuehren`

Erwartung:

- sichtbare Programmausgabe
- bei Lehrkraft/Admin zusaetzliche Container-Hinweise im Ausgabefeld
- bei Schuelern keine operativen Runner-Details

## 7. Empfohlene Servereinstellungen

| Einstellung | Empfehlung |
|---|---|
| KI-Provider | `litert-lm` |
| LiteRT-LM Backend | `cpu` |
| LiteRT-LM Idle | `45` Sekunden |
| Ausfuehrungs-Backend | `container` |
| Runtime | `docker` |
| Webzugriff fuer Schueler standardmaessig | deaktiviert |
| Reverse Proxy | vorgeschaltet |

`llama.cpp`-Einstellungen nur setzen, wenn bewusst ein GGUF-Fallback betrieben werden soll.

## 8. GitHub-Release und Distributionspakete

Die GitHub-Releases enthalten:

- Windows-Server-Paket
- Linux-Server-Paket
- generisches Distribution-ZIP
- Checksummen
- optional die Windows-`lit`-Binary als separates Asset

Die Release-ZIPs enthalten bewusst **keine** grossen lokalen Modellartefakte. Der Ordner `LIT/` wird scaffolded ausgeliefert und anschliessend lokal befuellt.

## 9. Typische Fehlerbilder

### Fehler: `Kein LiteRT-LM-Modell gefunden`

Pruefen:

- liegt eine `.litertlm`-Datei in `LIT/`?
- wurde versehentlich nur `Model/` statt `LIT/` befuellt?
- ist `litertlm_model_path` auf einen falschen Pfad gesetzt?

### Fehler: `LiteRT-LM-Binary nicht gefunden`

Pruefen:

- liegt `lit.windows_x86_64.exe` unter `LIT/`?
- ist der Binary-Pfad in den Servereinstellungen leer oder korrekt?
- auf Linux: existiert eine native `lit`-Binary?

### Fehler: `Input token ids are too long`

Dann ist der Material-Studio-Prompt fuer das Modell zu gross. Die aktuelle Implementierung kuerzt und retried bereits automatisch, aber lange Lehrerprompts oder sehr grosse Vorgabebloecke sollten trotzdem komprimiert werden.

### Fehler: `docker info` liefert einen 500-Fehler oder Timeout

Dann liegt das Problem in der Container-Runtime selbst, nicht im Nova-Server. Docker Desktop oder Podman neu starten, dann den Server neu starten.

## 10. Produktionshinweise fuer Lehranstalten

- HTTP niemals ungeschuetzt ins offene Netz stellen
- Reverse Proxy mit TLS und Logging verwenden
- Lehrer- und Admin-Zugaenge organisatorisch absichern
- Container-Images und LiteRT-Artefakte vor Unterrichtsbeginn vorladen
- Backups von `data/` regelmaessig und versioniert erstellen
- fuer groessere Deployments Linux-Server oder Linux-Worker bevorzugen

## 11. Weiterfuehrende Dokumente

- [Service.md](Service.md)
- [Readme.md](Readme.md)
- [Secure.md](Secure.md)
