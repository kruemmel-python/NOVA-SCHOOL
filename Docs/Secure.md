# Nova School Server Security

## Zweck dieses Dokuments

Dieses Dokument beschreibt die sicherheitsrelevanten Mechanismen des Nova School Server in der aktuell implementierten Codebasis. Es richtet sich an Schultraeger, Admin-Teams, IT-Beauftragte, Datenschutzverantwortliche und Lehranstalten mit hohen Anforderungen an Isolation, Nachvollziehbarkeit und lokale Datenkontrolle.

Wichtig:

- Dieses Dokument beschreibt sowohl **vorhandene Schutzmassnahmen** als auch **sicherheitsrelevante Grenzen**.
- Fuer strenge Institutionen sind die Grenzen genauso wichtig wie die Controls selbst.

## 1. Sicherheitszielbild

Der Nova School Server verfolgt folgende Sicherheitsziele:

1. Lokale Daten- und Modellausfuehrung ohne erzwungene Cloud-Abhaengigkeit.
2. Rollenbasierter Zugriff fuer Schueler, Lehrkraefte und Administration.
3. Isolierte Codeausfuehrung fuer Schuelerprojekte.
4. Begrenzung von Netzwerkzugriffen waehrend Projektlaeufen.
5. Nachvollziehbarkeit administrativer Eingriffe.
6. Minimierung von Host-Risiken durch Containerisierung und Dateisystemkopien.

## 2. Sicherheitsarchitektur im Ueberblick

| Schicht | Zweck |
|---|---|
| Eingebaute `SecurityPlane`-kompatible Schicht | Token-Ausgabe, Tenant- und Worker-Sicherheitskontext |
| `AuthService` | Login, Session-Aufbau, Passwortpruefung |
| Rollen-/Rechtesystem | Zugriff auf API, Runner, KI, Moderation, Deployments |
| `CodeRunner` | isolierte Codeausfuehrung mit Container-Haertung |
| `SchoolRepository` | SQLite mit Audit- und Konfigurationspersistenz |
| Lokale KI | Primaer LiteRT-LM aus `LIT/`, alternativ llama.cpp ohne zwingende Cloud-Nutzung |
| Worker-Dispatch | signierte und nonce-geschuetzte Worker-Requests |

## 3. Identitaet, Authentisierung und Sessions

## 3.1 Passwortspeicherung

Passwoerter werden nicht im Klartext gespeichert.

Implementiert in `auth.py`:

- `PBKDF2-HMAC-SHA256`
- `200000` Iterationen
- individueller `16`-Byte-Salt pro Benutzer
- Vergleich per `hmac.compare_digest`

Das ist fuer schulische Standardanwendungen ein solider lokaler Basisschutz.

## 3.2 Session-Erzeugung

Nach erfolgreichem Login wird ueber die eingebaute `SecurityPlane`-kompatible Schicht ein Token ausgestellt.

Dieses Token wird serverseitig fuer den Session-Kontext genutzt:

- Nutzerkennung
- Rollen
- Gruppen
- effektive Berechtigungen

## 3.3 Session-Cookie

Der Server setzt ein Cookie:

- Name: `nova_school_token`
- `HttpOnly`
- `SameSite=Lax`
- `Path=/`

Positiv:

- `HttpOnly` reduziert direkten Zugriff ueber Client-Skripte.
- `SameSite=Lax` reduziert bestimmte Cross-Site-Angriffe.

Wichtige Grenze:

- Der eingebaute Server spricht weiterhin **HTTP**, nicht HTTPS.
- `Secure` am Cookie wird gesetzt, wenn der Server einen HTTPS-Betrieb ueber `server_public_host = https://...` oder ueber Proxy-Header wie `X-Forwarded-Proto: https` erkennt.

Konsequenz fuer Lehranstalten:

- Der Nova School Server darf produktiv nur hinter einem TLS-terminierenden Reverse Proxy betrieben werden.
- Die direkte HTTP-Freigabe des Python-Servers ins Schulnetz bleibt nicht empfohlen.

## 3.4 Reverse-Proxy-Betrieb

Das Repository enthaelt produktionsnahe Vorlagen fuer:

- `deploy/reverse-proxy/Caddyfile`
- `deploy/reverse-proxy/nginx.conf`

Erwarteter Betrieb:

- NOVA SCHOOL intern auf `127.0.0.1:8877`
- TLS-Terminierung auf dem Reverse Proxy
- Weitergabe von `Host`, `X-Forwarded-Host` und `X-Forwarded-Proto`
- `server_public_host` auf die externe HTTPS-URL setzen

Damit werden:

- oeffentliche Verifikationslinks mit `https://` erzeugt
- Session-Cookies mit `Secure` ausgegeben

## 4. Autorisierung und Rollenmodell

