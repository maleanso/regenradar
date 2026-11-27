# ADR 0001 – Pipeline hier, Anzeige als Ebene in meteocam

Datum: 27.11.2026 · Status: angenommen (Chris)

## Ausgangslage

Gewünscht ist ein schweizweites Regenradar (−3 h Messung bis +6 h Prognose). Ziel ist am Ende
meteocam: Dort gibt es bereits eine Leaflet-Karte mit Ebenen (MeteoCams, Roundshot, Windy, METAR).

## Entscheid

1. **Kein eigenes Frontend.** Die Anzeige wird eine Ebene «Regen» in meteocam (eigener Icon-Knopf
   links, Zeitschieber unten fixiert). Statt MapLibre wird Leaflet verwendet, passend zu meteocam.
2. **Pipeline in Python in diesem Repo.** Der meteocam-Worker (TypeScript) kann Radar- und
   NetCDF-Dateien nicht sinnvoll lesen; Python hat dafür bewährte Bibliotheken.
3. **Ausführung mit GitHub Actions Cron** (alle 5–10 min). Repo öffentlich → Actions-Minuten gratis.
4. **Speicher: eigener Cloudflare-R2-Bucket, öffentlich lesbar** (z. B. `radar.meteocam.ch`).
   Der private Kamerabild-Bucket von meteocam bleibt getrennt.
5. **Keine Lizenz** für dieses Repo (alle Rechte vorbehalten).

## Begründung und Alternativen

| Variante | Vorteil | Nachteil |
|---|---|---|
| **GitHub Actions Cron** (gewählt) | gratis bei öffentlichem Repo, kein Server, Logs eingebaut | Start oft 5–15 min verspätet, kein garantiertes Intervall |
| Cloudflare Container | nahe an meteocam, genauere Zeitsteuerung | zusätzliche Kosten, neue Technik |
| Kleiner VPS | volle Kontrolle, zuverlässiger Cron | Wartung, Kosten, Sicherheitsupdates |

Für den PoC reicht die Verspätung von GitHub Actions; das `index.json` enthält immer die echten
Zeitstempel, die Anzeige bleibt also korrekt. Wenn die Aktualität nicht genügt, wird auf
Cloudflare Container oder einen VPS gewechselt (Phase 2).

## Folgen

- meteocam braucht nur die öffentliche URL von `index.json`, keine Secrets aus diesem Repo.
- Für das öffentliche Repo gilt: R2-Zugang nur als GitHub-Secret; Workflows aus Forks erhalten keine Secrets.
- Quellenangabe «Source: MeteoSwiss» und Hinweis «kein offizielles Flugwetterprodukt» sind in meteocam Pflicht.
