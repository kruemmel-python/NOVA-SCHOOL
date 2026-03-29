# Nova School Server

Ein lokaler Schulserver fuer Programmierunterricht, Projektarbeit und KI-gestuetzte Unterrichtsvorbereitung.

Der **Nova School Server** verbindet einen browserbasierten Arbeitsbereich mit lokalen Runnern, rollenbasierter Rechtevergabe, Peer Review, Offline-Dokumentation, verteilten Playground-Szenarien und lokalem KI-Support. Der primaere KI-Pfad ist jetzt **LiteRT-LM** ueber den projektlokalen Ordner `LIT/`. `llama.cpp` bleibt als alternativer Fallback erhalten.

## Warum dieses Projekt?

Viele Schulumgebungen brauchen:

- lokale Ausfuehrung ohne dauerhafte Cloud-Abhaengigkeit
- nachvollziehbare Rollen- und Rechtevergabe
- isolierte Codeausfuehrung
- unterrichtstaugliche KI-Unterstuetzung
- einen Server, der sowohl im Labor als auch auf einem Lehrer-Notebook lauffaehig ist

Genau dafuer ist der Nova School Server gebaut.

## Kernfunktionen

- Projektverwaltung fuer Einzel- und Gruppenarbeit
- Browserbasierter Editor mit Datei- und Live-Ausfuehrung
- Isolierte Codeausfuehrung fuer `Python`, `JavaScript`, `Node.js`, `C++`, `Java`, `Rust` und `HTML`
- Material-Studio fuer mehrstufige Erstellung von Unterrichtsmaterial
- Lokale KI-Codehilfe ueber `LiteRT-LM`
- `llama.cpp` als alternativer lokaler KI-Pfad fuer `.gguf`
- Sokratischer Mentor fuer Lernbegleitung
- Peer Review mit Snapshot-basierten Einreichungen
- Freigaben und Exporte von Projekten
- Curriculum- und Modulverwaltung
- Distributed Playground mit optionalem Worker-Dispatch
- Auditierbare Verwaltungsaktionen

## Architektur auf einen Blick

| Baustein | Rolle |
|---|---|
| `server.py` | HTTP-Server, API-Router und Session-Handling |
| `auth.py` | Login, Passwortpruefung, Session-Kontext |
| `database.py` | SQLite-Repository mit WAL-Modus |
| `code_runner.py` | Isolierte Codeausfuehrung, Container-Haertung, Scheduler |
| `ai_service.py` | Lokale KI-Provider fuer LiteRT-LM und llama.cpp |
| `material_studio.py` | Mehrstufiger Agenten-Workflow fuer Unterrichtsmaterial |
| `distributed.py` / `worker_dispatch.py` | Lokaler oder entfernter Playground-Betrieb |
| `LIT/` | Primaerer Runtime-Ordner fuer `lit` und `.litertlm`-Modelle |
| `static/` | Browser-Frontend |

## Betriebsmodell

Der Server selbst ist eine lokale Python-Anwendung. Die eigentliche Codeausfuehrung erfolgt vorzugsweise:

- in Containern
- mit schreibgeschuetztem Root-Dateisystem
- mit limitierter CPU-, RAM-, PID- und Dateigroesse
- mit deaktiviertem oder kontrolliertem Webzugriff

Die lokale KI laeuft standardmaessig:

- ueber `LiteRT-LM` mit `.litertlm`-Modellen im Ordner `LIT/`

Optional bleibt moeglich:

- `llama.cpp` mit `.gguf`-Modellen

## Schnellstart

### 1. Voraussetzungen

- Python `3.12`
- Docker oder Podman fuer isolierte Runner
- `LiteRT-LM` im Ordner `LIT/`
- keine externe `Nova-shell`-Installation fuer den Standardbetrieb

### 2. Empfohlene Projektstruktur auf Windows

```text
C:\
  nova_school_server\
    LIT\
      lit.windows_x86_64.exe
      gemma-3n-E4B-it-int4.litertlm
```

### 3. Server starten

Wenn das Repo unter `C:\nova_school_server` liegt:

