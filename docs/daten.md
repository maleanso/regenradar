# Daten

Stand: 27.11.2026 – Radar an echter Datei geprüft; ICON noch offen; INCA nicht frei verfügbar.

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
| Gitter, Fehlwerte, Kodierung | siehe «Geprüft an echter Datei» | Datei |

### Geprüft an echter Datei (27.11.2026)

Datei: `20261127-ch/rzc263310955vl.001.h5` (28 KB, wenig Regen; Datei erscheint ca. 35 s nach Intervallende).

| Punkt | Befund |
|---|---|
| Asset-Präfixe im Tages-Item | `rzc` (PRECIP), `cpc` (CombiPrecip), `tzc` – **klein geschrieben** |
| Dateiname real | `rzcYYJJJHHMM` + `vl.001.h5` (abweichend von der Doku `KK.x01`) → nur Präfix + Zeit auswerten |
| Konvention | `ODIM_H5/V2_4`, `/what/object` = `COMP`, Radare `ADLPW` (5 Stationen) |
| Datensatz | `/dataset1/data1/data`, **float64**, Form **640 Zeilen × 710 Spalten** |
| Werte | direkt **mm/h** (`quantity` RATE, `gain` 1, `offset` 0) – keine Umrechnung nötig |
| Kein Niederschlag | `undetect` = **0** |
| Keine Daten | `nodata` = **NaN** (ausserhalb Radarabdeckung, im Beispiel 22 % der Fläche) |
| Kleinster Wert | 0,01 mm/h, Schritte 0,01 |
| Zeit | `/dataset1/what` start 09:50, end 09:55 UTC → **5-min-Intervall, Dateizeit = Intervallende** |
| Projektion | `projdef` Swiss Oblique Mercator, x_0 2'600'000 / y_0 1'200'000 = **LV95 (EPSG:2056)** |
| Auflösung | 1000 m × 1000 m |
| Ausdehnung LV95 | x **2'255'000 – 2'965'000**, y **840'000 – 1'480'000** (Pixelkanten) |
| Ausrichtung | Zeile 0 = **Norden** (visuell geprüft) |

**Folge für die Pipeline:** Neueste Dateien = Assets des Tages-Items mit Präfix `rzc`, sortiert nach Zeit im Namen;
kurz nach Mitternacht UTC auch das Vortages-Item lesen (für −3 h). Werte < 0,1 mm/h vermutlich ausblenden (Entscheid mit Farbskala).
Das Gebiet reicht weit über die Schweiz hinaus (ca. 2,7–12,5° O, 43,6–49,4° N); ausserhalb der Abdeckung transparent.

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

_Offen – in der Open-Data-Doku nicht enthalten, keine offizielle Tabelle gefunden (auch pysteps hat keine MeteoSwiss-Skala).
Vorgehen: Chris liefert einen Screenshot der Legende aus der MeteoSchweiz-App, daraus werden Stufen und Farben abgelesen und hier festgehalten._
