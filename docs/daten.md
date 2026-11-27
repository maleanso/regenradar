# Daten

Stand: 27.11.2026 – Angaben aus der Doku von MeteoSchweiz. **Prüfung an echten Dateien steht noch aus**
(Download aus der Claude-Sitzung war blockiert, Domain `data.geo.admin.ch` muss freigegeben werden).

Quelle: MeteoSchweiz Open Data. Angabe in jeder Ansicht: **«Source: MeteoSwiss»**.

- STAC-API: https://data.geo.admin.ch/api/stac/v1
- Doku: https://opendatadocs.meteoswiss.ch (D1 Radar, E1 Nowcasting, E2/E3 ICON)

## Radar – PRECIP (frei verfügbar)

| Punkt | Wert | Quelle |
|---|---|---|
| STAC-Collection | `ch.meteoschweiz.ogd-radar-precip` (enthält PRECIP, PRECIP-SV, CombiPrecip) | STAC |
| STAC-Struktur | **ein Item pro Kalendertag** (z. B. `20261111-ch`), Dateien sind Assets; das Item des Folgetags füllt sich ab Mitternacht | Doku D1, STAC |
| Rollierendes Fenster | 14 Tage | Doku D1 |
| Dateiname | `RZCyyjjjHHMMKK.x01.h5` (yy Jahr, jjj Tag im Jahr, HHMM UTC, KK reserviert/variabel) | Doku D1 |
| Beispiel-URL (CombiPrecip) | `https://data.geo.admin.ch/ch.meteoschweiz.ogd-radar-precip/20261111-ch/cpc2631500002_00060.001.h5` | STAC |
| Format | ODIM HDF5 (ODIM_H5 v2.4), ca. 1 MB pro Datei | Doku D1 |
| Projektion | LV95 / EPSG:2056 | Doku D1 |
| Einheit | mm/h, momentane Regenrate; Sättigung 118 mm/h | Doku D1 |
| Zeitstempel | `HHMM` = Erstellungszeit UTC (nicht ausdrücklich Messzeit) | Doku D1 |
| Aktualisierung | alle 5 min | Doku D1 |
| Gitter, Fehlwerte, Kodierung (gain/offset) | _offen – aus HDF5-Metadaten lesen_ | – |

**Folge für die Pipeline:** Neueste Dateien = Assets des Tages-Items mit Präfix `RZC`/`rzc` (Gross-/Kleinschreibung prüfen),
um Mitternacht UTC auch das Vortages-Item lesen (für −3 h).

## Nowcast – INCA (**nicht frei verfügbar**)

| Punkt | Wert | Quelle |
|---|---|---|
| Zugang | **«Data on request»** über Kontaktformular MeteoSchweiz, keine STAC-Collection | Doku E1 |
| Format | NetCDF, z. B. `RP_INCA_202106280700.nc` | Doku E1 |
| Projektion | LV03 / EPSG:21781 (nicht LV95) | Doku E1 |
| Gitter | 1 km | Doku E1 |
| Zeitschritte Niederschlag | 5 min, alle 5 min neu, bis +6 h | Doku E1 |
| Zukunft | neues Nowcasting-System 2027–2028 (neues Gitter, Parameter, Namen), mit Parallelphase | Doku E1 |

→ Der Nowcast aus dem Auftrag ist **ohne Anfrage bei MeteoSchweiz nicht nutzbar**. Varianten siehe ROADMAP / ADR 0002 (offen).

## Modell – ICON-CH1-EPS / ICON-CH2-EPS (frei per STAC)

| Punkt | ICON-CH1-EPS | ICON-CH2-EPS |
|---|---|---|
| STAC-Collection | `ch.meteoschweiz.ogd-forecasting-icon-ch1` | `ch.meteoschweiz.ogd-forecasting-icon-ch2` |
| Auflösung | ca. 1 km, 11 Members | ca. 2,1 km, 21 Members |
| Neuer Lauf | alle 3 h | alle 6 h |
| Bereit nach | ca. 120 min | ca. 210 min |
| Horizont / Schritt | 33 h / 1 h | 120 h / 1 h |
| Niederschlag | `TOT_PREC` (Gesamtniederschlag) | `TOT_PREC` |
| Format / Gitter | GRIB2, unstrukturiertes ICON-Gitter (CLAT/CLON) | gleich |
| Verfügbarkeit | nur 24 h | nur 24 h |

Hilfen: Python-Paket `meteodatalab`, Beispiele im Repo `MeteoSwiss/opendata-nwp-demos`.

## Farbskala MeteoSchweiz

_Offen – in der Open-Data-Doku nicht enthalten. Quelle noch zu finden, Freigabe durch Chris._