## 4.1 Rollen

Die Codebasis kennt drei Hauptrollen:

- `student`
- `teacher`
- `admin`

## 4.2 Berechtigungsmodell

Zugriffe werden nicht nur ueber Rollen, sondern ueber explizite Permissions aufgeloest.

Beispiele:

- `files.write`
- `web.access`
- `ai.use`
- `teacher.materials.use`
- `run.python`
- `run.cpp`
- `deploy.use`
- `admin.manage`

Permissions werden kombiniert aus:

- Rollenstandard
- Gruppen-Overrides
- Nutzer-Overrides

## 4.3 Wichtige Governance-Information

In der aktuellen Implementierung gelten Lehrkraefte als privilegierte Konten:

- `teacher` darf serverseitige Einstellungen oeffnen und veraendern
- genauer: Zugriff auf `/api/server/settings` ist fuer `session.is_teacher` erlaubt

Das ist fuer kleine Schuldeployments pragmatisch, aber fuer streng getrennte Admin-Modelle relevant.

Empfehlung fuer strenge Lehranstalten:

- Lehrer-Konten als privilegierte Betriebsrolle behandeln
- nur vertrauten Accounts geben
- zusaetzlich organisatorisch absichern
- falls gewuenscht, die Berechtigung im Code oder durch vorgelagerte Governance einschranken

## 5. Codeausfuehrung und Isolation

## 5.1 Standard: Container-Backend

Der Server ist standardmaessig auf `container` gestellt. Das ist die empfohlene und sicherere Betriebsart.

Unterstuetzte Container-Runtimes:

- Docker
- Podman

## 5.2 Container-Haertungsmassnahmen

Im Containerbetrieb setzt der Runner unter anderem:

- `--read-only`
- `--cap-drop ALL`
- `--security-opt no-new-privileges`
- `--pids-limit`
- `--ulimit fsize=...`
- `--ulimit nofile=...`
- `--tmpfs /tmp:rw,noexec,nosuid,nodev,size=...`
- `--tmpfs /var/tmp:rw,noexec,nosuid,nodev,size=...`

Zusatznutzen:

- kein Live-Mount des Original-Workspaces
- jeder Lauf arbeitet mit einer materialisierten Kopie
- Root-Dateisystem des Containers bleibt schreibgeschuetzt

## 5.3 Seccomp

Der Runner unterstuetzt seccomp:

- Standardprofil: `seccomp_profiles/container-denylist.json`
- optional benutzerdefinierter Profilpfad

Wichtige Implementierungsgrenze:

- Unter Windows mit Docker wird kein zusaetzliches lokales seccomp-Profil an den Docker-Aufruf gehaengt.
- In diesem Fall verlaesst sich der Server auf die Docker-Builtin-Absicherung der Runtime.

Fuer Linux-Server oder Podman-Deployments ist das eigene seccomp-Profil wirksamer nutzbar.

## 5.4 Unsicherer Host-Prozess-Runner

Der Host-Prozess-Runner ist explizit als unsicherer Fallback markiert:

- standardmaessig deaktiviert
- nur bei gesetztem `unsafe_process_backend_enabled = true`
- nur fuer Lehrkraefte oder Administration zulaessig

Fuer Lehranstalten gilt:

- Dieser Modus sollte in produktiven Umgebungen deaktiviert bleiben.

## 6. Dateisystemschutz

## 6.1 Sichere Workspace-Kopien

Vor isolierten Laeufen kopiert der Server Projektdateien in einen Lauf-Workspace.

Dabei werden blockiert:

- symbolische Links
- Junctions
- ungueltige relative Pfade mit `..`

Das reduziert Angriffe ueber Pfadmanipulation und Host-Dateizugriffe.

## 6.2 Path-Sanitizing

Relevante Schutzmechanismen:

- nur relative Projektpfade
- keine absoluten Pfade fuer Runner-Dateien
- keine Traversal-Pfade
- Preview- und Download-Pfade werden gegen Basisverzeichnisse validiert

## 6.3 Artefakt-Snapshots

Shares, Exporte und Review-Snapshots werden aus einer kopierten Projektansicht erzeugt. Ignoriert werden unter anderem:

- `.git`
- `.venv`
- `venv`
- `node_modules`
- `dist`
- `build`
- `target`
- `.nova-school`

Das reduziert die unbeabsichtigte Verteilung interner Lauf- oder Build-Artefakte.

## 7. Netzwerk- und Internetkontrolle

## 7.1 Permission-basierter Webzugriff

Der zentrale Schalter fuer Projektnetzwerkzugriff ist:

- `web.access`

Wenn `web.access` **nicht** gesetzt ist:

