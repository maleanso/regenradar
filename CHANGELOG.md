# Changelog

Alle wichtigen Änderungen an diesem Projekt. Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Added
- Pipeline v0.1.0 (`pipeline/`): Radar PRECIP der letzten 3 h und ICON-CH1 `TOT_PREC` (Stundenwerte bis +6 h)
  als transparente PNG in Web Mercator mit Farbskala MeteoSchweiz, `index.json`, Aufräumen, Ablage lokal oder in R2
- Tests (pytest) mit echter Radar-Beispieldatei
- GitHub Actions: `pipeline` (alle 5 min, nach R2) und `test` (pytest); Betriebsdoku `docs/betrieb.md`
- Doku: Datenprüfung (`docs/daten.md`), ADR 0002 (Prognose ohne INCA), Ablage und `index.json` in `docs/architektur.md`
- Repo-Struktur, CLAUDE.md, ROADMAP.md, README, Doku-Gerüst
- ADR 0001: Pipeline in diesem Repo, Anzeige als Ebene in meteocam
