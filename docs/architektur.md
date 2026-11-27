# Architektur

Stand: 27.11.2026 (Pipeline v0.1.0)

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

## Ablage im Bucket

```
index.json                                  Übersicht (max-age 30 s)
radar/20261127T0955Z.png                    Radar, Zeit = Ende des 5-min-Intervalls (UTC)
model/20261127T0600Z/20261127T1200Z.png     ICON-Lauf 06 UTC, Stunde 11–12 UTC (Zeit = Ende)
```

PNG: Palettenbild 1486 × 1260 px, Web Mercator, Pixel 720 m (≈ 500 m am Boden), Index 0 transparent,
1–9 = Farbstufen MeteoSchweiz. Dateinamen enthalten die Zeit → `immutable`, werden nie überschrieben.

## index.json

```json
{
  "version": 1,
  "generator": "regenradar 0.1.0",
  "generated": "2026-11-27T10:09:04Z",
  "source": "Source: MeteoSwiss",
  "disclaimer": "Kein offizielles Flugwetterprodukt – nur für Versuchszwecke.",
  "crs": "EPSG:3857",
  "bounds": [[43.697316, 2.79412], [49.300004, 12.405375]],
  "size": [1486, 1260],
  "unit": "mm/h",
  "legend": [{"from": 0.2, "to": 1.0, "color": "#9B7D96"}, "…", {"from": 60.0, "to": null, "color": "#AF00DC"}],
  "radar": {"latest": "2026-11-27T10:05:00Z", "interval_min": 5, "note": "Momentane Regenrate …"},
  "model": {"name": "ICON-CH1-EPS (Kontrolllauf)", "run": "2026-11-27T06:00:00Z", "interval_min": 60, "note": "Stundenmittel …"},
  "frames": [
    {"time": "2026-11-27T07:10:00Z", "from": "2026-11-27T07:05:00Z", "kind": "radar", "url": "radar/20261127T0710Z.png"},
    {"time": "2026-11-27T11:00:00Z", "from": "2026-11-27T10:00:00Z", "kind": "model", "url": "model/20261127T0600Z/20261127T1100Z.png"}
  ]
}
```

- `bounds` = Leaflet-Grenzen `[[Süd, West], [Nord, Ost]]` für `L.imageOverlay` (Bild ist bereits Web Mercator).
- `url` ist relativ zu `index.json`.
- `time` = Ende des Intervalls, `from` = Beginn. `kind` = `radar` | `model` (später `extrapolation`, ADR 0002).
- Alter der Daten für die Warnung in meteocam (R6): `radar.latest` und `model.run` gegenüber der Uhrzeit des Geräts.

## Ablauf eines Laufs (`regenradar run`)

1. Radar: Tages-Item(s) per STAC lesen, alle `rzc`-Dateien der letzten 3 h, die noch fehlen, holen und rendern.
2. Modell: neuesten ICON-CH1-Lauf wählen, der alle Stunden von jetzt bis +6 h hat (sonst den vorherigen);
   fehlende Stunden rendern. Bei Fehler bleibt der zuletzt gespeicherte Lauf in Gebrauch.
3. `index.json` schreiben.
4. Aufräumen: Radar älter als 3 h 15 min, Modellbilder anderer Läufe.

Cache (`--cache`, Standard `~/.cache/regenradar`): Umrechnungs-Indizes und ICON-Koordinaten (einmal 37 MB).
Erster Lauf ca. 30 s, danach wenige Sekunden.

**Übergang:** Solange die eigene Hochrechnung (ADR 0002) fehlt, zeigt das Modell die Stunden ab **jetzt**
(`Settings.model_start = 0`). Mit der Hochrechnung wird das auf +2 h gesetzt.

## Abgrenzung zu meteocam

- Getrennte Repos, keine gemeinsamen Secrets.
- meteocam liest nur öffentliche URLs (Bilder + `index.json`).
- Der private Kamerabild-Bucket von meteocam wird von diesem Repo nie berührt.
