# Reverse Proxy und TLS

Dieser Ordner enthaelt produktionsnahe Reverse-Proxy-Vorlagen fuer einen TLS-gesicherten Betrieb des Nova School Server.

Zielbild:

- NOVA SCHOOL lauscht intern auf `127.0.0.1:8877`
- der Reverse Proxy terminiert TLS auf `443`
- die Anwendung bleibt intern lokal und unverschluesselt
- externe Clients sprechen ausschliesslich `https://`

Enthalten:

- `Caddyfile`
- `nginx.conf`

Wichtige Hinweise:

- setze in den Servereinstellungen `server_public_host` auf die externe HTTPS-URL, z. B. `https://nova.schule.local`
- die Proxy-Konfigurationen setzen `X-Forwarded-Proto` und `X-Forwarded-Host`
- dadurch setzt NOVA SCHOOL bei HTTPS-Betrieb automatisch `Secure` am Session-Cookie

Empfehlung fuer Lehranstalten:

- den eingebauten Python-HTTP-Server nicht direkt ins Schulnetz exponieren
- nur den Reverse Proxy auf `443` freigeben
- internen Server auf `127.0.0.1` binden