- Container laufen mit `--network none`
- Proxy-Variablen werden geleert
- `NO_PROXY` wird auf `*` gesetzt
- der Lauf wird intern als `NOVA_SCHOOL_WEB_POLICY=off` markiert

Wenn `web.access` gesetzt ist:

- Container nutzen `bridge`
- optional kann ein Proxy vorgegeben oder erzwungen werden

## 7.2 Proxy-Unterstuetzung

Der Server kann Webzugriff ueber einen definierten Proxy erzwingen:

- `web_proxy_url`
- `web_proxy_no_proxy`
- `web_proxy_required`

Wenn `web_proxy_required = true` und kein Proxy gesetzt ist:

- der Lauf wird abgelehnt

Das ist fuer Schulnetze mit zentraler Filterung ein wichtiger Kontrollpunkt.

## 7.3 Python- und npm-Abhaengigkeiten

Projektabhaengigkeiten werden nur geladen, wenn:

- Webzugriff erlaubt ist
- oder bereits ein lokaler Cache fuer die Abhaengigkeiten vorliegt

Das gilt unter anderem fuer:

- `requirements.txt`
- `npm install`
- `npm ci`

## 8. Lokale KI und Datenschutz

## 8.1 Lokale KI-Pfade

Die Anwendung unterstuetzt lokale KI lokal auf dem Server. Der primaere Pfad ist:

- `LiteRT-LM` ueber den projektlokalen Ordner `LIT/`

Optional bleibt moeglich:

- `llama.cpp`

Das reduziert Datenschutzrisiken gegenueber externen Cloud-Diensten deutlich.

## 8.2 Modell- und Prompt-Verarbeitung

Die KI-Anfragen werden lokal verarbeitet.

Fuer LiteRT-LM gilt in der aktuellen Implementierung:

- der Server nutzt die `lit`-CLI lokal pro Anfrage
- der Server bevorzugt automatisch `LIT/` im Projektordner fuer Binary, Modell und Cache-Herkunft
- Promptdateien werden temporaer im lokalen Cachebereich abgelegt
- nach dem Lauf werden diese Promptdateien wieder geloescht

## 8.2a Browser-Assets und CDNs

Die produktive Hauptoberflaeche laedt keine externen JavaScript-CDNs.

Aktueller Zustand:

- produktive Browser-Assets kommen aus dem lokalen Ordner `static/`
- der fruehere Browser-WebGPU-Pfad ist nur noch als lokaler Kompatibilitaets-Stub vorhanden
- fuer den Standardbetrieb mit LiteRT-LM oder llama.cpp ist kein externer Browser-Download noetig

## 8.3 Wichtige Grenze

Wenn `llama.cpp` genutzt wird und noch keine Binary vorhanden ist, kann die Runtime-Binary aus GitHub nachgeladen werden.

Fuer strikt abgeschottete Umgebungen bedeutet das:

- alle benoetigten Binaries und Modelle vorab lokal bereitstellen
- fuer den Standardbetrieb `LIT/` bereits vor dem Unterricht mit Binary und Modell befuellen
- keine Auto-Downloads im Produktivnetz zulassen

## 9. Auditierung und Nachvollziehbarkeit

Die Datenbank fuehrt Audit-Logs fuer sicherheitsrelevante und administrative Aktionen.

Beispiele:

- Benutzeranlage
- Gruppenanlage
- Membership-Aenderungen
- Permission-Aenderungen
- Settings-Aenderungen
- Chat-Moderation
- Playground-Start und -Stop

Das ist fuer Schulbetrieb und spaetere Nachvollziehbarkeit ein wichtiger Bestandteil.

## 10. Scheduler und Fairnesskontrollen

Die Codeausfuehrung nutzt einen serverseitigen Scheduler mit:

- globalen Gleichzeitigkeit-Limits
- rollenabhaengigen Owner-Limits
- Priorisierung fuer `admin`, `teacher`, `student`

Standardwerte:

- global: `4`
- student: `1`
- teacher: `2`
- admin: `3`

Das ist kein direkter Security-Blocker, aber ein wichtiger Schutz gegen Ressourcenverdrangung.

## 11. Peer Review und verteilte Worker

## 11.1 Peer Review

Peer Review arbeitet snapshot-basiert:

- Projekte werden als Snapshot kopiert
- Reviewer sehen Aliase statt ungefilterter direkter Review-Kettenamen

## 11.2 Remote Worker Dispatch

Der Worker-Dispatch verfuegt ueber mehrere Schutzmechanismen:

- pro Worker ein eigenes Secret
- HMAC-Signaturen fuer Requests
- Zeitstempelpruefung mit Replay-Fenster
- Nonce-Registrierung gegen Wiederverwendung
- Online-/Heartbeat-Validierung

Das ist fuer verteilte Unterrichtsszenarien relevant, wenn externe Worker-Knoten genutzt werden.

