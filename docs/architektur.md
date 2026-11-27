# Architektur

Stand: 27.11.2026 (Entwurf, Details folgen nach der Datenanalyse in Schritt 2)

## Überblick

```
MeteoSchweiz STAC-API                 GitHub Actions (Cron, alle 5–10 min)
data.geo.admin.ch/api/stac/v1   ──►   pipeline/ (Python)
  · Radar PRECIP (5 min)                · neueste Dateien holen
  · Nowcast RR-INCA (10 min)            · in mm/h umrechnen
                                        · nach EPSG:3857 umprojizieren
                                        · PNG mit Farbskala MeteoSchweiz
                                        · index.json schreiben, alte Bilder löschen
                                                │
                                                ▼
                                      Cloudflare R2 (eigener Bucket, öffentlich lesbar)
                                        radar/<zeit>.png, index.json
                                                │
                                                ▼
                                      meteocam (Leaflet-Karte)
                                        Ebene «Regen»: Zeitschieber, Legende, Quelle
```

## Bausteine

| Baustein | Ort | Aufgabe |
|---|---|---|
| Pipeline | dieses Repo, `pipeline/` | Daten holen und in Bilder umwandeln |
| Ausführung | GitHub Actions Cron | Pipeline alle 5–10 min starten |
| Speicher | Cloudflare R2, eigener Bucket | PNG-Bilder und `index.json` öffentlich bereitstellen |
| Anzeige | Repo meteocam | Ebene «Regen» auf der bestehenden Karte |

## index.json (Entwurf)

```json
{
  "generated": "2026-11-27T10:00:00Z",
  "source": "Source: MeteoSwiss",
  "bounds": [[45.6, 5.6], [48.1, 10.9]],
  "now": "2026-11-27T09:55:00Z",
  "frames": [
    { "time": "2026-11-27T06:55:00Z", "kind": "radar",    "url": "radar/20261127T0655Z.png" },
    { "time": "2026-11-27T10:05:00Z", "kind": "nowcast",  "url": "nowcast/20261127T1005Z.png" }
  ],
  "legend": [ { "mm_h": 0.1, "color": "#…" } ]
}
```

Bounds, Dateinamen und Legende werden nach der Datenanalyse festgelegt.

## Abgrenzung zu meteocam

- Getrennte Repos, keine gemeinsamen Secrets.
- meteocam liest nur öffentliche URLs (Bilder + `index.json`).
- Der private Kamerabild-Bucket von meteocam wird von diesem Repo nie berührt.
