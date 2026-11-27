# Betrieb

Stand: 27.11.2026. Einrichtung erst nach «deploy» – Schritt für Schritt mit Chris.

## Übersicht

| Teil | Wo | Wert |
|---|---|---|
| Lauf | GitHub Actions, Workflow `pipeline` | alle 5 min (`*/5`), Start oft 5–15 min verspätet (ADR 0001) |
| Speicher | Cloudflare R2, Bucket `regenradar` | öffentlich lesbar über eigene Domain |
| Öffentliche Adresse | `https://radar.meteocam.ch/index.json` | von meteocam gelesen |
| Tests | GitHub Actions, Workflow `test` | bei jedem Push |

## Einrichtung (einmalig)

1. **R2-Bucket** `regenradar` anlegen (Standort Europa).
2. **Eigene Domain** im Bucket: `radar.meteocam.ch` (Zone meteocam.ch ist bereits bei Cloudflare). Kein `r2.dev`-Link.
3. **CORS-Regel** im Bucket (nötig, weil meteocam `index.json` per `fetch` liest):
   ```json
   [
     {
       "AllowedOrigins": ["https://meteocam.ch", "https://meteocam.maleanso.workers.dev", "http://localhost:8787"],
       "AllowedMethods": ["GET", "HEAD"],
       "AllowedHeaders": ["*"],
       "MaxAgeSeconds": 3600
     }
   ]
   ```
   Preview-Adressen von meteocam (`*-meteocam.maleanso.workers.dev`) bei Bedarf ergänzen.
4. **Lebenszyklus-Regel** als Sicherheitsnetz: Objekte nach 2 Tagen löschen (die Pipeline räumt selbst auf).
5. **API-Token** für R2: «Object Read & Write», nur Bucket `regenradar`. Notieren: Access Key ID, Secret Access Key, Account ID.
6. **GitHub-Secrets** im Repo (Settings → Secrets and variables → Actions):
   `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` (= `regenradar`).
7. **Standard-Branch** auf `main` stellen (Zeitpläne laufen nur auf dem Standard-Branch).
8. Workflow `pipeline` einmal von Hand starten (Actions → pipeline → Run workflow), dann
   `https://radar.meteocam.ch/index.json` im Browser prüfen.

## Kosten (Schätzung)

- GitHub Actions: öffentliches Repo → gratis. ~288 Läufe pro Tag, je ca. 1 min.
- R2: wenige MB Speicher; pro Lauf ca. 5–10 Schreib-/Listen-Operationen → ca. 50'000–90'000 pro Monat
  (Gratis: 1 Mio. Klasse A). Lesen durch meteocam-Nutzer: Klasse B, Gratis 10 Mio. pro Monat.

## Hinweise

- GitHub deaktiviert Zeitpläne in öffentlichen Repos nach **60 Tagen ohne Aktivität** im Repo → dann im Tab Actions wieder einschalten.
- Fällt der Lauf aus, zeigt meteocam das Alter der Daten (Warnung R6).
- Lokaler Test ohne R2: `regenradar run --out ./out`.
