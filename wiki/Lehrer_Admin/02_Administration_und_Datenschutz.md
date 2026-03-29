# Administration und Datenschutz

## Datenschutzrechte

- Admins koennen strukturierte JSON-Exporte fuer Nutzer ausloesen.
- Hard-Delete und Retention sind nur fuer administrative Rollen vorgesehen.
- Chat-, KI- und Audit-Daten muessen nach dem Schulkonzept behandelt werden.

## Betrieb

| Bereich | Mindestmassnahme |
| --- | --- |
| **TLS** | Reverse Proxy mit HTTPS |
| **Runner** | Isolierte Container-Laeufe |
| **KI** | Lokale Modelle, keine Cloud-Prompts |
| **Backups** | Regelmaessige Sicherung von `data/` und Konfiguration |

## Sicherheit

- Produktiv nur mit HTTPS und gesicherter Netzumgebung betreiben.
- Rechte moeglichst rollenbasiert und sparsam vergeben.
- Aendere Demo-Zugangsdaten vor produktivem Einsatz.