```powershell
Set-Location C:\
python -m nova_school_server
```

Danach im Browser:

```text
http://127.0.0.1:8877
```

### 4. Seed-Logins

| Benutzer | Passwort | Rolle |
|---|---|---|
| `admin` | `NovaSchool!admin` | Administration |
| `teacher` | `NovaSchool!teacher` | Lehrkraft |
| `student` | `NovaSchool!student` | Demo-Schueler |

Wichtig:

- Diese Konten sind nur fuer den Erststart gedacht.
- In jeder echten Schulumgebung muessen die Kennwoerter sofort geaendert werden.

## KI-Backends

## LiteRT-LM

Der primaere KI-Pfad fuer dieses Projekt.

Empfohlene Ablage:

- `C:\nova_school_server\LIT\lit.windows_x86_64.exe`
- `C:\nova_school_server\LIT\gemma-3n-E4B-it-int4.litertlm`

Externer Downloadpfad:

- Hugging Face: `https://huggingface.co/google/gemma-3n-E4B-it-litert-lm/tree/main`
- bevorzugte Serverdatei: `gemma-3n-E4B-it-int4.litertlm`

Wichtig:

- das Modell-Repository ist gated
- vor dem Download muessen die Hugging-Face-Anmeldung und die Gemma-Lizenzfreigabe erfolgt sein

Automatisch erkannte Orte:

- `LIT/` im Projektordner
- `LIT/` neben dem Paketordner
- explizit gesetzte Servereinstellungen
- danach erst aeltere Fallbacks wie `D:\LIT`

## llama.cpp

Unterstuetzter Fallback fuer Umgebungen mit `.gguf`-Modellen. Dieser Pfad bleibt erhalten, ist aber nicht mehr der vorrangig dokumentierte Standard.

## Runner-Backends

## Empfohlen: Container

Der Standardbetrieb verwendet:

- `docker` oder `podman`
- read-only Root-FS
- `tmpfs` fuer temporaere Pfade
- `cap-drop ALL`
- `no-new-privileges`
- PID- und Datei-Limits
- seccomp, soweit auf der jeweiligen Runtime verfuegbar

## Nur als Fallback: Host-Prozess

Der Host-Prozess-Runner ist bewusst als unsicherer Ausnahmebetrieb markiert:

- standardmaessig deaktiviert
- nur fuer Lehrkraefte oder Administration freigebbar
- nicht fuer produktive Hochsicherheitsumgebungen empfohlen

## Release-Strategie

Die GitHub-Releases enthalten:

- Windows-, Linux- und generische Serverpakete
- Checksummen
- bei Verfuegbarkeit die Windows-`lit`-Binary als separates Asset

Die Server-ZIPs enthalten absichtlich **keine** grossen Modellartefakte. Der Ordner `LIT/` wird in den Paketen scaffolded, damit Modelle und native Runtimes lokal nachgelegt werden koennen.

## Installation und Betrieb

Fuer die vollstaendige Einrichtung siehe:

- [Installation.md](Installation.md)
- [Service.md](Service.md)
- [Secure.md](Secure.md)

## Sicherheitsprofil

Sicherheitsrelevante Kernpunkte:

- Passwort-Hashing mit `PBKDF2-HMAC-SHA256`
- Rollen- und Rechtevergabe pro Nutzer und Gruppe
- Session-Cookie mit `HttpOnly` und `SameSite=Lax`
- Audit-Logs fuer Verwaltungs- und Moderationsaktionen
- symlink-/junction-sichere Workspace-Kopien fuer Runner
- Netzwerkkontrolle pro Sitzung ueber `web.access`
- lokale KI statt externer Cloud als Standardpfad

Wichtig:

- Der integrierte Server bringt kein natives TLS mit.
- Fuer strenge Schul- und Traegeranforderungen ist ein Reverse Proxy mit TLS Pflicht.
- Oeffentliche Shares und Downloads sind absichtlich URL-basiert. Wenn das institutionell unzulaessig ist, muss `deploy.use` entzogen oder organisatorisch gesperrt werden.

Alle Details stehen in [Secure.md](Secure.md).
