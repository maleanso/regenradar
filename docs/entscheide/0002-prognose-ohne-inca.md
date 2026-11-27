# ADR 0002 – Prognose ohne freien INCA-Nowcast

Datum: 27.11.2026 · Status: angenommen (Chris)

## Ausgangslage

Der INCA-Nowcast (Niederschlag bis +6 h) ist laut MeteoSchweiz-Doku (E1) **nicht frei verfügbar**,
sondern nur auf Anfrage. Ausserdem: LV03 statt LV95, 5-min-Schritte, neues System 2027–2028 geplant.

## Entscheid

Die Prognose wird aus zwei frei verfügbaren Teilen zusammengesetzt, INCA wird parallel angefragt:

| Zeitraum | Quelle | Bemerkung |
|---|---|---|
| jetzt … +2 h | **eigene Hochrechnung aus dem Radar** (pysteps, Open Source, BSD-3) | Verschiebung der Regenzellen; Qualität nimmt mit der Zeit ab |
| +2 h … +6 h | **ICON-CH1-EPS `TOT_PREC`** (STAC, GRIB2) | Stundenwerte, Lauf alle 3 h, ca. 2 h Verzögerung |
| später | **INCA** (falls MeteoSchweiz zusagt) | ersetzt die eigene Hochrechnung |

## Folgen

- In meteocam müssen die drei Arten klar unterscheidbar sein: **Messung**, **Hochrechnung**, **Modell**.
- `index.json` bekommt pro Bild `kind` = `radar` | `extrapolation` | `model`.
- Grenze +2 h ist ein Startwert und wird nach ersten Vergleichen angepasst.
- Die Anfrage bei MeteoSchweiz (Kontaktformular) stellt Chris; Text kann vorbereitet werden.