## 12. Sicherheitsrelevante Grenzen der aktuellen Implementierung

Die folgenden Punkte muessen fuer eine ehrliche Sicherheitsbewertung klar benannt werden.

### 12.1 Kein natives TLS im Applikationsserver

Der integrierte Server basiert auf `ThreadingHTTPServer` und spricht HTTP.

Konsequenz:

- produktiver Betrieb nur hinter Reverse Proxy mit TLS

### 12.2 Kein `Secure`-Cookie-Flag

Das Session-Cookie ist `HttpOnly` und `SameSite=Lax`, aber aktuell nicht `Secure`.

Konsequenz:

- ohne vorgeschaltetes HTTPS ist das fuer Produktivbetrieb nicht ausreichend

### 12.3 Kein explizites CSRF-Token-Modell

Die API arbeitet cookie-basiert, aber es gibt aktuell keine zusaetzliche CSRF-Token-Schicht.

Konsequenz:

- `SameSite=Lax` hilft
- fuer institutionellen Betrieb sollten TLS, Same-Origin-Proxying und ein abgesichertes Intranet-Setup verbindlich sein

### 12.4 Oeffentliche Shares und Downloads sind URL-basiert

`/share/<id>/...` und `/download/<id>` sind absichtlich artefaktbasiert erreichbar.

Konsequenz:

- wenn oeffentliche Freigaben in einer Lehranstalt nicht erlaubt sind, muss `deploy.use` deaktiviert werden

### 12.5 Seed-Benutzer mit bekannten Standardpasswoertern

Beim Bootstrap werden Demo-Konten angelegt.

Konsequenz:

- vor Produktivbetrieb sofort aendern oder entfernen

### 12.6 Lehrkraefte koennen Servereinstellungen verwalten

Lehrkraefte sind in der aktuellen Implementierung privilegiert genug, um Servereinstellungen zu veraendern.

Konsequenz:

- Lehrer-Konten sind sicherheitsrelevant
- nicht als unkritische Endnutzerkonten behandeln

## 13. Empfohlene Baseline fuer strenge Lehranstalten

Die folgende Baseline ist fuer einen ernsthaften institutionellen Betrieb empfohlen.

1. Reverse Proxy mit TLS `1.2+` oder `1.3` vor den Server setzen.
2. Server intern nur im Verwaltungs- oder Unterrichtsnetz exponieren.
3. `unsafe_process_backend_enabled = false` lassen.
4. Container-Runner erzwingen.
5. Webzugriff standardmaessig deaktivieren.
6. Proxy-Pflicht fuer erlaubte Webzugriffe aktivieren.
7. `deploy.use` entziehen, wenn keine oeffentlichen Shares zulaessig sind.
8. Standardpasswoerter sofort aendern.
9. Lehrer-Konten als privilegierte Konten behandeln.
10. Modelle, Container-Images und Build-Abhaengigkeiten vorab lokal bereitstellen.
11. Backup von `school.db`, `workspaces` und Artefaktordnern etablieren.
12. Betrieb und Audit-Logs regelmaessig pruefen.

## 14. Datenschutz- und Compliance-Hinweise

Fuer Bildungseinrichtungen sind folgende Punkte besonders relevant:

- lokale KI reduziert Datenabflussrisiken
- Runner-Isolation reduziert Host-Risiken
- Audit-Logs verbessern Nachvollziehbarkeit
- Proxy-Steuerung unterstuetzt schulische Netzrichtlinien

Vor produktivem Einsatz sollten dennoch institutionell geprueft werden:

- Rollen- und Berechtigungskonzept
- Umgang mit oeffentlichen Shares
- Passwort- und Benutzerverwaltung
- Aufbewahrung von Review-Snapshots, Exporten und Laufartefakten
- Netzsegmentierung und Logging

## 15. Zusammenfassung

Der Nova School Server bringt bereits wichtige Schutzmechanismen fuer den schulischen Einsatz mit:

- lokale Authentisierung
- lokale KI
- Rechte- und Rollensystem
- Audit-Logs
- harte Container-Isolation
- Webzugriffskontrolle
- sichere Workspace-Kopien
- signierten Worker-Dispatch

Fuer wirklich strenge Lehranstalten ist jedoch entscheidend:

- HTTPS/TLS muss extern erzwungen werden
- privilegierte Rollen muessen organisatorisch kontrolliert werden
- oeffentliche Freigaben muessen bewusst erlaubt oder deaktiviert werden
- der Host-Prozess-Runner darf nicht als Normalbetrieb verwendet werden

Damit ist der Nova School Server gut fuer kontrollierte, lokale und nachvollziehbare Schulumgebungen geeignet, wenn die genannten Betriebsgrenzen professionell eingehalten werden.
