# regenradar

Schweizweiter Niederschlag auf Basis von MeteoSchweiz Open Data – als Bildebene für die Karte von
[meteocam](https://github.com/maleanso/meteocam).

- **Messung:** Radar PRECIP, alle 5 min, die letzten 3 Stunden
- **Prognose:** Nowcast RR-INCA, 10-min-Schritte, bis +6 Stunden

Dieses Repo enthält nur die **Datenaufbereitung** (Python). Sie erzeugt transparente PNG-Bilder
(Web Mercator) und ein `index.json` mit den Zeitstempeln. Angezeigt wird das Ganze in meteocam
als Ebene «Regen».

> Source: MeteoSwiss (Open Data, CC BY).
> Kein offizielles Flugwetterprodukt.

## Stand

Proof of Concept, Phase 1 – siehe [ROADMAP.md](ROADMAP.md).

## Aufbau

| Ordner | Inhalt |
|---|---|
| `pipeline/` | Python-Job: Daten holen, umrechnen, umprojizieren, PNG + `index.json` |
| `docs/` | Architektur, Datenbeschreibung, Entscheide (ADR) |

## Schnellstart

Folgt mit Schritt 3 (Pipeline). Vorgesehen:

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env   # R2-Zugang eintragen (nur für Upload nötig)
pytest
```

## Dokumentation

- [docs/architektur.md](docs/architektur.md) – Aufbau und Datenfluss
- [docs/daten.md](docs/daten.md) – Datenquellen, Formate, Gitter, Einheiten, Farbskala
- [docs/entscheide/](docs/entscheide/) – Architekturentscheide

## Lizenz

Keine Lizenz – alle Rechte vorbehalten. Die Daten stammen von MeteoSchweiz (CC BY).
