# Roadmap

Stand: 27.11.2026

## Phase 1 – Proof of Concept (−3 h bis +6 h)

- [x] 1. Repo-Struktur, CLAUDE.md, ROADMAP.md, README, CHANGELOG, ADR 0001
- [ ] 2. Je eine Radar- und eine Nowcast-Datei holen und analysieren → `docs/daten.md`
  - Format, Gitter, Projektion, Einheiten, Zeitstempel, Fehlwerte
  - Name der STAC-Collection für den Nowcast (RR-INCA) bestätigen
  - Farbskala MeteoSchweiz (Schwellenwerte, Farben) festhalten → Chris zur Freigabe zeigen
- [ ] 3. Pipeline: Dateien → PNG + `index.json` (erst nach «entwickle»)
  - Umrechnung in mm/h, Umprojektion nach EPSG:3857, transparente PNG mit Farbskala
  - `index.json` mit Zeitstempel, Art (Messung/Prognose), Ausdehnung (Bounds), Quelle
  - Alte Bilder ausserhalb −3 h löschen
  - pytest mit kleiner Beispieldatei
- [ ] 4. Integration meteocam: Ebene «Regen» (erst nach «entwickle», im Repo meteocam auf eigenem Branch)
- [ ] 5. Automatisierung (GitHub Actions Cron) und R2-Bucket (erst nach «deploy»)

**Stopp – weiter zu Phase 2 erst nach Freigabe durch Chris.**

## Integration meteocam – Wünsche von Chris (27.11.2026)

Umsetzung im Repo meteocam, erst nach «entwickle».

- [ ] R1. Eigener Icon-Knopf «Regen» auf der **linken** Kartenseite
- [ ] R2. Prüfen: METAR-Knopf ebenfalls auf die linke Seite verschieben (zusammen mit «Regen»)
- [ ] R3. Beim Einschalten erscheint der Zeitschieber **ganz unten, fixiert** (−3 h … +6 h, Play/Pause, Markierung «jetzt», Messung/Prognose klar unterscheidbar)
- [ ] R4. Legende in mm/h (Farbskala MeteoSchweiz), «Source: MeteoSwiss», Hinweis «kein offizielles Flugwetterprodukt»
- [ ] R5. Mobil gut bedienbar (iPhone, iPad, EFB)

## Phase 2 – Ideen (noch nicht freigegeben)

- Längere Vorausschau mit ICON-Modellniederschlag (ICON-CH1/CH2)
- Alternative Ausführung statt GitHub Actions: Cloudflare Container oder kleiner VPS (siehe ADR 0001)
- Low-Level-Wind (vorerst bewusst weggelassen)
