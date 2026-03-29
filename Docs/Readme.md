# Nova School Server

Ein lokaler Schulserver fuer Programmierunterricht, Projektarbeit und KI-gestuetzte Unterrichtsvorbereitung.

Der **Nova School Server** verbindet einen browserbasierten Arbeitsbereich mit lokalen Runnern, rollenbasierter Rechtevergabe, Peer Review, Offline-Dokumentation, verteilten Playground-Szenarien und lokalem KI-Support ueber **LiteRT-LM** oder **llama.cpp**.

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
- Lokale KI-Codehilfe ueber `LiteRT-LM` oder `llama.cpp`
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
| `static/` | Browser-Frontend |

## Betriebsmodell

Der Server selbst ist eine lokale Python-Anwendung. Die eigentliche Codeausfuehrung erfolgt vorzugsweise:

- in Containern
- mit schreibgeschuetztem Root-Dateisystem
- mit limitierter CPU-, RAM-, PID- und Dateigroesse
- mit deaktiviertem oder kontrolliertem Webzugriff

Die lokale KI laeuft wahlweise:

- ueber `LiteRT-LM` mit `.litertlm`-Modellen
- oder ueber `llama.cpp` mit `.gguf`-Modellen

## Schnellstart

### 1. Voraussetzungen

- Python `3.12`
- Nova-shell-Laufzeit erreichbar
- optional Docker oder Podman
- optional lokales KI-Modell

### 2. Server starten

Wenn das Repo unter `H:\nova_school_server` liegt:

```powershell
Set-Location H:\
python -m nova_school_server
```

Danach im Browser:

```text
http://127.0.0.1:8877
```

### 3. Seed-Logins

| Benutzer | Passwort | Rolle |
|---|---|---|
| `admin` | `NovaSchool!admin` | Administration |
| `teacher` | `NovaSchool!teacher` | Lehrkraft |
| `student` | `NovaSchool!student` | Demo-Schueler |

Wichtig:

- Diese Konten sind fuer den Erststart gedacht.
- In jeder echten Schulumgebung muessen die Kennwoerter sofort geaendert werden.

## Installation und Betrieb

Fuer die vollstaendige Einrichtung siehe:

- [Installation.md](Installation.md)
- [Secure.md](Secure.md)

## KI-Backends

## LiteRT-LM

Geeignet fuer:

- schnelle lokale Inferenz mit `.litertlm`
- kompakte lokale Modelle
- Material-Studio und direkte Hilfe ohne Cloud-Pfad

Typischer Setup:

- Binary in `D:\LIT\lit.windows_x86_64.exe`
- Modell in `D:\LIT` oder `Model`

## llama.cpp

Geeignet fuer:

- `.gguf`-Modelle
- alternative lokale Modellpfade
- automatische Runtime-Binary-Bereitstellung, falls noch keine lokale `llama-server`-Binary vorhanden ist

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

## Projektstruktur

Typische Struktur:

```text
H:\
  nova_school_server\
    Docs\
    Model\
    static\
    tests\
    server.py
    code_runner.py
    ai_service.py
    material_studio.py
  data\
    school.db
    workspaces\
    docs\
```

Wichtig:

- Das Repo `Docs/` enthaelt Entwickler- und Betriebsdokumentation.
- `data/docs` ist die zur Laufzeit verwendete interne Dokumentationsbibliothek.

## Einsatzszenarien

Der Nova School Server eignet sich fuer:

- Informatik-Unterricht in Schulnetzen
- Lehrergeraete zur Vorbereitung von Materialien
- abgeschottete Lernumgebungen mit lokaler KI
- Laborraeume mit Projektarbeit
- Demonstrationen verteilter Systeme im Unterricht

## Empfohlene Produktionspraxis

1. Server hinter Reverse Proxy mit TLS betreiben.
2. Container-Runner als Standard erzwingen.
3. Webzugriff standardmaessig deaktivieren und nur gezielt freigeben.
4. Demo-Konten sofort absichern.
5. Rollen und Rechte vor Inbetriebnahme fachlich pruefen.
6. Oeffentliche Shares nur dann aktiv lassen, wenn dies organisatorisch erlaubt ist.
7. KI-Modelle und Container-Images vor dem Unterricht lokal vorwaermen.

## Entwicklungsstatus

Die Codebasis ist funktionsfaehig, aber bewusst praxisnah und direkt am Schulbetrieb orientiert. Sie ist kein generisches LMS, sondern ein lokaler Server fuer Unterrichtsprojekte, Ausfuehrung, Materialerstellung und Moderation.

Besonders stark ist das Projekt dort, wo gebraucht wird:

- lokale Kontrolle
- niedrige Cloud-Abhaengigkeit
- transparente Sicherheitsgrenzen
- hoher Unterrichtsbezug

## Weiterfuehrende Dokumente

- [Installation.md](Installation.md)
- [Secure.md](Secure.md)
